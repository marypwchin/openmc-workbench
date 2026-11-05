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

## Explorations

<!-- generated:structure -->
```text
.
├── 0_nuclear_data/
│   ├── 0_0_set_up_nuclear_data.ipynb
│   ├── 0_0_set_up_nuclear_data.py
│   ├── 0_1_explore_endf-b8.1.ipynb
│   ├── 0_2_catalog_nuclear_data_libraries.ipynb
│   ├── 0_3_revisit_HDF5_extract_temperatures.ipynb
│   ├── 0_4_cross_sections_xml_pugixml.cpp
│   └── 0_5_inspect_hdf5_reactions.cpp
├── 1_cross_sections/
│   └── 1_0_ways_to_plot.ipynb
├── 2_materials/
│   └── 2_0_ways_to_define_materials.ipynb
└── 3_run/
    └── 3_0_tritium_breeding_and_neutron_fluence_maps.ipynb
```
<!-- /generated:structure -->

## Nuts and bolts

### Python and C++

OpenMC's transport kernel is written in C++, but much of its user-facing API is in Python. Most explorations here therefore use Python, particularly for model construction, calculations, and analysis. C++ is used selectively, where it is useful to examine data formats, underlying structures, or aspects of OpenMC's implementation more directly.

### Programmatic approach

Throughout the Workbench, I draw on practices from data science where practical. I organize nuclear data, model specifications, and simulation results in pandas DataFrames, and process them programmatically.

For instance, an OpenMC material is typically defined by calling `openmc.Material.add_element()` separately for each element, passing numerical values directly as arguments:

```python
breeder_material = openmc.Material()
breeder_material.add_element('Pb', 84.2, percent_type='ao')
breeder_material.add_element('Li', 15.8, percent_type='ao', enrichment=90., enrichment_target='Li6', enrichment_type='ao')
```

In contrast, [2_0_ways_to_define_materials.ipynb](2_materials/2_0_ways_to_define_materials.ipynb) organizes material compositions, including isotopic enrichment specifications, in a DataFrame:

```python
mats_df.loc[len(mats_df)] = ['PbLi_manual', 'Pb', 84.2, 'ao'] + 3 * [None]
mats_df.loc[len(mats_df)] = ['PbLi_manual', 'Li', 15.8, 'ao', 90., 'Li6', 'ao']
```

A common loop then constructs the OpenMC materials:

```python
mats = {}
for name, dat in mats_df.groupby('name'):
    mats[name] = openmc.Material(name=name)

    for _, row in dat.drop(columns='name').iterrows():
        mats[name].add_element(**row.dropna().to_dict())
```


This separation of input data from model-construction logic minimizes repetitive code, reduces the risk of inconsistencies, and makes the examples easier to explore, modify, and validate.

## Nuclear-data paths

<!-- shared:data -->
Scripts can break when files are not found at their expected locations. To minimize this problem, OpenMC Workbench keeps nuclear-data paths in one place, rather than requiring them to be specified in each notebook or program.

The nuclear-data libraries reside outside the repository, and the location needs to be specified only once.

### Optional: Install nuclear-data libraries

If you already have the required nuclear-data libraries, you can skip their installation.

Otherwise, see [0_nuclear_data/README.md](0_nuclear_data/README.md).

### Set up nuclear-data paths

From the repository root:

1. **Set the data location.** Copy `data_root.example.txt` to `data_root.txt`, then edit it to specify the path to your nuclear-data directory.

2. **Set up Python.** In the Python environment used by your Jupyter kernel, run:

   ```bash
   python -m pip install -e .
   ```

   Alternatively, run the following directly in a notebook, using the absolute path to your repository:

   ```python
   %pip install -e /absolute/path/to/openmc-workbench
   ```

3. **Set up C++.** From the repository root, run:

   ```bash
   python openmc_workbench_config.py
   ```

Step 2 makes `openmc_workbench_config` importable in Python. The notebooks can then access nuclear-data paths through statements such as:

```python
from openmc_workbench_config import ENDF_B81
```

Step 3 generates `openmc_workbench_config.hpp`, providing the same paths to C++ programs through:

```cpp
#include "openmc_workbench_config.hpp"
```

### Configuration files

| File | Purpose |
|---|---|
| `data_root.txt` | Created and edited by the user; specifies the nuclear-data directory. |
| `openmc_workbench_config.py` | Provided with the repository; discovers nuclear-data directories and makes their paths available to Python. |
| `openmc_workbench_config.hpp` | Generated by Step 3; makes the same paths available to C++. |

Library names such as `ENDF_B80`, `ENDF_B81`, and `FENDL_32C` are generated automatically from existing directory names. If new library directories are added, rerun Step 3 to update the C++ header.

This arrangement allows Python notebooks and C++ programs to use the same nuclear-data paths without maintaining separate path settings.
<!-- /shared:data -->

## Compilers and libraries

<!-- shared:compilers -->
See [docs/compilers_and_libraries.md](docs/compilers_and_libraries.md).
<!-- /shared:compilers -->

## Status

<!-- shared:status -->
This is an active, evolving workbench. Code, documentation, and analyses will be added and revised as the work progresses.
<!-- /shared:status -->
