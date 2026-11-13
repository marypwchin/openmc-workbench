# Enabling MPI in OpenMC across computing platforms

This is a log of getting OpenMC working on the computing systems used for the Workbench's MPI, HPC, and HTC explorations. It documents the environments, obstacles, failed approaches, and workarounds encountered along the way. All installation and execution obstacles were successfully resolved, and MPI-enabled OpenMC ran on all three systems.

This is not a general installation guide. The commands document what was used on each system. System-specific path variables (e.g., `$SHARED_STORAGE`, `$SITE_MPICH_ROOT`, and `$USER_MINIFORGE_ROOT`) stand in for the actual values: these excerpts are historical records, not commands to paste without adaptation. Modules and scheduler policies remain system-specific.

## Resources at a glance

| System | User's allocation | OpenMC / MPI stack  | What has been established |
| --- | --- | --- | --- |
| **System A — Containerized platform** (separate containers, shared persistent storage) | 6 containers, each exposing 72 logical CPUs | OpenMC 0.16.0, Conda Open MPI build, Python 3.14 | MPI/OpenMP runs with 1 MPI × 1 OpenMP, 2 × 1, and 1 × 2; executable discovery fix; persistent Conda prefix for use across containers |
| **System B — Slurm / site MPICH** (offline source build) |  Tens to hundreds of jobs at a time | OpenMC 0.16.0 compiled from source, site MPICH 4.3.0b1, GCC 13.3, parallel HDF5 1.13.0 | Offline C++ and Python API installations; two MPI processes launched on `[compute-node-B]`; OpenMC reported 2 MPI × 2 OpenMP |
| **System C — Slurm / Conda Open MPI** (Conda-installed OpenMC and MPI) | 30 jobs at a time | OpenMC 0.16.0 from conda-forge; Open MPI 5.0.11; Slurm 24.05.2 | Two-rank MPI collective communication passed after avoiding UCX; OpenMC subsequently reported 2 MPI × 1 OpenMP |

## 1. System A — containerized platform with shared persistent storage

### 1.1 Initial environment

Experiments started in separate containers, here called `container A1` and `container A2`. There are 6 containers, each exposing 72 logical CPUs (2 sockets × 18 cores × 2 hardware threads).

The existing Conda installation was at a container-local prefix (masked here):

```text
$CONTAINER_CONDA_ROOT
```

The original environment, `openmc-env`, contained OpenMC 0.16.0 but its build identifier included `dagmc_nompi_py314`: that OpenMC executable was not MPI-enabled. Loading an MPI module could not change a non-MPI OpenMC binary into an MPI-enabled one.

A separate system/module Open MPI 4.1.6 was available, with executables under a site-managed prefix (masked here):

```text
$SITE_OPENMPI_ROOT/bin/mpirun
$SITE_OPENMPI_ROOT/bin/mpicxx
```

This was not the same MPI implementation/prefix used by the eventual Conda OpenMC build.

### 1.2 Installing an MPI-enabled Conda build

The MPI-capable environment explicitly selected the conda-forge Open MPI variant of OpenMC 0.16.0:

```bash
conda create -n openmc-mpi \
    --override-channels -c conda-forge \
    "openmc=0.16.0=*mpi_openmpi*" \
    "openmpi>=5,<6"
```

The `*mpi_openmpi*` build selector mattered. A generic `openmc=0.16.0` specification could select a `nompi` build. Pairing the selected OpenMC binary with the Conda MPI launcher also avoided accidentally mixing it with the separate Open MPI 4.1.6 module.

The new environment did not automatically appear as a Jupyter kernel. Kernel registration was recorded as:

```bash
python -m ipykernel install --user \
    --name openmc-mpi \
    --display-name "Python (OpenMC MPI)"
```

### 1.3 Resolved: Conda environment not shared between containers

An environment installed by name under a container's local Conda prefix, e.g.

```text
$CONTAINER_CONDA_ROOT/envs/openmc-mpi
```

was available in `container A1` but not automatically in `container A2`. The containers did not share that Conda directory even though they could access the same persistent user storage.

The change was to install the environment by prefix in the platform's shared persistent directory instead of using a container-local named environment:

```bash
conda create \
    --prefix "$SHARED_STORAGE/conda-envs/openmc-mpi" \
    --override-channels -c conda-forge \
    "openmc=0.16.0=*mpi_openmpi*" \
    "openmpi>=5,<6"
```

Activation from another container used the full prefix:

```bash
conda activate "$SHARED_STORAGE/conda-envs/openmc-mpi"
```

`--prefix` and `-n` were alternative ways of specifying the destination. The shared prefix addressed persistent filesystem visibility.

### 1.4 Resolved: notebook subprocesses could not find `mpiexec` or `openmc`

The initial notebook invocation:

```python
openmc_model.run(mpi_args=["mpiexec", "-n", "2"])
```

raised `FileNotFoundError` when the launcher was not on the notebook process's `PATH`. An explicit MPI launcher path got past that exception, but `prterun` then failed to locate the **OpenMC executable**. Finding the launcher and finding its target executable were two separate issues.

Both were resolved by constructing paths from the Python environment that was actually running the notebook:

```python
from pathlib import Path
import sys

bin_dir = Path(sys.prefix) / "bin"

mpiexec = bin_dir / "mpiexec"
openmc_exec = bin_dir / "openmc"

statepoint_path = openmc_model.run(
    mpi_args=[str(mpiexec), "-n", "2"],
    openmc_exec=str(openmc_exec),
)
```

This avoided relying on the Jupyter server's inherited `PATH` and kept the OpenMC executable and MPI launcher in the same Conda environment.

### 1.5 Tests and status

| MPI processes | OpenMP threads per process | Reported result |
| ---: | ---: | --- |
| 1 | 1 | Worked |
| 2 | 1 | Worked |
| 1 | 2 | Worked |

## 2. System B — Slurm cluster with site-managed MPICH and offline source build

### 2.1 Computing environment

The build was performed on a site-managed Slurm cluster; a separate build node appeared in the installation work. Unlike System A, this was a **Slurm-managed cluster** with a site-provided MPI stack.

| Component | Observed value |
| --- | --- |
| Compiler | GCC 13.3.0 |
| MPI | MPICH 4.3.0b1 (Hydra launcher) |
| Python module | Python 3.13.1 |
| CMake | 3.26.5 (`/bin/cmake`) |
| HDF5 | Parallel HDF5 1.13.0 |
| `mpiexec` | `$SITE_MPICH_ROOT/bin/mpiexec` |
| `mpicxx` | `$SITE_MPICH_ROOT/bin/mpicxx` |
| Parallel HDF5 root | `$SITE_PARALLEL_HDF5_ROOT` |

There was no suitable OpenMC module, so the chosen approach was to compile OpenMC 0.16.0 against **site MPICH**, rather than install another MPI implementation with Conda.

A potentially misleading detail was that `h5cc` and `h5c++` resolved to `/bin`, whereas the parallel-HDF5 wrapper `h5pcc` resolved under the MPICH-linked HDF5 prefix. `h5pcc -showconfig` reported **Parallel HDF5: yes**. The CMake configuration explicitly selected that installation.

### 2.2 Resolved: unavailable GitHub and PyPI access

The initial GitHub clone failed with a network timeout on port 443. The OpenMC v0.16.0 source tree, including submodules, therefore had to be prepared outside the cluster and placed on the cluster filesystem.

Python packaging was blocked separately: `pip install .` attempted to download build requirements and failed with a network error, including an apparent inability to satisfy `setuptools>=80`. The version itself was not the problem; PyPI was unreachable from the cluster.

Linux x86-64 / CPython 3.13 wheels for the build tools and Python dependencies were prepared on a connected system. The distinction from macOS wheels was essential because the connected development machine was Apple Silicon. Dependencies included `setuptools`, `setuptools-scm`, `wheel`, NumPy, h5py, SciPy, IPython, Matplotlib, pandas, lxml, uncertainties, and `endf`.

### 2.3 C++ configuration and build

The source tree was available at `~/openmc`. The recorded CMake configuration selected system MPICH and its matching parallel HDF5:

```bash
cd ~/openmc

export HDF5_ROOT="$SITE_PARALLEL_HDF5_ROOT"

cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="$(which mpicc)" \
    -DCMAKE_CXX_COMPILER="$(which mpicxx)" \
    -DOPENMC_USE_MPI=ON \
    -DOPENMC_USE_OPENMP=ON \
    -DHDF5_PREFER_PARALLEL=ON \
    -DHDF5_ROOT="$HDF5_ROOT" \
    -DOPENMC_BUILD_TESTS=OFF \
    -DGIT_SUBMODULE=OFF \
    -DOPENMC_FORCE_VENDORED_LIBS=ON \
    -DCMAKE_INSTALL_PREFIX="$HOME/.local/openmc-0.16.0"

cmake --build build -j 2
cmake --install build
```

### 2.4 Offline Python installation: two distinct failures

A virtual environment was created for the Python API:

```bash
python -m venv "$HOME/.venvs/openmc-0.16.0"
source "$HOME/.venvs/openmc-0.16.0/bin/activate"
```

**First failure — dependency download.** Pip could not reach PyPI. Pre-downloaded, Linux-compatible wheels were installed from a local wheel directory:

```bash
python -m pip install \
    --no-index \
    --find-links="$HOME/openmc-linux-wheels" \
    "setuptools>=80" "setuptools-scm>=8" wheel
```

**Second failure — wheel staging.** Building the OpenMC Python wheel in the source tree repeatedly produced `[Errno 39] Directory not empty`, at changing paths such as:

```text
build/bdist.linux-x86_64/wheel/openmc/deplete
build/bdist.linux-x86_64/wheel/openmc/lib
```

Removing the staging directory and retrying did not solve it. The changing subdirectory did not establish a fault in either `openmc.deplete` or `openmc.lib`; a staging/cleanup interaction (possibly with the filesystem) was suspected, but its precise cause was not established.

**Working workaround — isolate wheel building from the CMake tree.** Only the Python package and its packaging metadata were copied into a fresh directory under local `/tmp`:

```bash
source "$HOME/.venvs/openmc-0.16.0/bin/activate"

WORKDIR=$(mktemp -d /tmp/openmc-python.XXXXXX)

cp -a ~/openmc/openmc \
      ~/openmc/pyproject.toml \
      ~/openmc/LICENSE \
      "$WORKDIR/"

cd "$WORKDIR"
mkdir -p "$HOME/openmc-built-wheels"

SETUPTOOLS_SCM_PRETEND_VERSION_FOR_OPENMC=0.16.0 \
python -m pip wheel . \
    --no-index \
    --no-build-isolation \
    --no-deps \
    --wheel-dir="$HOME/openmc-built-wheels"
```

The `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_OPENMC` variable supplied the package version because the temporary copy did not retain the Git metadata. Keeping the wheel build in `/tmp` avoided the problematic `build/bdist...` staging tree in the original source checkout.

The resulting wheel was installed offline:

```bash
python -m pip install \
    --no-index \
    --find-links="$HOME/openmc-linux-wheels" \
    --find-links="$HOME/openmc-built-wheels" \
    "openmc==0.16.0"
```

This workaround succeeded. The C++ executable and Python API remained installed in separate user-controlled prefixes.

### 2.5 Slurm execution verified later

MPI execution was subsequently verified in a Slurm allocation on:

```text
[compute-node-B]
```

The hostname probe returned that compute node twice, as expected:

```text
$ mpiexec -n 2 hostname
[compute-node-B]
[compute-node-B]
```

The OpenMC startup banner from the System B run showed:

```text
Version        | 0.16.0
MPI Processes  | 2
OpenMP Threads | 2
```

Thus the process launch reached OpenMC with two MPI ranks, each reporting two OpenMP threads. A two-task Slurm allocation with `--cpus-per-task=1` would reserve only two CPUs, so `OMP_NUM_THREADS=1` was identified as the appropriate match for that allocation. Alternatively, `--cpus-per-task=2` would be needed to reserve four CPUs for 2 MPI × 2 OpenMP.


Unlike System C, System B used the cluster's MPICH and did not require an Open MPI UCX workaround.

## 3. System C — Slurm cluster with Conda-managed Open MPI

### 3.1 Initial checks

The Slurm cluster was reached with a Miniforge base environment at:

```text
$USER_MINIFORGE_ROOT
```

Initially, `which mpiexec` returned nothing and `conda env list` showed only `base`. `module avail` displayed only the core Lmod modules, and `module spider openmpi`, `module spider mpich`, and `module spider mpi` did not find MPI modules.

Subsequent checks established:

| Component | Observation |
| --- | --- |
| Login host | `[login-node-C]` |
| Architecture | x86-64 |
| glibc | 2.43 |
| System GCC | 16.1.1 |
| Slurm | 24.05.2 |
| Slurm MPI plugins | `none`, `pmix`, `pmi2`; PMIx v5 available |
| Miniforge | `$USER_MINIFORGE_ROOT` |

Because no suitable MPI module was present, the Conda Open MPI build of OpenMC was selected.

### 3.2 Conda installation and verification

The environment was created with an explicit MPI-enabled OpenMC build and Open MPI 5:

```bash
conda create -n openmc-mpi \
    -c conda-forge --override-channels \
    --strict-channel-priority \
    python=3.13 \
    "openmc=0.16.0=*mpi_openmpi*" \
    "openmpi>=5,<6" \
    ipykernel
```

The resulting prefix was:

```text
$USER_MINIFORGE_ROOT/envs/openmc-mpi
```

The installed versions and capabilities were confirmed:

```text
OpenMC:             0.16.0
Open MPI:           5.0.11
OpenMC MPI enabled: yes
Parallel HDF5:      yes
DAGMC:              yes
Build:              dagmc_mpi_openmpi_py313h959804f_103
```

OpenMC reported GCC 15.3.0 as its build compiler, while the system compiler was GCC 16.1.1. There was no need to rebuild the precompiled OpenMC package.

### 3.3 Resolved: the MPI compiler wrapper could not find its underlying compiler

A small standalone MPI program written in C++ ([`5_0_test_mpi.cpp`](5_0_test_mpi.cpp)) was used to test MPI independently of OpenMC. During the initial compiler setup, the MPI wrapper reported:

```text
The Open MPI wrapper compiler was unable to find the specified compiler
x86_64-conda-linux-gnu-cc in your PATH.
```

Two approaches were tried:

| Attempt | Outcome |
| --- | --- |
| Override the wrapper to use the system GCC | **Failed** |
| Install Conda's `c-compiler` package | **Succeeded** |

For the C++ test program, the corresponding Conda C++ compiler package and MPI wrapper are:

```bash
conda install -n openmc-mpi \
    -c conda-forge --override-channels \
    cxx-compiler

conda activate openmc-mpi
mpicxx 5_0_test_mpi.cpp -o 5_0_test_mpi
```

### 3.4 Resolved for single-node tests: UCX initialization errors

The initial two-process MPI runs on a compute node produced errors such as:

```text
UCX ERROR bnxt_re0: ibv_create_cq(cqe=256) failed: Input/output error
UCX ERROR uct_iface_open(ud_verbs/bnxt_re0:1) failed
pml_ucx.c:319 Error: Failed to create UCP worker
```

Ranks sometimes reached the test's print statements despite the messages. Those messages were not evidence of a clean transport setup.

For the single-node tests, the working workaround was to bypass the UCX PML and use Open MPI's `ob1` messaging layer:

```bash
export OMPI_MCA_pml=ob1
export OMPI_MCA_btl=self,sm,tcp
```

Then:

```bash
mpiexec -n 2 ./5_0_test_mpi
```

successfully returned both rank identifiers and **exit status 0**, without the earlier UCX errors.

### 3.5 Two-rank collective-communication test

The MPI test program ([`5_0_test_mpi.cpp`](5_0_test_mpi.cpp)) was extended to invoke `MPI_Allreduce`, summing rank IDs over `MPI_COMM_WORLD`. With ranks 0 and 1, the expected sum is 1 on both ranks.

The resulting output was:

```text
MPI rank 1 of 2
MPI rank 0 of 2
Rank 0: sum = 1
Rank 1: sum = 1
```

This verified actual MPI collective communication, beyond merely launching two independent processes or reaching `MPI_Barrier`.

### 3.6 Direct `srun --mpi=pmix` was not the chosen path

Slurm advertised PMIx v5 and accepted direct `srun --mpi=pmix` tests, but PMIx emitted messages including:

```text
Framework: psec
Component: munge
```

Direct launching and MPI/PML issues were not fully resolved or benchmarked. The tested path retained Conda's `mpiexec` inside a Slurm allocation with the `ob1` workaround.

### 3.7 OpenMC execution status

An OpenMC run on System C initially failed before `MPI_INIT` completed (PRRTE reported exit status 14 on `[compute-node-C2]`). A subsequent OpenMC startup reported:

```text
MPI Processes  | 2
OpenMP Threads | 1
```

This established that OpenMC reached MPI initialization successfully in the later run and matched the two-task, one-CPU-per-task Slurm allocation (2 MPI × 1 OpenMP).

```bash
export OMPI_MCA_pml=ob1
export OMPI_MCA_btl=self,sm,tcp
export OMP_NUM_THREADS=1
export OPENMC_CROSS_SECTIONS="$(realpath ../../data/endf-b8.1/cross_sections.xml)"

mpiexec -n 2 openmc
```

`OPENMC_CROSS_SECTIONS="..." mpiexec -n 2 openmc` was also valid as a one-command assignment.

## Cross-system findings

| Topic | Observed lesson |
| --- | --- |
| **MPI implementation** | System A and System C used Conda Open MPI, while System B used the cluster's MPICH. OpenMC and launcher must come from compatible MPI stacks. |
| **Python subprocess paths** | A Jupyter kernel can import OpenMC while being unable to locate `mpiexec` or `openmc` on its `PATH`; resolving both from `sys.prefix/bin` fixed this on System A. |
| **Filesystem scope** | System A required a Conda prefix in persistent shared storage; separate container-local environments did not follow users between containers. |
| **Offline build** | On System B, source access, Python build dependencies, and wheel staging were three distinct problems requiring different workarounds. |
| **Compiler wrappers** | An MPI compiler wrapper requires its configured underlying compiler; System C resolved the missing compiler with Conda. |
| **MPI transport** | System C's failing UCX/RDMA path was avoided for single-node tests with Open MPI `ob1`; a two-rank `MPI_Allreduce` verified that communication worked with that configuration. |
| **Resource matching** | `--ntasks` counts MPI tasks and `--cpus-per-task` reserves CPUs per task. `OMP_NUM_THREADS` must be matched to that allocation. |

