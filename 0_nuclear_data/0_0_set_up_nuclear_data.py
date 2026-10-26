# Python version of openmc_nuclear_data_setup.ipynb.
# Install the shared module first: python -m pip install -e /absolute/path/to/openmc-workbench
# Configure DATA_ROOT in openmc_workbench_config.py; edit APPLY and LOCAL_ARCHIVES below.

# %% [markdown]
# # Set up OpenMC nuclear data
#
# **Notebook outline**
# ```text
# Set up OpenMC nuclear data
# ├── Intended directory layout
# ├── Sources
# ├── Download, extraction, and path handling
# ├── 1. Install the preprocessed HDF5 libraries
# ├── 2. Convert FENDL-3.2c neutron ACE data
# ├── 3. Install WMP data
# ├── 4. Install depletion chains
# └── 5. Check the installed layout
# ```
#
# Populate the directory layout below with published HDF5 libraries, WMP data, and depletion chains. The [OpenMC download page](https://openmc.org/data/) lists preprocessed HDF5 data for FENDL-3.2, but not FENDL-3.2c; for the latter, convert the IAEA neutron ACE archive to OpenMC HDF5 format. This directory layout will be used in subsequent notebooks.
#
# This notebook starts with no nuclear-data files downloaded. Run it in a Jupyter environment containing OpenMC and `tqdm` (`%pip install tqdm` if needed). Progress bars show elapsed time and, when the total is known, estimated time remaining. Downloads can require several GB per library.
#
# Before running the installation:
#
# 1. Download **FENDL-3.2c → Neutron → ACE** from [IAEA](https://nds.iaea.org/fendl/) and save the ZIP in `~/Downloads/`. Set `LOCAL_ARCHIVES["fendl-3.2c"]` below to the saved filename. This archive is downloaded manually; the notebook converts it to HDF5.
# 2. Leave the other `LOCAL_ARCHIVES` values as `None`. The notebook downloads those HDF5 and WMP archives, and the depletion chains, automatically when installation is enabled.
# 3. Run with `APPLY = False` to preview the steps, then set `APPLY = True` and rerun to create the directories and install the data.
#
# Existing indexed libraries are skipped if the notebook is run again.
#
# ## Disk-space requirements
#
# **Beware of file-size expansion:** compressed downloads can expand into much larger HDF5 libraries. Check available disk space before setting `APPLY = True`.
#
# The following approximate installed sizes were measured with `du -h` for this setup (GiB and MiB, rounded). These are planning figures, not fixed sizes for every release or filesystem.
#
# | Library or data | Installed disk space | Main contributor |
# | --- | ---: | --- |
# | ENDF/B-VIII.1 | 43 GiB | Thermal data: 37 GiB |
# | JEFF-4.0 | 51 GiB | Thermal data: 45 GiB |
# | JENDL-5 | 31 GiB | Thermal: 17 GiB; neutron: 14 GiB |
# | FENDL-3.2c | 907 MiB | Neutron HDF5 files |
# | WMP v1.1 | 16 MiB | WMP HDF5 files |
# | Depletion chains | 123 MiB | XML files |
#
# Allow approximately **126 GiB for the installed data alone**, plus additional space for retained archives in `_downloads/` and extraction files in `_staging/`. The FENDL ACE files remain in staging alongside the converted HDF5 files. Peak installation space therefore exceeds the installed total; archive and staging sizes are not included in the table. Existing ENDF/B-VIII.0 data, if retained from an earlier installation, consumes additional space and is excluded from this total.
#
# The notebook does not automatically delete downloads or staging files. Remove them manually only after checking the installation.

# %% [markdown]
# ## Intended directory layout
#
# ```text
# ~/data/
# ├── endf-b8.1/
# │   ├── cross_sections.xml
# │   ├── neutron/
# │   ├── photon/
# │   └── thermal/
# ├── fendl-3.2c/
# │   ├── cross_sections.xml
# │   └── neutron/
# ├── jeff-4/
# │   ├── cross_sections.xml
# │   ├── neutron/
# │   ├── photon/
# │   └── thermal/
# ├── jendl-5/
# │   ├── cross_sections.xml
# │   ├── neutron/
# │   ├── photon/
# │   └── thermal/
# ├── wmp/
# │   └── WMP_Library/
# ├── chains/
# │   ├── chain-endf-b8.1-fast.xml
# │   ├── chain-jeff-4-fast.xml
# │   └── chain-jendl-5-fast.xml
# ├── _downloads/    # temporary archive downloads; optional to retain
# └── _staging/      # temporary archive extraction
# ```
#
# WMP and depletion chains are kept separate from transport libraries. Archive contents determine the available neutron, photon and thermal subdirectories.

# %%
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from tqdm import tqdm

from openmc_workbench_config import DATA_ROOT

ROOT = DATA_ROOT
APPLY = False  # True installs data; False prints the steps only.

# 'None' downloads the archive during installation.
# Download the FENDL neutron ACE ZIP manually first, then set its saved path.
LOCAL_ARCHIVES = {
    "endf-b8.1": None,
    "jeff-4": None,
    "jendl-5": None,
    "wmp": None,
    "fendl-3.2c": Path.home() / "Downloads" / "fendl-FENDL-3.2c-neutron-ace.zip",
}
# Add SHA-256 values only from a trusted publisher source.
# Keys match LOCAL_ARCHIVES, or the chain filenames in CHAIN_URLS.
EXPECTED_SHA256 = {}

print("Data directory:", ROOT)
print("Install data:", APPLY)

# %% [markdown]
# ## Sources
#
# HDF5 archives and fast-spectrum depletion chains are linked from [OpenMC Cross Sections](https://openmc.org/data/). If a download is blocked, download the archive in a browser and set its path in `LOCAL_ARCHIVES`.
#
# Download **FENDL-3.2c → Neutron → ACE** from [IAEA](https://nds.iaea.org/fendl/), then set the local ZIP path above. This is neutron-only data at the supplied temperature; it is different from FENDL-3.2.
#
# WMP v1.1 comes from the [MIT WMP Library release](https://github.com/mit-crpg/WMP_Library/releases/tag/v1.1). Select WMP and depletion chains separately when using them in a simulation.

# %%
# Published archive links from openmc.org/data/.
HDF5_URLS = {
    "endf-b8.1": "https://anl.box.com/shared/static/6qr7jezzihkj9p9esl5jn19qgpujyjyz.xz",
    "jeff-4":    "https://anl.box.com/shared/static/fmcr8zoox1t6um0rwb2iw1nz72xue8ol.xz",
    "jendl-5":   "https://anl.box.com/shared/static/bitsmk1bjkjfj01h4lh29mmlqs1v30bn.xz",
}
WMP_URL = "https://github.com/mit-crpg/WMP_Library/releases/download/v1.1/WMP_Library_v1.1.tar.gz"

# These are fast-spectrum chain versions; source: openmc.org/data/
CHAIN_URLS = {
    "chain-endf-b8.1-fast.xml": "https://anl.box.com/shared/static/n0pkqe66uotskoljr93szvjyvtvycgze.xml",
    "chain-jeff-4-fast.xml": "https://anl.box.com/shared/static/p6cettxz3ovbp151qg7bc3k9ov0zt3wm.xml",
    "chain-jendl-5-fast.xml": "https://anl.box.com/shared/static/yw4bsaf86d1vhva42wzurwstlp1ynhe5.xml",
}

# %% [markdown]
# ## Download, extraction, and path handling
#
# Archives are unpacked into `_staging/` before being placed in the layout. Existing destination directories are preserved. The notebook does not automatically remove `_staging/` after installation. After the installed layout has been checked, any remaining staging files can be deleted manually to reclaim disk space. If installation fails, keep them for inspection.
#
# Before extraction or copying, SHA-256 hashes are compared with `EXPECTED_SHA256` when a trusted publisher checksum has been supplied. A mismatch stops installation. No reference checksums are preconfigured; without one, the hash is **recorded, not verified**. Records are saved to `_downloads/sha256.json` to identify the input files used. This also applies to local archives, including the manually downloaded FENDL ZIP. Already installed libraries are skipped without rechecking their source archives.

# %%
def check_sha256(key, path):
    """Verify against a supplied reference, or record the hash without verification."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream, tqdm(
        total=Path(path).stat().st_size, desc=f"SHA-256 {key}",
        unit="B", unit_scale=True, unit_divisor=1024
    ) as progress:
        for block in iter(lambda: stream.read(2**20), b""):
            digest.update(block)
            progress.update(len(block))
    actual = digest.hexdigest()
    expected = EXPECTED_SHA256.get(key)
    if expected is not None:
        expected = expected.strip().lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError(f"Invalid reference SHA-256 for {key}")
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch for {key}: expected {expected}, got {actual}")
    status = "verified against supplied reference" if expected else "recorded, not verified"
    print(f"{key}: SHA-256 {actual} ({status})")
    manifest = ROOT / "_downloads" / "sha256.json"
    records = json.loads(manifest.read_text()) if manifest.is_file() else {}
    records[key] = {"path": str(Path(path).resolve()), "sha256": actual,
                    "status": status, "expected_sha256": expected}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(records, indent=2) + "\n")


def download(key, url):
    local = LOCAL_ARCHIVES.get(key)
    archive = Path(local).expanduser() if local else ROOT / "_downloads" / url.rsplit("/", 1)[-1]
    if not APPLY:
        print("Use local archive" if local else "Download", key, "->", archive)
        return archive
    if local and not archive.is_file():
        raise FileNotFoundError(archive)
    if not archive.is_file():
        archive.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        partial = archive.with_name(archive.name + ".partial")
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
            length = response.headers.get("Content-Length")
            total = int(length) if length and length.isdigit() else None
            with tqdm(total=total, desc=f"Download {key}", unit="B",
                      unit_scale=True, unit_divisor=1024) as progress:
                for block in iter(lambda: response.read(2**20), b""):
                    output.write(block)
                    progress.update(len(block))
        partial.replace(archive)
    check_sha256(key, archive)
    return archive


def unpack(archive, name):
    stage = ROOT / "_staging" / name
    if stage.exists():
        raise FileExistsError(f"Inspect or remove the previous staging directory: {stage}")
    stage.mkdir(parents=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                (stage / member.filename).resolve().relative_to(stage.resolve())
            try:
                zf.extractall(stage)
            except NotImplementedError:
                subprocess.run(["unzip", "-o", str(archive), "-d", str(stage)], check=True)
    else:
        with tarfile.open(archive) as tf:
            # Reject links and paths outside staging, including on older Python versions.
            for member in tf.getmembers():
                (stage / member.name).resolve().relative_to(stage.resolve())
                if not (member.isfile() or member.isdir()):
                    raise ValueError(f"Unsupported archive member: {member.name}")
            tf.extractall(stage, filter="data")
    return stage


def normalize_index(index):
    # Keep paths relative so the complete data directory can be relocated.
    tree = ET.parse(index)
    root = tree.getroot()
    directory = root.find("directory")
    base = index.parent
    if directory is not None:
        base = Path(directory.text.strip())
        if not base.is_absolute():
            base = index.parent / base
    for entry in root.findall("library"):
        target = (base / entry.attrib["path"]).resolve()
        relative = target.relative_to(index.parent.resolve())
        if not target.is_file():
            raise FileNotFoundError(target)
        entry.set("path", relative.as_posix())
    if directory is not None:
        root.remove(directory)
    ET.indent(tree, space="  ")
    tree.write(index, encoding="utf-8", xml_declaration=True)

# %% [markdown]
# ## 1. Install the preprocessed HDF5 libraries

# %%
for key, url in HDF5_URLS.items():
    destination = ROOT / key
    if (destination / "cross_sections.xml").is_file():
        print(key, "already installed")
        continue
    if APPLY and destination.exists():
        raise FileExistsError(destination)
    archive = download(key, url)
    if not APPLY:
        continue
    stage = unpack(archive, key)
    indexes = list(stage.rglob("cross_sections.xml"))
    if len(indexes) != 1:
        raise ValueError(f"Expected one cross_sections.xml in {archive}; found {len(indexes)}")
    normalize_index(indexes[0])
    shutil.move(str(indexes[0].parent), str(destination))
    print("Installed", destination)

# %% [markdown]
# ## 2. Convert FENDL-3.2c neutron ACE data
#
# Import processed ACE directly with OpenMC; this step does not process raw ENDF data. Conversion stops on an error. A failed run may leave a partial directory; inspect it before retrying.
#
# Some FENDL ZIP archives use Deflate64 compression, which Python’s `zipfile` cannot extract. The notebook falls back to the command-line `unzip` utility.
#
# The IAEA archive stores extensionless ACE tables in `neutron/ace/`; the accompanying `.xsd` files are metadata and are excluded. A previous extraction is reused if its file inventory and sizes match the ZIP.

# %%
destination = ROOT / "fendl-3.2c"
if (destination / "cross_sections.xml").is_file():
    print("FENDL-3.2c already installed")
elif not APPLY:
    print("Convert", LOCAL_ARCHIVES["fendl-3.2c"], "->", destination)
else:
    import openmc.data

    if destination.exists():
        raise FileExistsError(destination)
    archive = Path(LOCAL_ARCHIVES["fendl-3.2c"]).expanduser()
    check_sha256("fendl-3.2c", archive)
    stage = ROOT / "_staging" / "fendl-3.2c"
    if stage.exists():
        # Reuse a completed extraction after checking the archive's file inventory.
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                target = stage / member.filename
                target.resolve().relative_to(stage.resolve())
                if not member.is_dir() and (
                    not target.is_file() or target.stat().st_size != member.file_size
                ):
                    raise ValueError(f"Incomplete extraction: {target}. Remove {stage} and rerun.")
        print("Using extracted archive:", stage)
    else:
        stage = unpack(archive, "fendl-3.2c")
    # IAEA uses extensionless ACE filenames; .xsd files are metadata.
    ace_directory = stage / "neutron" / "ace"
    ace_files = sorted(p for p in ace_directory.glob("*")
                       if p.is_file() and p.suffix in ("", ".ace"))
    if not ace_files:
        raise ValueError(f"No neutron ACE tables found in {ace_directory}")
    neutron = destination / "neutron"
    neutron.mkdir(parents=True)
    library = openmc.data.DataLibrary()
    for ace in tqdm(ace_files, desc="Convert FENDL-3.2c", unit="file"):
        data = openmc.data.IncidentNeutron.from_ace(ace)
        output = neutron / (data.name + ".h5")
        if output.exists():
            raise FileExistsError(output)
        data.export_to_hdf5(output)
        library.register_file(output)
    library.export_to_xml(destination / "cross_sections.xml")
    normalize_index(destination / "cross_sections.xml")
    print("Converted", len(ace_files), "ACE files")

# %% [markdown]
# ## 3. Install WMP data

# %%
destination = ROOT / "wmp" / "WMP_Library"
if destination.is_dir() and any(destination.rglob("*.h5")):
    print("WMP already installed")
else:
    archive = download("wmp", WMP_URL)
    if APPLY:
        if destination.exists():
            raise FileExistsError(destination)
        stage = unpack(archive, "wmp")
        folders = [p for p in stage.rglob("WMP_Library")
                   if p.is_dir() and any(p.rglob("*.h5"))]
        if len(folders) != 1:
            raise ValueError("Expected one WMP_Library directory containing HDF5 files")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(folders[0]), str(destination))
        print("Installed", destination)

# %% [markdown]
# ## 4. Install depletion chains
#
# These are the published fast-spectrum versions. Chain selection depends on the simulation; the files are separate from `cross_sections.xml`.

# %%
for name, url in CHAIN_URLS.items():
    destination = ROOT / "chains" / name
    if destination.is_file():
        print(name, "already installed")
        continue
    if not APPLY:
        print("Download", name, "->", destination)
        continue
    archive = download(name, url)
    if ET.parse(archive).getroot().tag != "depletion_chain":
        raise ValueError(f"Not a depletion chain: {archive}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, destination)

# %% [markdown]
# ## 5. Check the installed layout
#
# Check that the indexes and their referenced files exist. This is a file check, not validation of the nuclear data.
#
# In subsequent notebooks, import `ENDF_B81` from `openmc_workbench_config` to locate the ENDF/B-VIII.1 library. All notebooks share `DATA_ROOT` from that module, independently of the notebook working directory.

# %%
for key in (*HDF5_URLS, "fendl-3.2c"):
    index = ROOT / key / "cross_sections.xml"
    if not index.is_file():
        print(key, "not installed")
        continue
    entries = ET.parse(index).getroot().findall("library")
    missing = [entry.attrib["path"] for entry in entries
               if not (index.parent / entry.attrib["path"]).is_file()]
    print(key, f"{len(entries)} entries; {len(missing)} missing files")
    if not entries or missing:
        raise ValueError(f"Check {index}: empty index or missing files: {missing[:5]}")

print("WMP HDF5 files:", len(list((ROOT / "wmp").rglob("*.h5"))))
print("Chain files:", [p.name for p in sorted((ROOT / "chains").glob("*.xml"))])
