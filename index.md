# OpenMC Workbench

<!-- shared:introduction -->
**Ongoing work exploring [OpenMC](https://openmc.org/), building on an extensive background in Monte Carlo radiation transport.**

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding.

By Mary P. W. Chin
<!-- /shared:introduction -->

[**Source repository →**](https://github.com/marypwchin/openmc-workbench)

## Status

<!-- shared:status -->
This is an active, evolving workbench. Code, documentation, and analyses will be added and revised as the work progresses.

The repository is public in the spirit of open-source collaboration and scientific exchange. Efforts are made to document the behind-the-scenes work, including data preparation, configuration, and computational setup, for transparency and reproducibility.

The workbench is a record of ongoing explorations rather than a software product designed for end users. Comments, corrections, and peer review are welcome.
<!-- /shared:status -->

## Nuts and bolts

<!-- generated:exploration-notes -->
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
<!-- /generated:exploration-notes -->

## Explorations

Start with the [setup notebook](0_nuclear_data/0_0_set_up_nuclear_data.ipynb)
if you wish to reproduce the examples locally. Otherwise, go directly to
the [ENDF/B-VIII.1 exploration notebook](0_nuclear_data/0_1_explore_endf-b8.1.ipynb).

<!-- generated:notebooks -->
### Nuclear data

| File | What it covers | OpenMC API |
| --- | --- | --- |
| [`0_0_set_up_nuclear_data.ipynb`](0_nuclear_data/0_0_set_up_nuclear_data.ipynb) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. | [`DataLibrary.export_to_xml()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.export_to_xml), [`DataLibrary.register_file()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.register_file), [`IncidentNeutron.export_to_hdf5()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.export_to_hdf5), [`IncidentNeutron.from_ace()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.from_ace) |
| [`0_0_set_up_nuclear_data.py`](https://github.com/marypwchin/openmc-workbench/blob/main/0_nuclear_data/0_0_set_up_nuclear_data.py) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. | [`DataLibrary.export_to_xml()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.export_to_xml), [`DataLibrary.register_file()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.register_file), [`IncidentNeutron.export_to_hdf5()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.export_to_hdf5), [`IncidentNeutron.from_ace()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.from_ace) |
| [`0_1_explore_endf-b8.1.ipynb`](0_nuclear_data/0_1_explore_endf-b8.1.ipynb) | Explore `cross_section.xml` and HDF5 data from ENDF/B-VIII.1, comparing direct XML/HDF5 inspection with the OpenMC Python API. | [`DataLibrary.from_xml()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.from_xml), [`DataLibrary.get_by_material()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.get_by_material), [`IncidentNeutron.from_hdf5()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.from_hdf5) |
| [`0_2_catalog_nuclear_data_libraries.ipynb`](0_nuclear_data/0_2_catalog_nuclear_data_libraries.ipynb) | Build a reference DataFrame cataloging material, MT numbers, and nuclear-data libraries. | — |
| [`0_3_revisit_HDF5_extract_temperatures.ipynb`](0_nuclear_data/0_3_revisit_HDF5_extract_temperatures.ipynb) | Explore the structure of OpenMC neutron HDF5 files, inspect groups and attributes, extract temperatures, and compare temperature availability across nuclear-data libraries. | — |
| [`0_4_cross_sections_xml_pugixml.cpp`](https://github.com/marypwchin/openmc-workbench/blob/main/0_nuclear_data/0_4_cross_sections_xml_pugixml.cpp) | Read and explore `cross_sections.xml` in C++ using pugixml. Display the XML elements and their attributes, with an option to choose a nuclear-data library other than the default ENDF/B-VIII.1. | — |
| [`0_5_inspect_hdf5_reactions.cpp`](https://github.com/marypwchin/openmc-workbench/blob/main/0_nuclear_data/0_5_inspect_hdf5_reactions.cpp) | Inspect reaction groups in an OpenMC neutron HDF5 file. | — |

### Cross sections

| File | What it covers | OpenMC API |
| --- | --- | --- |
| [`1_0_ways_to_plot.ipynb`](1_cross_sections/1_0_ways_to_plot.ipynb) | Survey three ways to plot continuous-energy cross sections in OpenMC: `plot_xs()`, `calculate_cexs()`, and direct access to HDF5 data. | [`DataLibrary.from_xml()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.from_xml), [`DataLibrary.get_by_material()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.DataLibrary.html#openmc.data.DataLibrary.get_by_material), [`IncidentNeutron.from_hdf5()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.data.IncidentNeutron.html#openmc.data.IncidentNeutron.from_hdf5), [`plot_xs()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.plot_xs.html), [`plotter.calculate_cexs()`](https://docs.openmc.org/en/stable/_modules/openmc/plotter.html#calculate_cexs) |

### Materials

| File | What it covers | OpenMC API |
| --- | --- | --- |
| [`2_0_ways_to_define_materials.ipynb`](2_materials/2_0_ways_to_define_materials.ipynb) | Explore four ways to define multi-element materials in OpenMC. | [`Material()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html), [`Material.add_element()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.add_element), [`Material.set_density()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.set_density), [`Materials()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Materials.html), [`plot_xs()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.plot_xs.html) |

### Run

| File | What it covers | OpenMC API |
| --- | --- | --- |
| [`3_0_breeder_tritium_neutron_maps.ipynb`](3_run/3_0_breeder_tritium_neutron_maps.ipynb) | Map tritium production and neutron spectra in a concentric-spheres model. | [`Cell()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Cell.html), [`CellFilter()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.CellFilter.html), [`EnergyFilter()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.EnergyFilter.html), [`Geometry()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Geometry.html), [`IndependentSource()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.IndependentSource.html), [`Material()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html), [`Material.add_element()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.add_element), [`Material.get_nuclides()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.get_nuclides), [`Material.mean_free_path()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.mean_free_path), [`Material.set_density()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Material.html#openmc.Material.set_density), [`Materials()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Materials.html), [`MeshFilter()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.MeshFilter.html), [`Region.from_expression()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Region.html#openmc.Region.from_expression), [`Settings()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Settings.html), [`Sphere()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Sphere.html), [`StatePoint()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.StatePoint.html), [`Tallies()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Tallies.html), [`Tally()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.Tally.html), [`Model()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.model.Model.html), [`Model.plot()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.model.Model.html#openmc.model.Model.plot), [`Model.run()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.model.Model.html#openmc.model.Model.run), [`plot_xs()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.plot_xs.html), [`plotter.calculate_cexs()`](https://docs.openmc.org/en/stable/_modules/openmc/plotter.html#calculate_cexs), [`Discrete()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.stats.Discrete.html), [`Isotropic()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.stats.Isotropic.html), [`Point()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.stats.Point.html) |
| [`3_1_ways_to_run_and_post_process.ipynb`](3_run/3_1_ways_to_run_and_post_process.ipynb) | Explore different ways to run an OpenMC model, continue simulations, and retrieve tally results. | [`StatePoint()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.StatePoint.html), [`Model.from_model_xml()`](https://docs.openmc.org/en/stable/pythonapi/generated/openmc.model.Model.html#openmc.model.Model.from_model_xml) |
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

## Compilers and libraries

<!-- shared:compilers -->
See [docs/compilers_and_libraries.md](docs/compilers_and_libraries.md).
<!-- /shared:compilers -->
