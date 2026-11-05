/*
 * Inspect the reaction groups in an OpenMC neutron HDF5 file.
 *
 * Compile (from 0_nuclear_data/) with the HDF5 C++ compiler wrapper:
 *
 *   h5c++ -std=c++23 0_5_inspect_hdf5_reactions.cpp -o inspect_hdf5_reactions
 *
 * The h5c++ wrapper provides the HDF5 headers and linking options.
 * Use h5c++ -show to see the underlying compiler and options.
 *
 * Run:
 *   ./inspect_hdf5_reactions
 *       Inspect Li6.h5 from ENDF/B-VIII.1 (default).
 *
 *   ./inspect_hdf5_reactions jendl-5
 *       Inspect Li6.h5 from JENDL-5.
 *
 *   ./inspect_hdf5_reactions jeff-4 Li7.h5
 *       Inspect Li7.h5 from JEFF-4.0.
 *
 * The first optional argument specifies a nuclear-data directory under
 * DATA_ROOT, not a full path. If the directory is invalid or cross_sections.xml
 * is missing, the program warns and falls back to ENDF/B-VIII.1.
 *
 * The second optional argument specifies a neutron HDF5 filename in that
 * library's neutron/ directory. It defaults to Li6.h5.
 *
 * DATA_ROOT and ENDF_B81 are defined in openmc_workbench_config.hpp.
 */
#include <algorithm>
#include <filesystem>
#include <iostream>
#include <string>
#include <utility>
#include <vector>
#include <H5Cpp.h>
#include "../openmc_workbench_config.hpp"

namespace fs = std::filesystem;

void set_data_path_if_valid(const fs::path& candidate, fs::path& nuc_dat_path)
{
    const auto candidate_path = DATA_ROOT / candidate;
    if (fs::is_regular_file(candidate_path / "cross_sections.xml")) {
        nuc_dat_path = candidate_path;
    }
    else {
        std::cerr << "Invalid nuclear-data directory: " << candidate_path
                  << "\nUsing default: " << nuc_dat_path << '\n';
    }
}

int main(int argc, char* argv[])
{
    fs::path nuc_dat_path = ENDF_B81;

    if (argc > 1) {
        set_data_path_if_valid(argv[1], nuc_dat_path);
    }

    const fs::path nuclide_file = (argc > 2) ? argv[2] : "Li6.h5";
    const auto h5_path = nuc_dat_path / "neutron" / nuclide_file;

    // HDF5 reports failures through C++ exceptions rather than return codes.
    H5::Exception::dontPrint();
    try {
        H5::H5File h5_file(h5_path.string(), H5F_ACC_RDONLY);

        // OpenMC neutron files have a top-level nuclide group, e.g. /Li6.
        if (h5_file.getNumObjs() == 0) {
            std::cerr << "No nuclide group found in: " << h5_path << '\n';
            return 1;
        }
        const auto nuclide_name = h5_file.getObjnameByIdx(0);
        const auto nuclide_group = h5_file.openGroup(nuclide_name);
        const auto reactions = nuclide_group.openGroup("reactions");

        std::vector<std::pair<int, std::string>> reaction_mts;
        for (hsize_t i = 0; i < reactions.getNumObjs(); ++i) {
            const auto name = reactions.getObjnameByIdx(i);
            if (!name.starts_with("reaction_")) {
                continue;
            }

            const auto reaction = reactions.openGroup(name);
            const auto attribute = reaction.openAttribute("mt");
            int mt{};
            attribute.read(H5::PredType::NATIVE_INT, &mt);
            reaction_mts.emplace_back(mt, name);
        }

        std::sort(reaction_mts.begin(), reaction_mts.end());

        std::cout << "HDF5 file: " << h5_path << '\n';
        std::cout << "Nuclide: " << nuclide_name << '\n';
        for (const auto& [mt, name] : reaction_mts) {
            std::cout << "  " << name << "  MT=" << mt << '\n';
        }

        std::cout << "MT numbers:";
        for (const auto& [mt, name] : reaction_mts) {
            std::cout << ' ' << mt;
        }
        std::cout << '\n';
    }
    catch (const H5::Exception& e) {
        std::cerr << "HDF5 read failed: " << h5_path
                  << ": " << e.getDetailMsg() << '\n';
        return 1;
    }
}
