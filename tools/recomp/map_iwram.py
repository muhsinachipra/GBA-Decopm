"""Locate an observed RAM instruction span in the exact local ROM, without exporting bytes."""
import argparse
import hashlib
import json
from pathlib import Path

from build import ROOT, baseline, private_output, verify_rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ram", type=Path, required=True)
    parser.add_argument("--pc", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom_path = ROOT / "Road Rash - Jailbreak (USA).gba"
    verify_rom(rom_path, baseline((ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")))
    rom, ram = rom_path.read_bytes(), args.ram.read_bytes()
    base = 0x03000000 if len(ram) == 32768 else 0x02000000
    offset = args.pc - base
    if len(ram) not in (32768, 262144) or not 0 <= offset <= len(ram) - 32 or args.pc % 4:
        parser.error("Expected a full IWRAM/EWRAM capture and aligned ARM PC")
    anchor = ram[offset:offset + 32]
    source = rom.find(anchor)
    if source < 0 or rom.find(anchor, source + 1) >= 0:
        parser.error("Anchor has no unique ROM backing; further research required")
    low, high = offset, offset + 32
    while low > 0 and source + low - offset > 0 and ram[low-1] == rom[source+low-offset-1]:
        low -= 1
    while high < len(ram) and source + high - offset < len(rom) and ram[high] == rom[source+high-offset]:
        high += 1
    low = (low + 3) & ~3
    high &= ~3
    result = {"observed_pc": f"0x{args.pc:08X}",
              "runtime_start": f"0x{base+low:08X}",
              "source_start": f"0x{0x08000000+source+low-offset:08X}",
              "size": high-low, "ram_sha256": hashlib.sha256(ram).hexdigest(),
              "span_sha256": hashlib.sha256(ram[low:high]).hexdigest(),
              "status": "candidate: review execution mode and relocation before adding to analysis.toml"}
    output = private_output(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
