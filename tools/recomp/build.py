"""Hash-gated Windows AOT build; all derived output stays under work/."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import os
import sys
from ram_fields import apply as apply_ram_fields

ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_REVISION = "5e89943528aee7bc1c399bdbd035364a4b41dd10"


def baseline(context):
    section = context.split("### 1.1 ", 1)[1].split("### 1.2 ", 1)[0]
    return {key: re.search(rf"\| {key} \| `([0-9a-f]+)`", section)[1]
            for key in ("SHA1", "SHA256")}


def verify_rom(rom, expected):
    data = rom.read_bytes()
    for key, value in expected.items():
        actual = hashlib.new(key.lower(), data).hexdigest()
        if actual != value:
            raise ValueError(f"ROM {key} mismatch: {actual}; expected {value}")
    # Decode the signed ARM B displacement rather than assume entry at 0xC0.
    word = int.from_bytes(data[:4], "little")
    if word & 0xFF000000 != 0xEA000000:
        raise ValueError("ROM header does not contain an unconditional ARM B")
    displacement = word & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    target = 8 + displacement * 4
    if not 0xC0 <= target < len(data) or target % 4:
        raise ValueError("ROM entry is outside the cartridge code region")
    return len(data), 0x08000000 + target


def private_output(path):
    path = path.resolve()
    if not path.is_relative_to(ROOT / "work"):
        raise ValueError("Build output must be inside this repository's ignored work/")
    return path


def run(args, log):
    print("Running:", " ".join(map(str, args)), flush=True)
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(list(map(str, args)), check=True, stdout=stream,
                       stderr=subprocess.STDOUT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROOT / "Road Rash - Jailbreak (USA).gba")
    parser.add_argument("--output", type=Path, default=ROOT / "work/native")
    parser.add_argument("--framework", type=Path, default=ROOT / "tools/bin/gbarecomp-src")
    parser.add_argument("--bios", type=Path, help="Local 16 KiB BIOS; never copied into tracked paths")
    parser.add_argument("--bios-overlay", type=Path, action="append", default=[],
                        help="Reviewed BIOS analysis overlay; identity must match supplied BIOS")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    expected = baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8"))
    size, entry = verify_rom(args.rom.resolve(), expected)
    if not args.generate_only and not args.bios:
        raise ValueError("A host build requires --bios; use --generate-only for cartridge analysis")
    bios_data = args.bios.resolve().read_bytes() if args.bios else b""
    if args.bios and len(bios_data) != 16384:
        raise ValueError("BIOS must be exactly 16 KiB")
    out = private_output(args.output)
    revision = subprocess.check_output(["git", "-C", str(args.framework), "rev-parse", "HEAD"], text=True).strip()
    if revision != FRAMEWORK_REVISION:
        raise ValueError(f"Framework revision mismatch: {revision}")
    if args.jobs < 1:
        raise ValueError("--jobs must be positive")
    out.mkdir(parents=True, exist_ok=True)
    print(f"ROM SHA1 + SHA256 verified; header entry 0x{entry:08X}", flush=True)
    mingw = Path("C:/msys64/mingw64/bin")
    os.environ["PATH"] = str(mingw) + os.pathsep + os.environ["PATH"]
    cmake = mingw / "cmake.exe"
    tomlpp = ROOT / "tools/bin/tomlpp"
    dependency_args = ([f"-DGBARECOMP_TOMLPP_INCLUDE_DIR={tomlpp.as_posix()}"]
                       if (tomlpp / "toml.hpp").is_file() else [])
    tool_build = out / "tool-build"
    run([cmake, "-S", args.framework, "-B", tool_build, "-G", "Ninja",
         "-DCMAKE_BUILD_TYPE=Release", "-DGBARECOMP_MINGW_PREFIX_UNIX=C:/msys64/mingw64",
         *dependency_args], out / "configure-tool.log")
    run([cmake, "--build", tool_build, "--target", "gba_recompile", "gba_scan",
         "--parallel", args.jobs], out / "build-tool.log")
    config = out / "game-analysis.toml"
    config.write_text(f'''[program]
name = "Road Rash: Jailbreak"
id = "rrj_usa"
load_address = 0x08000000
size = {size}
entry_pc = 0x08000000
codegen_shards = 64
static_resume_all = true

[identity]
sha1 = "{expected['SHA1']}"
''' + (ROOT / "native/analysis.toml").read_text(encoding="utf-8"), encoding="utf-8")
    generated = out / "generated"
    run([tool_build / "gba_recompile.exe", "--rom", args.rom.resolve(),
         "--config", config, "--max-functions", "20000", "--out", generated], out / "generate.log")
    apply_ram_fields(generated, args.rom.read_bytes(), ROOT / "native/mutable_sites.json")
    (generated / "identity.h").write_text(
        f'#pragma once\n#define RRJ_ROM_SHA1 "{expected["SHA1"]}"\n'
        f'#define RRJ_ROM_SHA256 "{expected["SHA256"]}"\n#define RRJ_ROM_SIZE {size}\n'
        f'#define RRJ_BIOS_SHA1 "{hashlib.sha1(bios_data).hexdigest()}"\n'
        f'#define RRJ_BIOS_SHA256 "{hashlib.sha256(bios_data).hexdigest()}"\n', encoding="utf-8")
    run([tool_build / "gba_scan.exe", args.rom.resolve()], out / "scan.log")
    if args.generate_only:
        return
    bios_dir = out / "generated-bios"
    if args.bios:
        bios = args.bios.resolve()
        data = bios.read_bytes()
        if len(data) != 16384:
            raise ValueError("BIOS must be exactly 16 KiB")
        bios_config = out / "bios-analysis.toml"
        bios_config.write_text(f'''[program]
name = "Local BIOS"
id = "local_bios"
load_address = 0
size = 16384
entry_pc = 0
static_resume_all = true
[identity]
sha1 = "{hashlib.sha1(data).hexdigest()}"
''', encoding="utf-8")
        overlays = [item for path in args.bios_overlay for item in ("--config", path.resolve())]
        run([tool_build / "gba_recompile.exe", "--bios", bios, "--config",
             bios_config, *overlays, "--out", bios_dir], out / "generate-bios.log")
    build = out / "build"
    run([cmake, "-S", ROOT / "native", "-B", build, "-G", "Ninja",
         "-DCMAKE_BUILD_TYPE=Release", f"-DRRJ_FRAMEWORK={args.framework.resolve().as_posix()}",
         f"-DRRJ_GENERATED={generated.as_posix()}",
         f"-DGBARECOMP_GENERATED_BIOS_DIR={bios_dir.as_posix()}",
         "-DGBARECOMP_MINGW_PREFIX_UNIX=C:/msys64/mingw64", *dependency_args], out / "configure-host.log")
    run([cmake, "--build", build, "--target", "RoadRashJailbreakRecomp",
         "--parallel", args.jobs], out / "build-host.log")
    print(f"Built: {build / 'RoadRashJailbreakRecomp.exe'}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
