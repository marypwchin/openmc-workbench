# OpenMC Workbench

<!-- shared:introduction -->
**Ongoing work exploring [OpenMC](https://openmc.org/), building on an extensive background in Monte Carlo radiation transport.**

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding.

By Mary P. W. Chin
<!-- /shared:introduction -->

[**Source repository →**](https://github.com/marypwchin/openmc-workbench)

## Notebooks

Start with the [setup notebook](0_nuclear_data/0_0_set_up_nuclear_data.ipynb)
if you wish to reproduce the examples locally. Otherwise, go directly to
the [ENDF/B-VIII.1 exploration notebook](0_nuclear_data/0_1_explore_endf-b8.1.ipynb).

<!-- generated:notebooks -->
| Notebook | What it covers |
| --- | --- |
| [Set up OpenMC nuclear data](0_nuclear_data/0_0_set_up_nuclear_data.ipynb) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. |
| [Exploring ENDF/B-VIII.1](0_nuclear_data/0_1_explore_endf-b8.1.ipynb) | Explore `cross_section.xml` and HDF5 data from ENDF/B-VIII.1, comparing direct XML/HDF5 inspection with the OpenMC Python API. |
| [Cataloging nuclear data libraries](0_nuclear_data/0_2_catalog_nuclear_data_libraries.ipynb) | Build a reference DataFrame cataloging material, MT numbers, and nuclear-data libraries. |
| [Revisit HDF5 and extract temperatures](0_nuclear_data/0_3_revisit_HDF5_extract_temperatures.ipynb) | Explore the structure of OpenMC neutron HDF5 files, inspect groups and attributes, extract temperatures, and compare temperature availability across nuclear-data libraries. |
| [Survey ways to plot cross sections with OpenMC](1_cross_sections/1_0_survey_ways_to_plot.ipynb) | Survey three ways to plot continuous-energy cross sections in OpenMC: `plot_xs()`, `calculate_cexs()`, and direct access to HDF5 data. |
| [Make materials with and without neutronics_material_maker](1_cross_sections/1_1_plot_macroscopic_cross_sections_of_compounds.ipynb) | Compounds need to be defined before plotting macroscropic cross sections. Compare two ways to create OpenMC materials: defining elemental compositions, enrichment, and densities manually, and using predefined materials from `neutronics_material_maker`. |
| [Tritium production in a PbLi concentric-spheres model](2_first_simulations/2_0_tritium_production_PbLi_concentric_spheres.ipynb) | Demonstrate setting up and running an OpenMC simulation using a simple concentric-sphere geometry with a lead–lithium (PbLi) breeding blanket. |
<!-- /generated:notebooks -->

Reading the notebooks does not require a local nuclear-data installation.
Running the notebooks does: use a Python environment with OpenMC and the
dependencies listed in the notebooks, and follow the setup instructions.

For text-only setup, the parallel Python script, [0_0_set_up_nuclear_data.py](0_nuclear_data/0_0_set_up_nuclear_data.py), serves the same purpose as [0_0_set_up_nuclear_data.ipynb](0_nuclear_data/0_0_set_up_nuclear_data.ipynb).

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
