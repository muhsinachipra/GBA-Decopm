"""Compare private native/interpreter captures; emit only hashes and match results."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native", type=Path)
    parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    native = json.loads(args.native.read_text(encoding="utf-8"))
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    if native["backend"] != "strict-static" or reference["backend"] != "interpreter":
        parser.error("Expected strict-static and interpreter captures in that order")
    if native["bios_sha1"] != reference["bios_sha1"] or native["run"] != reference["run"] or native["segments"] != reference["segments"]:
        parser.error("Captures use different BIOS images or input/frame schedules")
    fields = ("framebuffer_sha256", "iwram_sha256", "ewram_sha256", "registers", "ppu_state")
    result = {field: native[field] == reference[field] for field in fields if field in native and field in reference}
    result["cycle_count"] = native["counters"]["cycles_elapsed"] == reference["counters"]["cycles_elapsed"]
    result["irq_count"] = native["counters"]["irq_entries"] == reference["counters"]["irq_entries"]
    print(json.dumps({"reference": "framework interpreter (not mGBA)",
                      "checkpoint_frame": native["ppu_state"]["frame"],
                      "match": result}, indent=2))
    if not all(result.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
