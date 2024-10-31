"""Generates set of FuseSoC CAPI-2 core file for basejump_stl using some sane defaults."""

import argparse
import os
import sys

from ruamel.yaml import YAML


def add_header(core_yaml, vendor, library, module, name, version, description):
    """Add CAPI-2 vlnv header to a yaml dictionary."""
    core_yaml["CAPI=2"] = ""
    core_yaml["name"] = f"{vendor}:{library}.{module}:{name}:{version}"
    core_yaml["description"] = description

    return core_yaml


def add_filesets(core_yaml, includes, packages, sources):
    """Add filesets to a yaml dictionary."""
    include_files = [{include: {"is_include_file": True}} for include in includes]
    package_files = [package for package in packages]
    source_files = [source for source in sources]

    rtl = {}
    rtl["files"] = include_files + package_files + source_files
    rtl["file_type"] = "systemVerilogSource"

    core_yaml["filesets"] = {"rtl": rtl}

    return core_yaml


def add_parameters(core_yaml, params):
    """Add parameters to a yaml dictionary."""
    core_yaml["parameters"] = {}
    for pname, pval in params:
        core_yaml["parameters"][pname] = {}
        core_yaml["parameters"][pname]["paramtype"] = "vlogparam"
        core_yaml["parameters"][pname]["datatype"] = "int"

    return core_yaml


def add_targets(core_yaml, toplevel, parameters):
    """Add targets to a yaml dictionary."""
    verilator_tool = {}
    verilator_tool["mode"] = "lint-only"
    verilator_tool["verilator_options"] = ["-Wwarn-lint", "-Wwarn-style", "-Wno-fatal"]

    lint_target = {}
    lint_target["toplevel"] = toplevel
    lint_target["filesets"] = ["rtl"]
    lint_target["default_tool"] = "verilator"
    lint_target["tools"] = {"verilator": verilator_tool}
    lint_target["parameters"] = [f"{param[0]}={param[1]}" for param in parameters]

    core_yaml["targets"] = {"lint": lint_target}

    return core_yaml


def add_footer(core_yaml):
    """Add footer to a yaml dictionary."""
    core_yaml["provider"] = {}
    core_yaml["provider"]["name"] = "github"
    core_yaml["provider"]["user"] = "bespoke-silicon-group"
    core_yaml["provider"]["repo"] = "basejump_stl"
    core_yaml["provider"]["version"] = "v0.0.1"

    return core_yaml


def gen_core_yaml(vlnv, description, includes, packages, sources, parameters):
    """Generate a complete CAPI-2 core yaml dictionary."""
    [vendor, library, module, name, version] = vlnv.split(":")

    core_yaml = {}
    core_yaml = add_header(core_yaml, vendor, library, module, name, version, description)
    core_yaml = add_filesets(core_yaml, includes, packages, sources)
    core_yaml = add_parameters(core_yaml, parameters)
    core_yaml = add_targets(core_yaml, name, parameters)
    core_yaml = add_footer(core_yaml)

    return core_yaml


def dump_core_yaml(core_yaml, cores_root, preview):
    """Dump the core yaml to stdout or a file."""
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 120
    yaml.preserve_quotes = True
    if preview:
        yaml.dump(core_yaml, sys.stdout)
        yaml_target = sys.stdout
    else:
        [_, library_full, name, _] = core_yaml["name"].split(":")
        [_, module] = library_full.split(".")
        output_dir = f"{cores_root}/{module}"
        os.makedirs(output_dir, exist_ok=True)
        yaml_target = f"{output_dir}/{name}.core"
        with open(yaml_target, "w") as f:
            yaml.dump(core_yaml, f)


def main():
    """Generate a set of core files for basejump_stl."""
    parser = argparse.ArgumentParser(description="Generate a core file")

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Previews the core file before writing it",
    )

    parser.add_argument(
        "--cores-root",
        required=True,
        help="Directory where core files will be written",
    )

    # Parse the arguments
    args = parser.parse_args()
    preview = args.preview
    cores_root = args.cores_root

    core_yaml = gen_core_yaml(
        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_abs:0.0.1",
        "Absolute value unit",
        ["bsg_misc/bsg_defines.sv"],
        [],
        ["bsg_misc/bsg_abs.sv"],
        [("width_p", 8)],
    )
    dump_core_yaml(core_yaml, cores_root, preview)

    core_yaml = gen_core_yaml(
        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_adder_cin:0.0.1",
        "Adder with carry-in",
        ["bsg_misc/bsg_defines.sv"],
        [],
        ["bsg_misc/bsg_adder_cin.sv"],
        [("width_p", 8)],
    )
    dump_core_yaml(core_yaml, cores_root, preview)

    core_yaml = gen_core_yaml(
        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_adder_one_hot:0.0.1",
        "Adder of two one-hot vectors",
        ["bsg_misc/bsg_defines.sv"],
        [],
        ["bsg_misc/bsg_adder_one_hot.sv"],
        [("width_p", 8)],
    )
    dump_core_yaml(core_yaml, cores_root, preview)

    core_yaml = gen_core_yaml(
        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_adder_ripple_carry:0.0.1",
        "Adder of two vectors",
        ["bsg_misc/bsg_defines.sv"],
        [],
        ["bsg_misc/bsg_adder_ripple_carry.sv"],
        [("width_p", 8)],
    )
    dump_core_yaml(core_yaml, cores_root, preview)

    core_yaml = gen_core_yaml(
        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_arb_fixed:0.0.1",
        "Fixed priority arbiter",
        ["bsg_misc/bsg_defines.sv"],
        [],
        [
            "bsg_misc/bsg_arb_fixed.sv",
            "bsg_misc/bsg_priority_encode_one_hot_out.sv",
            "bsg_misc/bsg_scan.sv",
        ],
        [("inputs_p", 8), ("lo_to_hi_p", 1)],
    )
    dump_core_yaml(core_yaml, cores_root, preview)


#    core_yaml = gen_core_yaml(
#        "bespoke-silicon-group:basejump_stl:bsg_misc:bsg_mux:0.0.1",
#        "An M-input N-wide multiplexer",
#        ["bsg_misc/bsg_defines.sv"],
#        [],
#        ["bsg_misc/bsg_mux.sv"],
#        [("els_p", 2), ("width_p", 8)],
#    )
#    dump_core_yaml(core_yaml, cores_root, preview)
#
if __name__ == "__main__":
    main()
