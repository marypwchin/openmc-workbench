#!/usr/bin/env python
# coding: utf-8

# # Set up OpenMC nuclear data
# 
# <!-- index:description -->
# Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout.
# <!-- /index:description -->
# 
# <!-- generated:structure -->
# ```text
# Set up OpenMC nuclear data
# ├── Disk-space requirements
# ├── Expected directory structure
# ├── Sources
# ├── Downloads and extracted files
# ├── 1. Install the preprocessed HDF5 libraries
# ├── 2. Convert FENDL-3.2c neutron ACE data
# ├── 3. Install WMP data
# ├── 4. Install depletion chains
# └── 5. Check the installed files
# ```
# <!-- /generated:structure -->
# 
# This notebook installs nuclear-data libraries for use with OpenMC. The libraries reside outside the repository, in the directory specified by `data_root.txt`. Before running the notebook, follow the [Nuclear-data paths](../README.md#nuclear-data-paths) instructions to set that directory and make `openmc_workbench_config` available in your Jupyter Python environment. You will also need OpenMC and `tqdm` (`%pip install tqdm` if needed).
# 
# A standalone alternative, [0_0_set_up_nuclear_data.py](0_0_set_up_nuclear_data.py), is exported from this notebook. **Run either the notebook or the Python script, not both.**
# 
# The installation includes preprocessed HDF5 libraries, windowed multipole (WMP) data, and fast-spectrum depletion chains. FENDL-3.2c requires an additional step: its neutron ACE files are converted to OpenMC HDF5 format. The published [OpenMC nuclear-data page](https://openmc.org/data/) offers FENDL-3.2 data, which is different from FENDL-3.2c.
# 
# Before starting:
# 
# 1. Review the disk-space requirements below. Downloaded archives can expand to much larger files.
# 2. Download **FENDL-3.2c → Neutron → ACE** from the [IAEA](https://www-nds.iaea.org/fendl/) and save the ZIP file locally. Set `LOCAL_ARCHIVES["fendl-3.2c"]` in the code below to its path. Other entries can remain `None` for automatic downloads.
# 3. Run once with `APPLY = False` to see the planned downloads and conversions. Set `APPLY = True` and rerun to install the files.
# 
# Libraries that already have a `cross_sections.xml` index are skipped. Downloads and conversions may take considerable time; progress bars show download and checksum progress.
# 
# ## Disk-space requirements
# 
# Compressed archives can require substantially more space once extracted. Check the available disk space before setting `APPLY = True`.
# 
# The following installed sizes were measured using `du -h` for this setup. They are approximate and may differ between releases or filesystems.
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
# Allow approximately **126 GiB for the installed data**, plus space for downloaded archives in `_downloads/` and extracted files in `_staging/`. The converted FENDL HDF5 files are installed separately, while the original ACE files remain in staging. The highest disk-space use during installation will therefore exceed the table total. Any pre-existing ENDF/B-VIII.0 files also require additional space.
# 
# The notebook does not delete downloaded archives or staging files automatically. Remove them only after checking the installation.
# 

# ## Expected directory structure
# 
# The nuclear-data directory specified by `data_root.txt` will contain the following folders:
# 
# ```text
# DATA_ROOT/
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
# ├── _downloads/    # downloaded archives; may be retained
# └── _staging/      # extracted archives; may be removed after checking
# ```
# 
# WMP data and depletion chains are kept separate from the neutron, photon, and thermal libraries. The available subdirectories depend on the contents of each published archive.
# 

# In[ ]:


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


# ## Sources
# 
# The preprocessed HDF5 libraries and fast-spectrum depletion chains are available from [OpenMC nuclear data](https://openmc.org/data/). If a download is blocked, save the archive using a browser and enter its location in `LOCAL_ARCHIVES`.
# 
# Download **FENDL-3.2c → Neutron → ACE** from the [IAEA FENDL page](https://nds.iaea.org/fendl/), then enter the saved ZIP path in `LOCAL_ARCHIVES`. This archive contains neutron ACE data at the supplied temperature; it is not the FENDL-3.2 HDF5 library.
# 
# WMP v1.1 is available from the [MIT WMP Library release](https://github.com/mit-crpg/WMP_Library/releases/tag/v1.1). WMP data and depletion chains are selected separately when preparing an OpenMC calculation.
# 

# In[ ]:


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


# ## Downloads and extracted files
# 
# Archives are extracted into `_staging/`, then the installed data are placed in their final directories. Existing installation directories are not overwritten. The notebook retains the staging files so that incomplete installations can be inspected. After checking the installed files, you may remove staging files to recover disk space.
# 
# If a published SHA-256 checksum is entered in `EXPECTED_SHA256`, the notebook compares it with the downloaded or local archive and stops if it differs. Without a published reference checksum, the calculated value is **recorded but not verified**. Values are saved in `_downloads/sha256.json`. Libraries already installed are skipped without checking their original archives again.
# 

# In[ ]:


def check_sha256(key, path):
    """Verify against a supplied reference, or record the hash without verification."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream, tqdm(
        total=Path(path).stat().st_size,
        desc=f"SHA-256 {key}",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
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
    records[key] = {
        "path": str(Path(path).resolve()),
        "sha256": actual,
        "status": status,
        "expected_sha256": expected,
    }
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
            with tqdm(
                total=total,
                desc=f"Download {key}",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress:
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


# ## 1. Install the preprocessed HDF5 libraries
# 
# The ENDF/B-VIII.1, JEFF-4.0, and JENDL-5 archives already contain HDF5 files for OpenMC. This step downloads and installs them; it does not process raw evaluated nuclear data.
# 

# In[ ]:


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


# ## 2. Convert FENDL-3.2c neutron ACE data
# 
# OpenMC reads the processed ACE tables and converts them to HDF5. This is not a conversion from raw ENDF files. If an error stops the conversion, a partial directory may remain and should be inspected before trying again.
# 
# Some FENDL ZIP archives use Deflate64 compression, which Python's `zipfile` cannot extract. In that case, the notebook uses the command-line `unzip` utility.
# 
# The IAEA archive stores ACE tables without filename extensions under `neutron/ace/`. The `.xsd` files contain metadata and are not converted. An earlier extraction is reused only if its file list and file sizes match those in the ZIP archive.
# 

# In[ ]:


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


# ## 3. Install WMP data
# 
# WMP v1.1 is installed separately from the cross-section libraries. The files are placed under `wmp/WMP_Library/`.
# 

# In[ ]:


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


# ## 4. Install depletion chains
# 
# This step installs the published fast-spectrum depletion chains under `chains/`. The chain used in a calculation depends on the model and nuclear-data library. Chain files are separate from `cross_sections.xml`.
# 

# In[ ]:


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


# ## 5. Check the installed files
# 
# This final step checks that each installed `cross_sections.xml` index contains entries and that its referenced files exist. It also lists the WMP HDF5 files and depletion-chain files found. These are **file checks**, not validation of the nuclear data or physical results.
# 
# Subsequent notebooks can import paths such as `ENDF_B81` from `openmc_workbench_config`. The names are discovered from the directories under `DATA_ROOT` when the configuration module is imported.
# 

# In[ ]:


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

