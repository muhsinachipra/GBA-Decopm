"""Compare strict-static checkpoints against an independent mGBA capture."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_state(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        result[key] = value
    return result


def pixel_data(path: Path) -> tuple[tuple[int, int], bytes]:
    with Image.open(path) as image:
        converted = image.convert("RGBA")
        return converted.size, converted.tobytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native", type=Path, help="strict-static capture directory")
    parser.add_argument("oracle", type=Path, help="mGBA Lua capture directory")
    args = parser.parse_args()

    native = json.loads((args.native / "capture.json").read_text(encoding="utf-8"))
    oracle = read_state(args.oracle / "state.txt")
    if native.get("backend") != "strict-static":
        parser.error("The first directory must contain a strict-static capture")

    expected_schedule = [(native["run"]["frames"], 0)]
    expected_schedule.extend(
        (segment["run"]["frames"], 0x3FF ^ segment["keyinput"])
        for segment in native["segments"]
    )
    schedule = [
        (int(frames), int(mask, 16))
        for frames, mask in re.findall(r"(\d+):0x([0-9A-Fa-f]+)", oracle["schedule"])
    ]
    schedule_match = schedule == expected_schedule

    native_iwram = sha256(args.native / "iwram.bin")
    native_ewram = sha256(args.native / "ewram.bin")
    oracle_iwram = sha256(args.oracle / "iwram.bin")
    oracle_ewram = sha256(args.oracle / "ewram.bin")

    native_size, native_pixels = pixel_data(args.native / "frame.png")
    oracle_size, oracle_pixels = pixel_data(args.oracle / "frame.png")
    dimensions_match = native_size == oracle_size
    pixels_match = dimensions_match and native_pixels == oracle_pixels
    pixel_mismatches = None
    if dimensions_match:
        pixel_mismatches = sum(
            native_pixels[i:i + 4] != oracle_pixels[i:i + 4]
            for i in range(0, len(native_pixels), 4)
        )

    native_ppu = native["ppu_state"]
    oracle_ppu = {key: int(value) for key, value in oracle.items() if key in native_ppu}
    ppu_fields = set(native_ppu) & set(oracle_ppu) - {"frame"}
    ppu_matches = {key: native_ppu[key] == oracle_ppu[key] for key in sorted(ppu_fields)}

    register_fields = [f"r{i}" for i in range(15)]
    register_matches = {
        key: native["registers"][key] == (int(oracle[key]) & 0xFFFFFFFF)
        for key in register_fields
    }

    alignment_frames = int(oracle.get("alignment_frames", "0"))
    match = {
        "rom_identity": oracle.get("rom_code", "").endswith("A9RE") and int(oracle["rom_size"]) == 0x400000,
        "schedule": schedule_match,
        "frame_count": int(oracle["frames"]) == native["run"]["frames"] + sum(
            segment["run"]["frames"] for segment in native["segments"]
        ) + alignment_frames,
        "iwram": native_iwram == oracle_iwram,
        "ewram": native_ewram == oracle_ewram,
        "framebuffer": pixels_match,
        "ppu_registers": all(ppu_matches.values()),
        "cpu_r0_r14": all(register_matches.values()),
    }
    result = {
        "reference": "mGBA 0.10.5 (independent emulator)",
        "native_frame": native_ppu["frame"],
        "oracle_frames": int(oracle["frames"]),
        "alignment_frames": alignment_frames,
        "image_dimensions": {"native": native_size, "oracle": oracle_size},
        "framebuffer_pixel_mismatches": pixel_mismatches,
        "ppu_mismatches": sorted(key for key, value in ppu_matches.items() if not value),
        "cpu_mismatches": sorted(key for key, value in register_matches.items() if not value),
        "memory_sha256_match": {"iwram": native_iwram == oracle_iwram, "ewram": native_ewram == oracle_ewram},
        "match": match,
    }
    print(json.dumps(result, indent=2))
    if not all(match.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
