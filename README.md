# OpenMC Workbench

[![Notebook CI](https://github.com/marypwchin/openmc-workbench/actions/workflows/notebooks.yml/badge.svg)](https://github.com/marypwchin/openmc-workbench/actions/workflows/notebooks.yml)
[![Pages](https://github.com/marypwchin/openmc-workbench/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/marypwchin/openmc-workbench/actions/workflows/publish.yml)
[![External links](https://github.com/marypwchin/openmc-workbench/actions/workflows/links.yml/badge.svg)](https://github.com/marypwchin/openmc-workbench/actions/workflows/links.yml)
[![Documentation](https://img.shields.io/badge/docs-MyST-blue)](https://marypwchin.github.io/openmc-workbench/)


**Ongoing work exploring [OpenMC](https://openmc.org/), building on an extensive background in Monte Carlo radiation transport.**

This repository documents my ongoing exploration of OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding rather than formal research studies.

By Mary P. W. Chin

[**Read online →**](https://marypwchin.github.io/openmc-workbench/)

## Repository structure

<!-- generated:structure -->
```text
.
├── 0_nuclear_data/
│   ├── 0_0_set_up_nuclear_data.ipynb
│   ├── 0_0_set_up_nuclear_data.py
│   ├── 0_1_explore_endf-b8.1.ipynb
│   ├── 0_2_catalog_nuclear_data_libraries.ipynb
│   ├── 0_2_cataloging_nuclear_data_libraries_catalog.feather
│   ├── 0_2_cataloging_nuclear_data_libraries_df.feather
│   └── 0_3_revisit_HDF5_extract_temperatures.ipynb
├── README.md
├── index.md
├── myst.yml
├── openmc_workbench_config.py
└── sidebar-footer.md
```

<details>
<summary>Full repository tree, tooling, and CI</summary>

```text
.
├── .github/
│   └── workflows/
│       ├── links.yml
│       ├── notebooks.yml
│       └── publish.yml
├── 0_nuclear_data/
│   ├── 0_0_set_up_nuclear_data.ipynb
│   ├── 0_0_set_up_nuclear_data.py
│   ├── 0_1_explore_endf-b8.1.ipynb
│   ├── 0_2_catalog_nuclear_data_libraries.ipynb
│   ├── 0_2_cataloging_nuclear_data_libraries_catalog.feather
│   ├── 0_2_cataloging_nuclear_data_libraries_df.feather
│   └── 0_3_revisit_HDF5_extract_temperatures.ipynb
├── docs/
│   └── automation.md
├── scripts/
│   ├── check_links.py
│   ├── check_notebooks.py
│   └── update_structure.py
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── index.md
├── myst.yml
├── openmc_workbench_config.py
├── pyproject.toml
├── requirements-dev.txt
└── sidebar-footer.md
```

See the [automation guide](docs/automation.md), [CI workflow](.github/workflows/notebooks.yml), and [pre-commit configuration](.pre-commit-config.yaml).

</details>
<!-- /generated:structure -->

## Shared data location

The notebooks and text-only setup script use [openmc_workbench_config.py](openmc_workbench_config.py)
to locate the nuclear-data path, so that the path does not need to be defined in every notebook. Set `DATA_ROOT` in [openmc_workbench_config.py](openmc_workbench_config.py) to your nuclear-data path. To install this shared module, run
`python -m pip install -e .` from the repository root in the Python environment
used by your Jupyter kernel. In a notebook, you can instead run
`%pip install -e /absolute/path/to/openmc-workbench`, using your checkout's actual path.

Review the setup notebook's disk-space requirements and preview the installation with `APPLY = False` before running with downloads or conversion.

## Status

This is an active, evolving workbench. Code, documentation, and analyses will be added and revised as the work progresses. Scope, assumptions, and validation status will be documented as the work progresses.
