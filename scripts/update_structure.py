"""Update notebook outlines and exploration lists; --check changes nothing."""
import argparse
import json
import re
import subprocess
from pathlib import Path

from openmc_api_index import openmc_methods

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- generated:structure -->'
END = '<!-- /generated:structure -->'
DESC_START = '<!-- index:description -->'
DESC_END = '<!-- /index:description -->'
INDEX_START = '<!-- generated:notebooks -->'
INDEX_END = '<!-- /generated:notebooks -->'
NOTES_START = '<!-- generated:exploration-notes -->'
NOTES_END = '<!-- /generated:exploration-notes -->'
EXPLORATION_SUFFIXES = {'.ipynb', '.py', '.cpp'}


def source(cell):
    value = cell.get('source', '')
    return ''.join(value) if isinstance(value, list) else value


def headings(text):
    fence = None
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            match = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
            if match:
                yield len(match[1]), match[2]


def tree_lines(node, prefix=''):
    lines = []
    for i, (name, children) in enumerate(node):
        last = i == len(node) - 1
        lines.append(prefix + ('└── ' if last else '├── ') + name)
        lines.extend(tree_lines(children, prefix + ('    ' if last else '│   ')))
    return lines


def block(lines):
    return START + '\n```text\n' + '\n'.join(lines) + '\n```\n' + END


def description_match(text):
    return re.search(
        re.escape(DESC_START) + r'\s*\n(.*?)\n' + re.escape(DESC_END),
        text, flags=re.S,
    )


def notebook_details(path):
    """Read manually edited title and description; no notebook execution needed."""
    nb = json.loads(path.read_text(encoding='utf-8'))
    for cell in nb['cells']:
        if cell['cell_type'] != 'markdown':
            continue
        text = source(cell)
        title = next((label for level, label in headings(text) if level == 1), None)
        if title is None:
            continue
        match = description_match(text)
        if match is None:
            raise ValueError(
                f'{path.relative_to(ROOT)}: add a description in the title cell '
                f'between {DESC_START} and {DESC_END}'
            )
        description = ' '.join(match[1].split())
        if not description:
            raise ValueError(f'{path.relative_to(ROOT)}: empty index description')
        return title, description
    raise ValueError(f'{path.relative_to(ROOT)}: expected a Markdown # title')


def notebook_text(path):
    original = path.read_text(encoding='utf-8')
    nb = json.loads(original)
    cells = nb['cells']
    # Remove our own outline before collecting headings (no recursive outlines).
    for cell in cells:
        if cell['cell_type'] == 'markdown':
            text = source(cell)
            text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n*', '', text, flags=re.S)
            cell['source'] = text.splitlines(keepends=True)
    title_cell = None
    title = None
    items = []
    for cell in cells:
        if cell['cell_type'] != 'markdown':
            continue
        for level, label in headings(source(cell)):
            if title is None and level == 1:
                title_cell, title = cell, label
            else:
                items.append((level, label))
    if title_cell is None:
        raise ValueError(f'{path}: expected a Markdown # title')
    nodes = []
    stack = [(0, nodes)]
    for level, label in items:
        while stack[-1][0] >= level:
            stack.pop()
        children = []
        stack[-1][1].append((label, children))
        stack.append((level, children))

    # Keep the editable description directly below the # title, if present.
    title_text = source(title_cell)
    lines = title_text.splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if re.match(r'^ {0,3}#\s+', line))
    before = ''.join(lines[:index + 1]).rstrip('\n')
    remaining = ''.join(lines[index + 1:]).lstrip('\n')
    match = re.match(
        re.escape(DESC_START) + r'\s*\n.*?\n' + re.escape(DESC_END),
        remaining, flags=re.S,
    )
    description_block = ''
    if match:
        description_block = match.group(0).strip() + '\n\n'
        remaining = remaining[match.end():].lstrip('\n')
    result = before + '\n\n' + description_block + block([title] + tree_lines(nodes))
    if remaining:
        result += '\n\n' + remaining
    else:
        result += '\n'
    title_cell['source'] = result.splitlines(keepends=True)

    # Preserve the original bytes if the JSON content already matches.
    if nb == json.loads(original):
        return original
    return json.dumps(nb, ensure_ascii=False, indent=1) + '\n'


def repository_paths():
    # Include tracked and nonignored new files; exclude local caches and environments.
    output = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
    )
    excluded = {'.git', '.ipynb_checkpoints', '__pycache__', '.venv', 'venv', '.pytest_cache', '.ruff_cache'}
    return sorted({p for p in output.decode().split('\0') if p and
                   not excluded.intersection(Path(p).parts) and (ROOT / p).is_file()})


def exploration_paths(paths):
    """Numbered scientific explorations, excluding repository helper scripts."""
    return sorted(
        path for path in paths
        if Path(path).suffix in EXPLORATION_SUFFIXES
        and len(Path(path).parts) >= 2
        and re.match(r'^\d+_', Path(path).parts[0])
        and re.match(r'^\d+_', Path(path).name)
    )


def readme_text(paths):
    def nodes(mapping):
        return [(name + ('/' if value else ''), nodes(value))
                for name, value in sorted(mapping.items(), key=lambda pair: (not bool(pair[1]), pair[0]))]

    def render_tree(selected):
        nested = {}
        for path in selected:
            node = nested
            for part in Path(path).parts:
                node = node.setdefault(part, {})
        return '```text\n' + '\n'.join(['.'] + tree_lines(nodes(nested))) + '\n```'
    # Show numbered notebooks, Python scripts, and C++ programs.
    selected = exploration_paths(paths)
    generated = START + '\n' + render_tree(selected) + '\n' + END
    text = (ROOT / 'README.md').read_text(encoding='utf-8')
    explorations = re.search(r'(?m)^## Explorations[ \t]*$', text)
    nuts_and_bolts = re.search(r'(?m)^## Nuts and bolts[ \t]*$', text)
    if explorations is None or nuts_and_bolts is None or explorations.start() >= nuts_and_bolts.start():
        raise ValueError('README.md needs ## Explorations before ## Nuts and bolts')
    if (text.count(START) != 1 or text.count(END) != 1
            or not (explorations.end() < text.index(START)
                    < text.index(END) < nuts_and_bolts.start())):
        raise ValueError('README.md needs generated:structure under ## Explorations')
    pattern = re.escape(START) + r'.*?' + re.escape(END)
    text, count = re.subn(pattern, lambda _: generated, text, flags=re.S)
    if count != 1:
        raise ValueError('README.md needs exactly one complete generated:structure block')
    return text


def notebook_pages():
    """List notebook paths in MyST TOC order, expanding wildcard patterns.

    This handles the repository's simple `- file:` and `- pattern:` entries;
    category headings (`- title:`) are for MyST navigation, not the index table.
    Wildcard matches are sorted by filename for deterministic output.
    """
    pages = []
    seen = set()
    myst = (ROOT / 'myst.yml').read_text(encoding='utf-8')

    for line in myst.splitlines():
        item = re.match(r"^\s*-\s+(file|pattern):\s*(.*?)\s*$", line)
        if item is None:
            continue
        kind = item[1]
        value = item[2].split(' #', 1)[0].strip().strip('\"\'')
        if not value.endswith('.ipynb'):
            continue  # Index and other non-notebook pages
        if kind == 'file':
            filenames = [value]
        else:
            pattern = Path(value)
            if pattern.is_absolute() or '..' in pattern.parts:
                raise ValueError(f'Unsafe notebook pattern in myst.yml: {value}')
            filenames = sorted(
                path.relative_to(ROOT).as_posix()
                for path in ROOT.glob(value)
                if path.is_file() and path.suffix == '.ipynb'
                and '.ipynb_checkpoints' not in path.parts
            )
            if not filenames:
                raise ValueError(f'Notebook pattern in myst.yml matches nothing: {value}')

        for filename in filenames:
            if filename in seen:
                raise ValueError(f'Notebook appears more than once in myst.yml: {filename}')
            seen.add(filename)
            pages.append(filename)

    if not pages:
        raise ValueError('No notebook `- file:` or `- pattern:` entries in myst.yml')
    return pages


# Shared content is authored in README.md. index.md has the same shared text,
# but a descriptive table rather than a directory tree.
def shared_block(text, name):
    pattern = re.compile(
        r'<!-- shared:' + re.escape(name) + r' -->\n(.*?)\n<!-- /shared:'
        + re.escape(name) + r' -->', re.S
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f'Missing shared {name} section in README.md')
    return match.group(1)


def exploration_notes(readme):
    """Copy the two Nuts and bolts subsections from README.md."""
    explorations = re.search(r'(?m)^## Explorations[ \t]*$', readme)
    nuts_and_bolts = re.search(r'(?m)^## Nuts and bolts[ \t]*$', readme)
    if (explorations is None or nuts_and_bolts is None
            or explorations.start() >= nuts_and_bolts.start()):
        raise ValueError('README.md needs ## Explorations before ## Nuts and bolts')

    following = re.search(r'(?m)^## [^\n]+$', readme[nuts_and_bolts.end():])
    end = nuts_and_bolts.end() + following.start() if following else len(readme)
    content = readme[nuts_and_bolts.end():end]
    headings = list(re.finditer(r'(?m)^### ([^\n]+?)[ \t]*$', content))
    subsections = {}
    for i, heading in enumerate(headings):
        stop = headings[i + 1].start() if i + 1 < len(headings) else len(content)
        name = heading[1].strip()
        if name in subsections:
            raise ValueError(f'Duplicate ### {name} subsection in README.md')
        subsections[name] = content[heading.start():stop].strip()

    names = ('Python and C++', 'Programmatic approach')
    for name in names:
        if name not in subsections:
            raise ValueError(f'README.md needs a ### {name} subsection under ## Nuts and bolts')
    return '\n\n'.join(subsections[name] for name in names)


def code_url(path):
    """Link source files to GitHub so they also open from the MyST website."""
    myst = (ROOT / 'myst.yml').read_text(encoding='utf-8')
    match = re.search(r'(?m)^\s*github:\s*(https://\S+)', myst)
    if match is None:
        raise ValueError('myst.yml needs project.github for Python/C++ links')
    return f'{match[1].rstrip("/")}/blob/main/{path}'


def index_text(paths, readme):
    text = (ROOT / 'index.md').read_text(encoding='utf-8')
    title = re.search(r'^# .+$', readme, re.M)
    if not title:
        raise ValueError('README.md needs a top-level title')
    text, n = re.subn(r'^# .+$', lambda _: title.group(), text, count=1, flags=re.M)
    if n != 1:
        raise ValueError('index.md needs a top-level title')
    nuts_and_bolts = re.search(r'(?m)^## Nuts and bolts[ \t]*$', text)
    explorations = re.search(r'(?m)^## Explorations[ \t]*$', text)
    if (nuts_and_bolts is None or explorations is None
            or nuts_and_bolts.start() >= explorations.start()):
        raise ValueError('index.md needs ## Nuts and bolts before ## Explorations')

    for section in ('introduction', 'data', 'compilers', 'status'):
        content = shared_block(readme, section)
        pattern = (r'<!-- shared:' + re.escape(section)
                   + r' -->\n.*?\n<!-- /shared:' + re.escape(section) + r' -->')
        replacement = ('<!-- shared:' + section + ' -->\n'
                       + content + '\n<!-- /shared:' + section + ' -->')
        text, n = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
        if n != 1:
            raise ValueError(f'Missing shared {section} markers in index.md')

    pattern = re.escape(INDEX_START) + r'(.*?)' + re.escape(INDEX_END)
    match = re.search(pattern, text, flags=re.S)
    if not match:
        raise ValueError('Missing generated:notebooks table in index.md')

    # Keep existing descriptions for Python/C++ files, even when the generated
    # tables already have an OpenMC API column.
    previous_descriptions = {}
    if '| File | What it covers | OpenMC API |' not in match[1]:
        raise ValueError('index.md needs generated three-column OpenMC API tables')
    row_pattern = r'^\| \[(.*?)\]\(([^)]+)\) \| (.*?) \| .*? \|$'
    for _label, url, description in re.findall(row_pattern, match[1], flags=re.M):
        previous_descriptions[url] = description

    # Keep the existing MyST notebook selection. Other numbered source files
    # are added alongside them, sorted by path.
    published_notebooks = set(notebook_pages())
    selected = [path for path in exploration_paths(paths)
                if not path.endswith('.ipynb') or path in published_notebooks]
    lines = []
    directory = None
    for path in selected:
        subdirectory = Path(path).parts[0]
        if subdirectory != directory:
            directory = subdirectory
            heading = re.sub(r'^\d+_', '', directory).replace('_', ' ').capitalize()
            if lines:
                lines.append('')
            lines.extend([
                f'### {heading}',
                '',
                '| File | What it covers | OpenMC API |',
                '| --- | --- | --- |',
            ])

        label = f'`{Path(path).name}`'
        if path.endswith('.ipynb'):
            _title, description = notebook_details(ROOT / path)
            url = path
        else:
            url = code_url(path)
            description = previous_descriptions.get(url, previous_descriptions.get(path))
            if description is None:
                description = 'Description to be added.'
                print(f'Add a description for {path} in index.md')
        description = description.replace('|', r'\|') if path.endswith('.ipynb') else description
        methods = openmc_methods(ROOT / path)
        lines.append(f'| [{label}]({url}) | {description} | {methods} |')

    generated = INDEX_START + '\n' + '\n'.join(lines) + '\n' + INDEX_END
    text = re.sub(pattern, lambda _: generated, text, count=1, flags=re.S)

    # The notes belong under Nuts and bolts; the tables belong under Explorations.
    nuts_and_bolts = re.search(r'(?m)^## Nuts and bolts[ \t]*$', text)
    explorations = re.search(r'(?m)^## Explorations[ \t]*$', text)
    if (text.count(NOTES_START) != 1 or text.count(NOTES_END) != 1
            or text.count(INDEX_START) != 1 or text.count(INDEX_END) != 1
            or nuts_and_bolts is None or explorations is None
            or not (nuts_and_bolts.end() < text.index(NOTES_START)
                    < text.index(NOTES_END) < explorations.start()
                    < text.index(INDEX_START) < text.index(INDEX_END))):
        raise ValueError(
            'index.md needs generated:exploration-notes under ## Nuts and bolts '
            'and generated:notebooks under ## Explorations'
        )
    notes = NOTES_START + '\n' + exploration_notes(readme) + '\n' + NOTES_END
    notes_pattern = re.escape(NOTES_START) + r'.*?' + re.escape(NOTES_END)
    text, count = re.subn(notes_pattern, lambda _: notes, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError('index.md needs a complete generated:exploration-notes block')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--pages-only', action='store_true',
                        help='Update or check README.md and index.md without changing notebooks')
    parser.add_argument(
        '--readme-only', action='store_true',
        help='Update/check only README.md; leave notebook files untouched',
    )
    args = parser.parse_args()
    paths = repository_paths()
    updates = [] if (args.readme_only or args.pages_only) else ([(ROOT / p, notebook_text(ROOT / p)) for p in paths if p.endswith('.ipynb')])
    readme = readme_text(paths)
    updates.append((ROOT / 'README.md', readme))
    if not args.readme_only:
        updates.append((ROOT / 'index.md', index_text(paths, readme)))

    stale = False
    for path, content in updates:
        if path.read_text(encoding='utf-8') != content:
            stale = True
            print(('Stale: ' if args.check else 'Updated: ') + str(path.relative_to(ROOT)))
            if not args.check:
                path.write_text(content, encoding='utf-8')
    return int(args.check and stale)


if __name__ == '__main__':
    raise SystemExit(main())
