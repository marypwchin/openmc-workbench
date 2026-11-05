# Compilers and libraries

A few notes on the compilers and libraries used by the C++ examples. The Linux instructions cover Debian, Ubuntu, and Red Hat Enterprise Linux (RHEL), followed by macOS. The examples use C++23, although they do not necessarily rely on C++23-specific features.

## Linux (Debian, Ubuntu, and Red Hat)

### C++ compilers

GCC is a straightforward choice for compiling the examples. Install the usual build tools if needed.

Debian or Ubuntu:

```bash
sudo apt install build-essential
```

Red Hat Enterprise Linux:

```bash
sudo dnf group install "Development Tools"
```

Check which compiler is being used:

```bash
which g++
g++ --version
```

Clang is another option if installed:

```bash
which clang++
clang++ --version
```

For an example that uses no additional libraries:

```bash
g++ -std=c++23 example.cpp -o example
```

The available C++23 features depend on the compiler and its standard library. In particular, RHEL 9's system GCC is older; a newer [GCC Toolset](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/developing_c_and_cpp_applications_in_rhel_9/assembly_additional-toolsets-for-development-rhel-9_developing-applications) may be needed for `-std=c++23` and newer language features.

### HDF5

HDF5 includes `h5c++`, a wrapper that supplies the compiler and linking options needed by its C++ interface.

Debian or Ubuntu:

```bash
sudo apt install libhdf5-dev
```

Red Hat Enterprise Linux:

```bash
sudo dnf install hdf5-devel
```

On RHEL 9, `hdf5-devel` is available through EPEL, which may need to be enabled first (see [Red Hat's EPEL setup guidance](https://www.redhat.com/en/blog/install-epel-linux)).

Inspect the installed wrapper:

```bash
which h5c++
h5c++ -show
h5c++ -showconfig
```

- `which h5c++` shows which installation is being used.
- `h5c++ -show` prints the underlying compiler command, including include paths and libraries.
- `h5c++ -showconfig` reports the HDF5 build configuration.

Compile the HDF5 example with:

```bash
h5c++ -std=c++23 inspect_hdf5.cpp -o inspect_hdf5
```

The wrapper may use GCC or another compiler, depending on how HDF5 was built. Check `-show` rather than assuming.

### XML and pugixml

The XML example uses [pugixml](https://pugixml.org/). Install its development package.

Debian or Ubuntu:

```bash
sudo apt install libpugixml-dev
```

Red Hat Enterprise Linux:

```bash
sudo dnf install pugixml-devel
```

On RHEL 9, `pugixml-devel` is available through EPEL.

Then compile with:

```bash
g++ -std=c++23 inspect_xml.cpp -o inspect_xml -lpugixml
```

These packages install headers and libraries in standard system locations, so extra `-I` and `-L` options are normally unnecessary.

## macOS

### C++ compilers

Apple Clang is available through Xcode or Apple's command-line developer tools. To inspect the compiler selected by those tools:

```bash
xcrun --find clang++
xcrun clang++ --version
```

MacPorts can also provide GCC, with versioned executable names. For GCC 15:

```bash
which g++-mp-15
g++-mp-15 --version
```

A Conda environment may provide another Clang compiler. Check the executable name shown by a library's compiler wrapper; in one `openmc-env` installation, `h5c++ -show` uses `arm64-apple-darwin20.0.0-clang++`.

For a standalone C++ example using Apple Clang:

```bash
clang++ -std=c++23 example.cpp -o example
```

### HDF5

In the `openmc-env` Conda environment, HDF5 provides `h5c++`. Activate the environment and inspect the wrapper:

```bash
conda activate openmc-env
which h5c++
h5c++ -show
h5c++ -showconfig
```

Here, `h5c++ -show` identifies the Conda compiler and the HDF5 libraries and paths supplied automatically. The precise flags depend on the environment; there is no need to copy them into the build command.

Compile the HDF5 example with:

```bash
h5c++ -std=c++23 inspect_hdf5.cpp -o inspect_hdf5
```

`h5c++` is a compiler wrapper, not a separate C++ compiler. Its underlying compiler may differ from the one returned by `which clang++`.

### XML and pugixml

In this macOS setup, pugixml is installed through MacPorts. Check the installation:

```bash
port installed pugixml
```

Compile the XML example with Apple Clang:

```bash
clang++ -std=c++23 inspect_xml.cpp -o inspect_xml \
    -I/opt/local/include -L/opt/local/lib -lpugixml
```

Here:

- `-I/opt/local/include` gives the compiler the location of `pugixml.hpp`.
- `-L/opt/local/lib` gives the linker the library directory.
- `-lpugixml` links the pugixml library.

An error about a missing `pugixml.hpp` usually indicates an include-path issue. Undefined pugixml symbols at link time usually indicate a missing or incorrect library option.

The HDF5 and pugixml examples use different installations here—Conda for HDF5 and MacPorts for pugixml—so their build commands are kept separate.
