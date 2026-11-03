# OpenMC Workbench

<!-- shared:introduction -->
**Ongoing work exploring [OpenMC](https://openmc.org/), building on an extensive background in Monte Carlo radiation transport.**

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding.

OpenMC's transport kernel is written in C++, but much of its user-facing API is in Python. Most explorations here therefore use Python, particularly for model construction, calculations, and analysis. C++ is used selectively, where it is useful to examine data formats, underlying structures, or aspects of OpenMC's implementation more directly.

By Mary P. W. Chin
<!-- /shared:introduction -->

[**Source repository →**](https://github.com/marypwchin/openmc-workbench)

## Explorations

Start with the [setup notebook](0_nuclear_data/0_0_set_up_nuclear_data.ipynb)
if you wish to reproduce the examples locally. Otherwise, go directly to
the [ENDF/B-VIII.1 exploration notebook](0_nuclear_data/0_1_explore_endf-b8.1.ipynb).

<!-- generated:notebooks -->
| File | What it covers |
| --- | --- |
| [`0_0_set_up_nuclear_data.ipynb`](0_nuclear_data/0_0_set_up_nuclear_data.ipynb) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. |
| [`0_0_set_up_nuclear_data.py`](https://github.com/marypwchin/openmc-workbench/blob/main/0_nuclear_data/0_0_set_up_nuclear_data.py) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. |
| [`0_1_explore_endf-b8.1.ipynb`](0_nuclear_data/0_1_explore_endf-b8.1.ipynb) | Explore `cross_section.xml` and HDF5 data from ENDF/B-VIII.1, comparing direct XML/HDF5 inspection with the OpenMC Python API. |
| [`0_2_catalog_nuclear_data_libraries.ipynb`](0_nuclear_data/0_2_catalog_nuclear_data_libraries.ipynb) | Build a reference DataFrame cataloging material, MT numbers, and nuclear-data libraries. |
| [`0_3_revisit_HDF5_extract_temperatures.ipynb`](0_nuclear_data/0_3_revisit_HDF5_extract_temperatures.ipynb) | Explore the structure of OpenMC neutron HDF5 files, inspect groups and attributes, extract temperatures, and compare temperature availability across nuclear-data libraries. |
| [`0_4_cross_sections_xml_pugixml.cpp`](https://github.com/marypwchin/openmc-workbench/blob/main/0_nuclear_data/0_4_cross_sections_xml_pugixml.cpp) | Read and explore `cross_sections.xml` in C++ using pugixml. Display the XML elements and their attributes, with an option to choose a nuclear-data library other than the default ENDF/B-VIII.1. |
| [`1_0_survey_ways_to_plot.ipynb`](1_cross_sections/1_0_survey_ways_to_plot.ipynb) | Survey three ways to plot continuous-energy cross sections in OpenMC: `plot_xs()`, `calculate_cexs()`, and direct access to HDF5 data. |
| [`1_1_plot_macroscopic_cross_sections_of_compounds.ipynb`](1_cross_sections/1_1_plot_macroscopic_cross_sections_of_compounds.ipynb) | Compounds need to be defined before plotting macroscropic cross sections. Compare two ways to create OpenMC materials: defining elemental compositions, enrichment, and densities manually, and using predefined materials from `neutronics_material_maker`. |
| [`2_0_tritium_production_PbLi_concentric_spheres.ipynb`](2_first_simulations/2_0_tritium_production_PbLi_concentric_spheres.ipynb) | Demonstrate setting up and running an OpenMC simulation using a simple concentric-sphere geometry with a lead–lithium (PbLi) breeding blanket. |
<!-- /generated:notebooks -->

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

## Status

<!-- shared:status -->
This is an active, evolving workbench. Code, documentation, and analyses will be added and revised as the work progresses.
<!-- /shared:status -->
