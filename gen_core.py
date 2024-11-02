"""Generates set of FuseSoC CAPI-2 core file for basejump_stl using some sane defaults."""

import argparse
import os
import sys

from ruamel.yaml import YAML


def add_header(core_yaml, vendor, library, name, version, description):
    """Add CAPI-2 vlnv header to a yaml dictionary."""
    core_yaml["CAPI=2"] = ""
    core_yaml["name"] = f"{vendor}:{library}:{name}:{version}"
    core_yaml["description"] = description

    return core_yaml


def add_filesets(core_yaml, includes, packages, sources):
    """Add filesets to a yaml dictionary."""
    package_files = [package for package in packages]
    vinclude_files = [{include: {"is_include_file": True}} for include in includes if include.endswith(".svh")]
    vsrc_files = [source for source in sources if source.endswith(".sv")]
    cinclude_files = [{include: {"is_include_file": True}} for include in includes if include.endswith(".hpp")]
    csrc_files = [source for source in sources if source.endswith(".cpp")]

    rtl = {}
    if vsrc_files or vinclude_files:
        rtl["files"] = vinclude_files + package_files + vsrc_files
        rtl["file_type"] = "systemVerilogSource"

    nonsynth = {}
    if csrc_files or cinclude_files:
        nonsynth["files"] = cinclude_files + csrc_files
        nonsynth["file_type"] = "cppSource"

    core_yaml["filesets"] = {"rtl": rtl, "nonsynth": nonsynth}

    return core_yaml


def add_footer(core_yaml):
    """Add footer to a yaml dictionary."""
    core_yaml["provider"] = {}
    core_yaml["provider"]["name"] = "github"
    core_yaml["provider"]["user"] = "bespoke-silicon-group"
    core_yaml["provider"]["repo"] = "basejump_stl"
    core_yaml["provider"]["version"] = "v0.0.1"

    return core_yaml


def gen_core_yaml(vlnv, description, includes, packages, sources):
    """Generate a complete CAPI-2 core yaml dictionary."""
    [vendor, library, name, version] = vlnv.split(":")

    core_yaml = {}
    core_yaml = add_header(core_yaml, vendor, library, name, version, description)
    core_yaml = add_filesets(core_yaml, includes, packages, sources)
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
        [_, _, name, _] = core_yaml["name"].split(":")
        os.makedirs(cores_root, exist_ok=True)
        yaml_target = f"{cores_root}/{name}.core"
        with open(yaml_target, "w") as f:
            yaml.dump(core_yaml, f)


def extract_submodule(basejump_stl_root, submodule_root):
    """Extract the submodule files from the basejump_stl directory."""
    info = {
        "root": submodule_root,
        "incs": [],
        "pkgs": [],
        "srcs": [],
        "test": [],
        "errs": [],
    }
    files = []
    for root, _, filenames in os.walk(f"{basejump_stl_root}/{submodule_root}"):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), f"{basejump_stl_root}/{submodule_root}")
            files.append(rel_path)
    for f in files:
        if "nonsynth" in f:
            info["test"].append(f)
        elif f.endswith(".svh"):
            info["incs"].append(f)
        elif f.endswith("_pkg.sv"):
            info["pkgs"].append(f)
        elif f.endswith(".cpp"):
            info["test"].append(f)
        elif f.endswith(".sv"):
            info["srcs"].append(f)
        else:
            info["errs"].append(f)

    return info


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

    parser.add_argument(
        "--basejump-stl-root",
        required=True,
        help="Directory where basejump_stl is located",
    )

    # Parse the arguments
    args = parser.parse_args()
    preview = args.preview
    cores_root = args.cores_root
    basejump_stl_root = args.basejump_stl_root

    bsg_async = extract_submodule(basejump_stl_root, "bsg_async")
    bsg_axi = extract_submodule(basejump_stl_root, "bsg_axi")
    bsg_cache = extract_submodule(basejump_stl_root, "bsg_cache")
    bsg_clk_gen = extract_submodule(basejump_stl_root, "bsg_clk_gen")
    bsg_dataflow = extract_submodule(basejump_stl_root, "bsg_dataflow")
    bsg_dmc = extract_submodule(basejump_stl_root, "bsg_dmc")
    bsg_link = extract_submodule(basejump_stl_root, "bsg_link")
    bsg_mem = extract_submodule(basejump_stl_root, "bsg_mem")
    bsg_noc = extract_submodule(basejump_stl_root, "bsg_noc")
    bsg_tag = extract_submodule(basejump_stl_root, "bsg_tag")
    bsg_test = extract_submodule(basejump_stl_root, "bsg_test")

    rtl_vlnv = "bespoke-silicon-group:basejump_stl:rtl:0.0.1"
    rtl_desc = "BaseJump STL: A Standard Template Library for SystemVerilog"
    rtl_modules = [
        bsg_async,
        bsg_axi,
        bsg_cache,
        bsg_clk_gen,
        bsg_dataflow,
        bsg_dmc,
        bsg_link,
        bsg_mem,
        bsg_noc,
        bsg_tag,
    ]

    rtl_incs = []
    rtl_pkgs = []
    rtl_srcs = []
    rtl_errs = []

    for module in rtl_modules:
        rtl_incs.extend([f"{module['root']}/{f}" for f in module["incs"]])
        rtl_pkgs.extend([f"{module['root']}/{f}" for f in module["pkgs"]])
        rtl_srcs.extend([f"{module['root']}/{f}" for f in module["srcs"]])
        rtl_errs.extend([f"{module['root']}/{f}" for f in module["errs"]])

    rtl_yaml = gen_core_yaml(rtl_vlnv, rtl_desc, rtl_incs, rtl_pkgs, rtl_srcs)
    dump_core_yaml(rtl_yaml, cores_root, preview)

    test_vlnv = "bespoke-silicon-group:basejump_stl:nonsynth:0.0.1"
    test_desc = "BaseJump STL: A Standard Template Library for SystemVerilog (Nonsynthesizable)"
    test_modules = [
        bsg_async,
        bsg_axi,
        bsg_cache,
        bsg_clk_gen,
        bsg_dataflow,
        bsg_dmc,
        bsg_link,
        bsg_mem,
        bsg_noc,
        bsg_tag,
        bsg_test,
    ]

    test_incs = []
    test_pkgs = []
    test_srcs = []
    test_errs = []

    for module in test_modules:
        test_srcs.extend([f"{module['root']}/{f}" for f in module["test"]])
        test_errs.extend([f"{module['root']}/{f}" for f in module["errs"]])

    test_yaml = gen_core_yaml(test_vlnv, test_desc, test_incs, test_pkgs, test_srcs)
    dump_core_yaml(test_yaml, cores_root, preview)

    fakeram = extract_submodule(basejump_stl_root, "hard/fakeram")
    generic = extract_submodule(basejump_stl_root, "hard/generic")
    gf_14 = extract_submodule(basejump_stl_root, "hard/gf_14")
    pickle_40 = extract_submodule(basejump_stl_root, "hard/pickle_40")
    saed_90 = extract_submodule(basejump_stl_root, "hard/saed_90")
    tsmc_16 = extract_submodule(basejump_stl_root, "hard/tsmc_16")
    tsmc_28 = extract_submodule(basejump_stl_root, "hard/tsmc_28")
    tsmc_40 = extract_submodule(basejump_stl_root, "hard/tsmc_40")
    tsmc_180_250 = extract_submodule(basejump_stl_root, "hard/tsmc_180_250")
    ultrascale_plus = extract_submodule(basejump_stl_root, "hard/ultrascale_plus")

    hard_vlnv = "bespoke-silicon-group:basejump_stl:hard:0.0.1"
    hard_desc = "BaseJump STL: A Standard Template Library for SystemVerilog (Hardened)"
    hard_modules = [
        fakeram,
        generic,
        gf_14,
        pickle_40,
        saed_90,
        tsmc_16,
        tsmc_28,
        tsmc_40,
        tsmc_180_250,
        ultrascale_plus,
    ]

    hard_incs = []
    hard_pkgs = []
    hard_srcs = []
    hard_errs = []

    for module in hard_modules:
        hard_incs.extend([f"{module['root']}/{f}" for f in module["incs"]])
        hard_pkgs.extend([f"{module['root']}/{f}" for f in module["pkgs"]])
        hard_srcs.extend([f"{module['root']}/{f}" for f in module["srcs"]])
        hard_errs.extend([f"{module['root']}/{f}" for f in module["errs"]])

    hard_yaml = gen_core_yaml(hard_vlnv, hard_desc, hard_incs, hard_pkgs, hard_srcs)
    dump_core_yaml(hard_yaml, cores_root, preview)


if __name__ == "__main__":
    main()
