# Repository automation: step by step

The repository includes scripts to keep the exploration lists up to date and check files before changes are committed. These checks help catch missing links, invalid notebooks, and Python errors. They do **not** run OpenMC calculations or verify scientific results.

## Files and their purposes

The main files are listed below. Paths are relative to the repository root.

| File | Purpose |
| --- | --- |
| [.github/workflows/notebooks.yml](../.github/workflows/notebooks.yml) | Runs notebook and Python checks on GitHub after a push or pull request, or when started manually. |
| [.github/workflows/links.yml](../.github/workflows/links.yml) | Checks external links weekly or when started manually. |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | Specifies the checks to run locally before a Git commit. |
| [requirements-dev.txt](../requirements-dev.txt) | Lists the Python packages used for development and checking files. |
| [pyproject.toml](../pyproject.toml) | Defines the installable Python module, allowing `python -m pip install -e .`. |
| [openmc_workbench_config.py](../openmc_workbench_config.py) | Makes nuclear-data paths available to Python and generates the C++ header when run as a script. |
| `data_root.txt` | User-created file containing the location of the nuclear-data libraries; not committed to Git. |
| [data_root.example.txt](../data_root.example.txt) | Example to copy when creating `data_root.txt`. |
| `openmc_workbench_config.hpp` | Generated C++ header containing the same nuclear-data directory names; not committed to Git. |
| [scripts/update_structure.py](../scripts/update_structure.py) | Updates notebook outlines, the exploration lists in `README.md` and `index.md`, and text shared between those pages. |
| [scripts/openmc_api_index.py](../scripts/openmc_api_index.py) | Finds documented OpenMC API calls in `.ipynb` and `.py` files. |
| [scripts/check_notebooks.py](../scripts/check_notebooks.py) | Checks notebook file structure. |
| [scripts/check_links.py](../scripts/check_links.py) | Checks links to files in the repository and collects external links for checking online. |
| [.gitignore](../.gitignore) | Keeps local data paths, generated files, environments, and other unwanted files out of normal Git staging. |

GitHub workflow files use YAML (`.yml`), where indentation matters. Python packaging settings use TOML (`.toml`). The commands and scripts listed here are specific to OpenMC Workbench; the file formats are standard.

### Nuclear-data paths for Python and C++

The nuclear-data libraries reside outside the repository. Their location is specified once in `data_root.txt`, as explained in [Nuclear-data paths](../README.md#nuclear-data-paths).

`openmc_workbench_config.py` has two uses:

- **In Python:** `from openmc_workbench_config import ENDF_B81` makes the path to an existing `endf-b8.1` directory available to a notebook or script. Importing the module does not generate files.
- **For C++:** Running `python openmc_workbench_config.py` from the repository root generates `openmc_workbench_config.hpp`. A C++ program can then include the header using `#include "openmc_workbench_config.hpp"`.

Directory names such as `endf-b8.1` and `fendl-3.2c` become `ENDF_B81` and `FENDL_32C`. If library directories are added, removed, or renamed, run the Python script again to regenerate the C++ header. Changing only the directory path in `data_root.txt` does not require regeneration; C++ reads that file when the program runs. The header should also be regenerated if the repository is moved.

## 1. Check what is generated

`scripts/update_structure.py` updates the outline near the beginning of each notebook. It reads Markdown headings (`#`, `##`, `###`, etc.), including headings in the first cell, and builds a text outline. Headings inside fenced code examples are ignored. Use one `#` title per notebook and `##` or `###` for its sections. Underlined headings and HTML headings are not supported.

The script also updates two views of the explorations:

- `README.md` presents **Explorations** first as a directory tree of numbered `.ipynb`, `.py`, and `.cpp` files, then **Nuts and bolts** with the working details. Repository helper scripts and auxiliary files are excluded from the tree.
- `index.md` presents **Nuts and bolts** first, then **Explorations** grouped by numbered subdirectory, with headings such as **Nuclear data** and **First simulations**. Each table has **File | What it covers | OpenMC API** columns. Notebooks link to their MyST pages; Python and C++ source files link to GitHub. The last column lists recognized OpenMC constructors, functions, and methods with documentation links; a dash means none were recognized.

Notebook descriptions are taken from the marked description in each notebook's first Markdown title cell. Descriptions of `.py` and `.cpp` files can be edited in the `index.md` table; the script retains them on later runs. New source files initially show `Description to be added.`

`scripts/openmc_api_index.py` reads Python notebook cells and scripts without executing them. Its list of recognized OpenMC calls includes material and geometry APIs, and can be extended as needed. It does not interpret C++ code or infer every possible call through dynamically created objects.

The **title, introduction, nuclear-data path instructions, and status** are maintained in `README.md` and copied into `index.md`. The **Python and C++** and **Programmatic approach** subsections under **Nuts and bolts**, including their code examples, are also copied from `README.md` into the `generated:exploration-notes` block of `index.md`. Edit this material in `README.md`, not `index.md`. The logo, badges, and documentation link belong only to `README.md`; the source-repository link and exploration tables belong only to `index.md`.

The generator expects `generated:structure` under **Explorations** in `README.md`; `generated:exploration-notes` under **Nuts and bolts** and `generated:notebooks` under **Explorations** in `index.md`. Missing or misplaced headings and markers produce an error rather than an automatic layout conversion. The one-time heading reorganization belongs in the separate `one_off/nuts_and_bolts_layout.py` script; it is not part of routine automation.

The file list comes from Git: it includes tracked files and new files that are not ignored. Empty directories, checkpoints, virtual environments, and caches are omitted. Add unwanted local files or large data directories to `.gitignore`.

Only the marked notebook outline is updated. Code, outputs, execution counts, and metadata are retained, although the notebook file's JSON formatting may change. If a notebook is open during an update, reload it before saving again to avoid overwriting the new outline.

## 2. Update exploration lists and notebook outlines

From the repository root, update the notebook outlines and both exploration lists, then inspect the changes:

```sh
python3 scripts/update_structure.py
git diff --stat
git diff -- README.md index.md
python3 scripts/update_structure.py --check
```

If only the README or its common text has changed, update the two documentation pages without modifying notebooks:

```sh
python3 scripts/update_structure.py --pages-only
python3 scripts/update_structure.py --pages-only --check
```

`--check` reports files that need updating but does not change them. A normal second run should produce no further changes. `--readme-only` updates `README.md` without updating `index.md`; use `--pages-only` when both pages need to remain synchronized.

Run the script after adding, moving, or renaming exploration files; changing notebook headings or descriptions; or editing shared README text, including the **Nuts and bolts** subsections. Check descriptions in `index.md` for new or renamed `.py` and `.cpp` files.

## 3. Set up checks before committing

The following commands create a local Python environment for repository checks and install the Git pre-commit hook. Run them from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -e .
pre-commit validate-config
pre-commit install
```

The hook runs the configured checks before each commit. It must be installed separately in each new clone of the repository. The first run may need internet access to install its tools. This environment is for checking repository files; it does not replace the OpenMC environment used to run the notebooks.

## 4. Run the checks

Run all configured checks with:

```sh
pre-commit run --all-files
```

Four checks are included:

1. **Exploration lists and notebook outlines:** Updates the exploration lists in `README.md` and `index.md`, refreshes notebook outlines, and keeps shared documentation synchronized.
2. **Notebook structure:** Uses `nbformat` to check that notebook files are valid. It does not run their cells or check scientific results.
3. **Local links:** Checks that linked repository files and directories exist, including links in notebook Markdown. It does not check heading links, notebook attachments, or links written inside code and output cells.
4. **Python errors:** Uses Ruff with rules `E9,F63,F7,F82,F401` to catch syntax errors, invalid control flow, undefined names, and unused imports. It is not a full code review or scientific validation.

To run a particular check:

```sh
pre-commit run update-structure --all-files
pre-commit run notebook-schema --all-files
pre-commit run fatal-python-errors --all-files
pre-commit run local-links --all-files
```

The output identifies the file and, where available, the line or notebook cell involved. Make the correction and run the check again. Ruff reports issues without automatically changing the code.

The first check can modify files. If it does, the commit stops so you can inspect and stage the changes. Run the commit again after reviewing them; the hook does not stage files automatically.

## 5. Review changes before committing

The following commands show which files have changed and what will be included in a commit:

```sh
git status --short
git diff --check
git diff
git add -A
pre-commit run --all-files
git diff --cached --check
git diff --cached --stat
git diff --cached
```

`git diff --check` looks for whitespace problems. The `--cached` commands show changes already staged for the commit. Review them for accidental data files, personal directory paths, unwanted notebook outputs, or unrelated edits. If a check modifies files, inspect and stage those changes before committing.

## 6. Check notebooks and results separately

The automated checks are intentionally limited. The following still need separate attention:

- **Run notebooks from start to finish.** Use the intended OpenMC Python environment and check the results, including assertions. This can reveal problems caused by executing cells out of order or by missing dependencies. Set the nuclear-data directory in `data_root.txt` and install the module using `python -m pip install -e .`, as described in the [README](../README.md#nuclear-data-paths).
- **Install nuclear data deliberately.** `0_0_set_up_nuclear_data.ipynb` and `0_0_set_up_nuclear_data.py` are alternative ways to install the libraries. Check the required disk space and the `LOCAL_ARCHIVES` paths, then preview with `APPLY = False`. Do not include these downloads and conversions in a commit check.
- **Keep or remove notebook outputs deliberately.** Plots and tables may be useful to readers; the checks do not automatically delete them.
- **Check XML and HDF5 content.** The notebook-file checks do not verify that XML indexes are complete, that their referenced files exist, or that nuclear-data files contain the expected information. No separate test suite currently covers these checks.
- **Apply additional code-formatting checks if needed.** The current Ruff rules target clear errors and unused imports rather than general style.
- **Validate the physics independently.** Data provenance, assumptions, transport results, and physical comparisons require scientific assessment; passing the automated checks does not establish their correctness.

## 7. Run the checks on GitHub

`.github/workflows/notebooks.yml` runs after a push or pull request and can also be started manually. To view the results, open the repository's **Actions** tab, select **Validate notebooks**, and inspect the steps. Use **Run workflow** for a manual run when the workflow is available on the default branch.

GitHub checks generated content using `--check`, without writing changes. If it reports outdated notebook outlines or exploration lists, run `python scripts/update_structure.py` locally, review the changes, and commit them.

To run two of the checks locally:

```sh
python scripts/check_notebooks.py 0_nuclear_data/*.ipynb
ruff check --select E9,F63,F7,F82,F401 .
```

GitHub also installs `openmc_workbench_config` and checks that it can import `DATA_ROOT` and `ENDF_B81` from outside the repository. The test creates a small, temporary `endf-b8.1` directory and a `data_root.txt`; it does not download nuclear data. The workflow does not generate or compile the C++ header.

GitHub does not install OpenMC, run notebook cells, or perform transport simulations. These checks supplement, rather than replace, local testing and scientific review.

References: https://pre-commit.com/ and https://nbformat.readthedocs.io/

## 8. Check external links

`.github/workflows/links.yml` checks external links each Monday at 13:23 UTC. The check can also be started manually through **Actions → Check external links → Run workflow**. GitHub runs scheduled workflows from the default branch and may start them later than the scheduled time.

The workflow collects HTTP and HTTPS links from Markdown files and notebook Markdown cells, then passes them to Lychee for checking. Links within code cells, outputs, and code examples are excluded. It does not download nuclear-data archives referenced only in setup code.

Failed links appear in the workflow log and summary. A response such as HTTP 403 (access denied) or 429 (too many requests) may reflect blocking or rate limits rather than a missing page. Check the link in a browser before changing it. The workflow limits simultaneous requests to four and retries failures, but some sites may still block automated checks.

To collect the external links locally, without checking them online:

```sh
python scripts/check_links.py
python scripts/check_links.py --external-output /tmp/openmc-external-links.txt
```

Lychee reference: https://github.com/lycheeverse/lychee-action
