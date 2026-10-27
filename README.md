# OpenMC Workbench

<p>
<img src="assets/logo.png" alt="OpenMC Workbench logo" width="220">
</p>

[![Notebook CI](https://github.com/marypwchin/openmc-workbench/actions/workflows/notebooks.yml/badge.svg)](https://github.com/marypwchin/openmc-workbench/actions/workflows/notebooks.yml)
[![Pages](https://github.com/marypwchin/openmc-workbench/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/marypwchin/openmc-workbench/actions/workflows/publish.yml)
[![External links](https://github.com/marypwchin/openmc-workbench/actions/workflows/links.yml/badge.svg)](https://github.com/marypwchin/openmc-workbench/actions/workflows/links.yml)
[![Documentation](https://img.shields.io/badge/docs-MyST-blue)](https://marypwchin.github.io/openmc-workbench/)


<!-- shared:introduction -->
**Ongoing work exploring [OpenMC](https://openmc.org/), building on an extensive background in Monte Carlo radiation transport.**

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding.

By Mary P. W. Chin
<!-- /shared:introduction -->

[**Read online →**](https://marypwchin.github.io/openmc-workbench/)

## Notebooks

<!-- generated:structure -->
```text
.
├── 0_nuclear_data/
│   ├── 0_0_set_up_nuclear_data.ipynb
│   ├── 0_1_explore_endf-b8.1.ipynb
│   ├── 0_2_catalog_nuclear_data_libraries.ipynb
│   └── 0_3_revisit_HDF5_extract_temperatures.ipynb
└── 1_cross_sections/
    └── 1_0_survey_ways_to_plot.ipynb
```
<!-- /generated:structure -->

## Shared data location

<!-- shared:data -->
The notebooks and the setup script use [openmc_workbench_config.py](openmc_workbench_config.py)
to locate the nuclear-data path, so that the path does not need to be defined in every notebook. Set `DATA_ROOT` in [openmc_workbench_config.py](openmc_workbench_config.py) to your nuclear-data path. To install this shared module, run
`python -m pip install -e .` from the repository root in the Python environment
used by your Jupyter kernel. In a notebook, you can instead run
`%pip install -e /absolute/path/to/openmc-workbench`, using your checkout's actual path.

Review the setup notebook's disk-space requirements and preview the installation with `APPLY = False` before running with downloads or conversion.
<!-- /shared:data -->

## Status

<!-- shared:status -->
This is an active, evolving workbench. Code, documentation, and analyses will be added and revised as the work progresses.
<!-- /shared:status -->
