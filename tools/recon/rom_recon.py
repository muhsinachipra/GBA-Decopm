"""ROM reconnaissance for the Road Rash: Jailbreak (GBA) research project.

Usage:
    python tools/recon/rom_recon.py "Road Rash - Jailbreak (USA).gba" \
        --out docs/recon/rom_recon_report.md \
        --nointro-dat work/recon/dat/nointro-gba.dat
"""
import argparse
import array
import hashlib
import math
import os
import re
import zlib

GBATEK_LOGO_LEN = 156
FIXED_0xB2 = 0x96


def shannon_entropy(block):
    if not block:
        return 0.0
    counts = [0] * 256
    for b in block:
        counts[b] += 1
    n = len(block)
    ent = 0.0
    for c in counts:
        if c:
            p = c / n
            ent -= p * math.log2(p)
    return ent


def parse_header(data):
    info = {}
    info["size"] = len(data)
    entry = int.from_bytes(data[0x00:0x04], "little")
    info["entry_word"] = f"0x{entry:08X}"
    if ((entry >> 28) & 0x0F) == 0x0E and ((entry >> 25) & 0x07) == 0b101:
        off = entry & 0x00FFFFFF
        if off & 0x00800000:
            off -= 0x01000000
        info["entry_target"] = f"0x{(off << 2) + 8:08X}"
    else:
        info["entry_target"] = "(not a plain ARM B instruction)"
    info["logo_sha1"] = hashlib.sha1(data[0x04:0x04 + GBATEK_LOGO_LEN]).hexdigest()
    info["title"] = data[0xA0:0xAC].decode("ascii", "replace")
    info["game_code"] = data[0xAC:0xB0].decode("ascii", "replace")
    info["maker_code"] = data[0xB0:0xB2].decode("ascii", "replace")
    info["fixed_b2"] = f"0x{data[0xB2]:02X}"
    info["fixed_b2_ok"] = data[0xB2] == FIXED_0xB2
    info["version"] = f"0x{data[0xBC]:02X}"
    info["complement_stored"] = data[0xBD]
    info["complement_calc"] = (-sum(data[0xA0:0xBD]) - 0x19) & 0xFF
    info["complement_ok"] = info["complement_stored"] == info["complement_calc"]
    info["reserved_be"] = f"0x{int.from_bytes(data[0xBE:0xC0], 'little'):04X}"
    return info


def hash_summary(data):
    return {
        "crc32": format(zlib.crc32(data) & 0xFFFFFFFF, "08x"),
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def entropy_map(data, block_size):
    rows = []
    for off in range(0, len(data), block_size):
        block = data[off:off + block_size]
        rows.append((off, len(block), shannon_entropy(block)))
    return rows


def byte_census(data):
    total = len(data)
    zero = data.count(0x00)
    ff = data.count(0xFF)
    return zero, ff, total


def pattern_census(data):
    even = data[: len(data) // 2 * 2]
    w16 = array.array("H")
    w16.frombytes(even)
    thumb_push_lr = 0
    thumb_sub_sp = 0
    for w in w16:
        if (w & 0xFF00) == 0xB500:
            thumb_push_lr += 1
        elif (w & 0xFF80) == 0xB080:
            thumb_sub_sp += 1
    quad = data[: len(data) // 4 * 4]
    w32 = array.array("I")
    w32.frombytes(quad)
    arm_stmfd_sp = 0
    arm_b_bl = 0
    for w in w32:
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            arm_stmfd_sp += 1
        if ((w >> 25) & 0x07) == 0b101 and ((w >> 28) & 0x0F) in (0x0A, 0x0B, 0x0E):
            arm_b_bl += 1
    return {
        "thumb_push_lr": thumb_push_lr,
        "thumb_sub_sp": thumb_sub_sp,
        "arm_stmfd_sp_lr": arm_stmfd_sp,
        "arm_b_bl_words": arm_b_bl,
    }


STRONG_KEYWORDS = [
    "magicpockets",
    "gax",
    "jailbreak",
    "road rash",
    "roadrash",
]

CONTENT_KEYWORDS = [
    "pacific highway",
    "suburban dump",
    "surviv",
    "cop",
    "wild",
    "mul-player",
    "multiplayer",
    "jailbreak",
    "wanted",
    "busted",
    "checkpoint",
]

MAX_LISTED_HITS = 200


def harvest_strings(data, min_len=4):
    return [(m.start(), m.group().decode("ascii")) for m in re.finditer(rb"[\x20-\x7E]{%d,}" % min_len, data)]


def filter_strings(strings, keywords):
    lowered = [(off, s, s.lower()) for off, s in strings]
    hits = []
    for off, s, ls in lowered:
        for kw in keywords:
            if kw in ls:
                hits.append((off, s, kw))
                break
    return hits


def nointro_check(dat_path, sha1):
    found = []
    with open(dat_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if sha1 in line.lower():
                found.append(line.strip())
    return found


def fmt_hex(off):
    return f"0x{off:06X}"


def build_report(rom_path, info, hashes, ent_rows, bytecensus, census, strong_hits, content_hits, all_strings, nointro_lines):
    lines = []
    lines.append("# ROM Recon Report")
    lines.append("")
    lines.append(f"- ROM: `{os.path.basename(rom_path)}`")
    lines.append(f"- Size: {info['size']} bytes")
    lines.append("")
    lines.append("## Hashes")
    lines.append("")
    lines.append("| Algorithm | Value |")
    lines.append("|---|---|")
    for k in ("crc32", "md5", "sha1", "sha256"):
        lines.append(f"| {k} | `{hashes[k]}` |")
    lines.append("")
    lines.append("## Header")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for k in ("title", "game_code", "maker_code", "version", "entry_word", "entry_target",
              "fixed_b2", "fixed_b2_ok", "complement_stored", "complement_calc", "complement_ok",
              "reserved_be", "logo_sha1"):
        val = info[k]
        if isinstance(val, int):
            val = f"0x{val:02X}"
        lines.append(f"| {k} | `{val}` |")
    lines.append("")
    lines.append("## No-Intro cross-check")
    lines.append("")
    if nointro_lines:
        lines.append("MATCH. SHA1 found in provided DAT:")
        lines.append("")
        for l in nointro_lines:
            lines.append(f"- `{l}`")
    else:
        lines.append("No DAT provided or SHA1 not found in provided DAT.")
    lines.append("")
    lines.append("## Entropy map (Shannon entropy per block, bits/byte)")
    lines.append("")
    lines.append("| Offset | Entropy |")
    lines.append("|---|---|")
    for off, _size, ent in ent_rows:
        bar = "#" * int(round(ent * 4))
        lines.append(f"| {fmt_hex(off)} | {ent:.3f} {bar} |")
    lines.append("")
    lines.append("## Byte census")
    lines.append("")
    zero, ff, total = bytecensus
    lines.append(f"- 0x00: {zero} ({zero / total * 100:.1f}%)")
    lines.append(f"- 0xFF: {ff} ({ff / total * 100:.1f}%)")
    lines.append("")
    lines.append("## Instruction-pattern census (heuristic)")
    lines.append("")
    lines.append("| Pattern | Count |")
    lines.append("|---|---|")
    for k in ("thumb_push_lr", "thumb_sub_sp", "arm_stmfd_sp_lr", "arm_b_bl_words"):
        lines.append(f"| {k} | {census[k]} |")
    lines.append("")
    lines.append("## String harvest")
    lines.append("")
    lines.append(f"- ASCII strings (min 4 chars): {len(all_strings)}")
    lines.append(f"- Strong-keyword hits: {len(strong_hits)}")
    lines.append(f"- Content-keyword hits: {len(content_hits)}")
    lines.append("")
    lines.append("### Strong keyword hits")
    lines.append("")
    for off, s, kw in strong_hits:
        lines.append(f"- {fmt_hex(off)} [{kw}] `{s[:160]}`")
    lines.append("")
    lines.append("### Content keyword hits")
    lines.append("")
    for off, s, kw in content_hits[:MAX_LISTED_HITS]:
        lines.append(f"- {fmt_hex(off)} [{kw}] `{s[:160]}`")
    if len(content_hits) > MAX_LISTED_HITS:
        lines.append(f"- ... and {len(content_hits) - MAX_LISTED_HITS} more (see stdout counts)")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="ROM reconnaissance: header, checksums, hashes, entropy, patterns, strings.")
    ap.add_argument("rom", help="path to the .gba ROM (local, never committed)")
    ap.add_argument("--out", help="write markdown report to this path")
    ap.add_argument("--block", type=int, default=65536, help="entropy block size (default 65536)")
    ap.add_argument("--min-string", type=int, default=4, help="minimum ASCII string length")
    ap.add_argument("--nointro-dat", help="path to a No-Intro .dat file to cross-check the SHA1")
    ap.add_argument("--quiet", action="store_true", help="do not print a summary to stdout")
    args = ap.parse_args()

    with open(args.rom, "rb") as fh:
        data = fh.read()

    info = parse_header(data)
    hashes = hash_summary(data)
    ent_rows = entropy_map(data, args.block)
    bytecensus = byte_census(data)
    census = pattern_census(data)
    strings = harvest_strings(data, args.min_string)
    strong_hits = filter_strings(strings, STRONG_KEYWORDS)
    content_hits = filter_strings(strings, CONTENT_KEYWORDS)
    nointro_lines = nointro_check(args.nointro_dat, hashes["sha1"]) if args.nointro_dat else []

    report = build_report(args.rom, info, hashes, ent_rows, bytecensus, census, strong_hits, content_hits, strings, nointro_lines)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report + "\n")
    if not args.quiet:
        print(f"ROM: {args.rom}")
        print(f"size={info['size']} sha1={hashes['sha1']}")
        print(f"title={info['title']!r} game_code={info['game_code']!r} "
              f"complement_ok={info['complement_ok']} reserved_0xBE={info['reserved_be']}")
        print(f"patterns: {census}")
        print(f"strings>={args.min_string}: {len(strings)}; strong hits: {len(strong_hits)}; content hits: {len(content_hits)}")
        if nointro_lines:
            print(f"no-intro: MATCH ({nointro_lines[0][:120]})")
        elif args.nointro_dat:
            print("no-intro: SHA1 NOT FOUND in provided DAT")
        if args.out:
            print(f"report: {args.out}")


if __name__ == "__main__":
    main()
