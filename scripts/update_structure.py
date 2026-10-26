"""Update notebook outlines, README tree and the index table; --check changes nothing."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- generated:structure -->'
END = '<!-- /generated:structure -->'
DESC_START = '<!-- index:description -->'
DESC_END = '<!-- /index:description -->'
INDEX_START = '<!-- generated:notebooks -->'
INDEX_END = '<!-- /generated:notebooks -->'


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
            # Migrate the existing hand-written outline in this repository.
            text = re.sub(r'\*\*Notebook outline\*\*\n```text\n.*?```\n*', '', text, flags=re.S)
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
    # Show the scientific notebooks; repository tooling remains discoverable in Git.
    notebook_paths = [
        p for p in paths
        if p.endswith('.ipynb')
        and len(Path(p).parts) >= 2
        and re.match(r'^\d+_', Path(p).parts[0])
    ]
    generated = START + '\n' + render_tree(notebook_paths) + '\n' + END
    text = (ROOT / 'README.md').read_text(encoding='utf-8')
    if START in text:
        return re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: generated, text, flags=re.S)
    pattern = r'(## (?:Repository structure|Notebooks)\s*\n)```text\n.*?```'
    text, count = re.subn(pattern, lambda m: m[1] + generated, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError('README needs a Repository structure heading followed by a text fence')
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


def index_text():
    rows = ['| Notebook | What it covers |', '| --- | --- |']
    for filename in notebook_pages():
        path = ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(f'myst.yml lists missing notebook: {filename}')
        title, description = notebook_details(path)
        # Escaped pipes cannot create extra columns in a Markdown table.
        title = title.replace('|', r'\|')
        description = description.replace('|', r'\|')
        rows.append(f'| [{title}]({filename}) | {description} |')
    generated = INDEX_START + '\n' + '\n'.join(rows) + '\n' + INDEX_END
    text = (ROOT / 'index.md').read_text(encoding='utf-8')
    if INDEX_START in text:
        pattern = re.escape(INDEX_START) + r'.*?' + re.escape(INDEX_END)
        return re.sub(pattern, lambda _: generated, text, flags=re.S)
    # First run: migrate a hand-written two- or three-column Workbench table.
    pattern = (r'(?m)^\| (?:Category \| )?Workbench \| What it covers \|\n'
               r'\|[^\n]*\|\n(?:\|[^\n]*\|\n)*')
    match = re.search(pattern, text)
    if not match:
        raise ValueError('index.md needs a Workbench table or generated:notebooks markers')
    return (text[:match.start()].rstrip('\n') + '\n\n' + generated + '\n\n'
            + text[match.end():].lstrip('\n'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument(
        '--readme-only', action='store_true',
        help='Update/check only README.md; leave notebook files untouched',
    )
    args = parser.parse_args()
    paths = repository_paths()
    updates = [] if args.readme_only else ([(ROOT / p, notebook_text(ROOT / p)) for p in paths if p.endswith('.ipynb')])
    updates.append((ROOT / 'README.md', readme_text(paths)))
    # Process notebook updates first: notebook_details reads the on-disk description.
    updates.append((ROOT / 'index.md', index_text()))
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
