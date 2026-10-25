# OpenMC Workbench

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding. The notebooks combine explanations, Python examples, and comparisons between the OpenMC API and the underlying data files.

This is an evolving workbench.

## Workbench notebooks

Start with the setup notebook if you wish to reproduce the examples locally, or go directly to the exploration notebook to read the analysis.

<!-- generated:notebooks -->
| Notebook | What it covers |
| --- | --- |
| [Set up OpenMC nuclear data](0_nuclear_data/0_0_set_up_nuclear_data.ipynb) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. |
| [Exploring ENDF/B-VIII.1](0_nuclear_data/0_1_explore_endf-b8.1.ipynb) | Explore `cross_section.xml` and HDF5 data from ENDF/B-VIII.1, comparing direct XML/HDF5 inspection with the OpenMC Python API. |
| [Cataloging nuclear data libraries](0_nuclear_data/0_2_catalog_nuclear_data_libraries.ipynb) | Build a reference DataFrame cataloging material, MT numbers, and nuclear-data libraries. |
| [Revisit HDF5 and extract temperatures](0_nuclear_data/0_3_revisit_HDF5_extract_temperatures.ipynb) | Explore the structure of OpenMC neutron HDF5 files, inspect groups and attributes, extract MT temperatures, and compare temperature availability across nuclear-data libraries. |
<!-- /generated:notebooks -->

For text-only setup, the parallel Python script, [0_0_set_up_nuclear_data.py](0_nuclear_data/0_0_set_up_nuclear_data.py), serves the same purpose as [0_0_set_up_nuclear_data.ipynb](0_nuclear_data/0_0_set_up_nuclear_data.ipynb).

## Reproducing the notebooks

Reading the notebooks does not require a local nuclear-data installation. Running the notebooks does: use a Python environment with OpenMC and the dependencies listed in the notebooks, and follow the setup instructions.

The notebooks and the setup script use [shared configuration](openmc_workbench_config.py) to locate the nuclear-data path, so that the path does not need to be defined in every notebook. Set `DATA_ROOT` in [openmc_workbench_config.py](openmc_workbench_config.py) to your nuclear-data path. From your local repository root, install that module into the Python environment used by your Jupyter kernel:

```sh
python -m pip install -e .
```

Review the setup notebook's disk-space requirements and preview the installation with `APPLY = False` before enabling downloads or conversion.

## Source and contributions

The notebooks and supporting code are maintained in the [OpenMC Workbench repository](https://github.com/marypwchin/openmc-workbench). For contributor setup, validation checks, and CI workflows, please see the [repository automation guide](docs/automation.md).
