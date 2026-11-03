## Nuclear-data setup

Review the disk-space requirements:
| Library or data | Installed disk space |
| --- | ---: |
| ENDF/B-VIII.1 | 43 GiB |
| JEFF-4.0 | 51 GiB |
| JENDL-5 | 31 GiB |
| FENDL-3.2c | 907 MiB |
| WMP v1.1 | 16 MiB |
| Depletion chains | 123 MiB |

Preview the installation with `APPLY = False` in `0_0_set_up_nuclear_data.ipynb` or `0_0_set_up_nuclear_data.py` before running with downloads or conversion.

Two alternative formats are provided:

- **`0_0_set_up_nuclear_data.ipynb`** — The primary, documented Jupyter notebook, allowing users to inspect and execute the setup step by step.
- **`0_0_set_up_nuclear_data.py`** — A standalone Python script exported from the notebook for command-line execution.

The two are alternatives, not sequential steps. Run either one; there is no need to run both.

`0_0_set_up_nuclear_data.ipynb` is maintained as the authoritative source, with the Python script regenerated using Jupyter's built-in export. This keeps the implementation visible in the notebook while avoiding two independently maintained versions.

A shell (`.sh`) version is not provided because the setup relies substantially on Python libraries, including OpenMC. Reimplementing it in shell would introduce unnecessary duplication.