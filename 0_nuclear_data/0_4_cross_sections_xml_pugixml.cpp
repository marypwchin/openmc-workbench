/*
 * Compile on macOS with pugixml installed through MacPorts:
 *
 * c++ -std=c++17 cross_sections_xml_pugixml.cpp \
 *     -I/opt/local/include -L/opt/local/lib -lpugixml \
 *     -o cross_sections_xml_pugixml
 *
 * Compiler options:
 *   -std=c++23           Enable C++23, required for std::filesystem.
 *   -I/opt/local/include Locate pugixml.hpp (MacPorts-specific).
 *   -L/opt/local/lib     Locate the pugixml library (MacPorts-specific).
 *   -lpugixml            Link against pugixml.
 *
 * Place -lpugixml after the source file for conventional linking order.
 * Other installation methods may require different include/library paths.
 *
 * Run:
 *   ./cross_sections_xml_pugixml
 *       Use ENDF/B-VIII.1 (default).
 *
 *   ./cross_sections_xml_pugixml jendl-5
 *       Use JENDL-5.
 *
 *   ./cross_sections_xml_pugixml jeff-4
 *       Use JEFF-4.0.
 *
 *   ./cross_sections_xml_pugixml endf-b8.0
 *       Use ENDF/B-VIII.0.
 *
 * The optional argument specifies a nuclear-data directory under DATA_ROOT,
 * not a full path. If the directory is invalid or cross_sections.xml is
 * missing, the program reports a warning and falls back to ENDF/B-VIII.1.
 *
 * DATA_ROOT and ENDF_B81 are defined in openmc_workbench_config.hpp.
 */
#include <filesystem>
#include <iostream>
#include <pugixml.hpp>
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

    const auto xs_path = nuc_dat_path / "cross_sections.xml";

// Unlike Python's ElementTree.parse(), which raises an exception on failure,
// pugixml's load_file() reports errors through its return value.
    pugi::xml_document xs_xml;
    const auto result = xs_xml.load_file(xs_path.string().c_str());

    if (!result) {
        std::cerr << "XML loading failed: " << xs_path
                  << ": " << result.description() << '\n';
        return 1;
    }

    const auto root = xs_xml.document_element();

    std::cout << "Root: " << root.name() << '\n';

    for (auto element : root.children()) {
        std::cout << "\nElement: " << element.name() << '\t';

        for (auto attr : element.attributes()) {
            std::cout << "  " << attr.name()
                      << " = " << attr.value() << '\t';
        }
    }
    std::cout << '\n';
}
