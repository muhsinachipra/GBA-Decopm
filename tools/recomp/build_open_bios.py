"""Assemble the pinned open-source mGBA BIOS shim locally for experimental bring-up.

Not a retail BIOS, and not a final compatibility qualification. All binaries
remain ignored. Use runtime BIOS HLE for SWIs when using this image.
"""
import hashlib
from pathlib import Path
import os
import subprocess
import urllib.request

from build import ROOT, baseline, verify_rom


def main():
    verify_rom(ROOT / "Road Rash - Jailbreak (USA).gba",
               baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")))
    source = ROOT / "tools/bin/hle-bios.s"
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve("https://raw.githubusercontent.com/mgba-emu/mgba/0.10.5/src/gba/hle-bios.s", source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != "0f626f49cb2f0cef95c30cd7a3bbf8fd698085d15a3361a2bc6b9ac10030f062":
        raise ValueError("mGBA BIOS source differs from pinned 0.10.5 source")
    out = ROOT / "work/open-bios"
    out.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = "C:/msys64/mingw64/bin" + os.pathsep + os.environ["PATH"]
    arm = ROOT / "tools/bin/arm-tools/mingw64/bin"
    gcc = Path("C:/msys64/mingw64/bin/gcc.exe")
    for name in ("arm-none-eabi-as.exe", "arm-none-eabi-ld.exe", "arm-none-eabi-objcopy.exe"):
        if not (arm / name).is_file():
            raise FileNotFoundError(f"Install/extract ARM binutils at {arm}")
    commands = [
        [gcc, "-E", "-P", "-x", "assembler-with-cpp", source, "-o", out / "hle-bios.s"],
        [arm / "arm-none-eabi-as.exe", "-mcpu=arm7tdmi", out / "hle-bios.s", "-o", out / "hle-bios.o"],
        # GBA game execution does not use ARM abort/FIQ exceptions. mGBA's
        # shim leaves those symbols external; bind unused vectors to reset.
        [arm / "arm-none-eabi-ld.exe", "-Ttext=0", "-e", "0", "--defsym=pabtBase=0",
         "--defsym=dabtBase=0", "--defsym=fiqBase=0", out / "hle-bios.o", "-o", out / "hle-bios.elf"],
        [arm / "arm-none-eabi-objcopy.exe", "--pad-to", "0x4000", "-O", "binary",
         out / "hle-bios.elf", out / "hle-bios.bin"],
    ]
    for command in commands:
        subprocess.run(list(map(str, command)), check=True)
    image = (out / "hle-bios.bin").read_bytes()
    if len(image) != 16384 or hashlib.sha1(image).hexdigest() != "73528a5d6ea2c163e82956b1eee3b6116700d5c8":
        raise ValueError("Assembled BIOS differs from the reviewed overlay")
    print(f"Experimental mGBA BIOS assembled: {out / 'hle-bios.bin'}")


if __name__ == "__main__":
    main()
