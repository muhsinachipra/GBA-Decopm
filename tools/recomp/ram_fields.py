"""Emit native operations for reviewed mutable ARM operand fields, with opcode guards.

This changes scalar operands of AOT operations, never interprets an instruction.
Unexpected mutations abort. The source opcode comes only from the private ROM.
"""
import json
import re


def transform(block, pc, source_word, field):
    suffix = f"{pc:08X}"
    if field == "lsr_immediate":
        if source_word & 0x02000010 or (source_word >> 5) & 3 != 1:
            raise ValueError(f"Not an ARM immediate LSR at 0x{pc:08X}")
        pattern = rf"(_op2_{suffix} = _rm_{suffix}) >> [0-9]+;"
        replacement = (f"uint32_t _opcode_{suffix} = bus_read_u32(0x{pc:08X}u);\n"
                       f"    if ((_opcode_{suffix} & ~0x00000F80u) != 0x{source_word & ~0xF80:08X}u) "
                       f"runtime_unimplemented_op(\"unreviewed RAM mutation\", 0x{pc:08X}u);\n"
                       f"    uint32_t _shift_{suffix} = (_opcode_{suffix} >> 7) & 31u;\n"
                       f"    _op2_{suffix} = _shift_{suffix} ? (_rm_{suffix} >> _shift_{suffix}) : 0u;")
        block, count = re.subn(pattern, lambda _: replacement, block)
        if count != 1:
            raise ValueError(f"Expected one native LSR operation at 0x{pc:08X}; found {count}")
        pattern = rf"_co_{suffix} = \(_rm_{suffix} >> [0-9]+\) & 1u;"
        block, count = re.subn(pattern,
            f"_co_{suffix} = (_rm_{suffix} >> (_shift_{suffix} ? _shift_{suffix} - 1u : 31u)) & 1u;", block)
        if count != 1:
            raise ValueError(f"Expected one shifter carry operation at 0x{pc:08X}")
    elif field == "condition":
        if (source_word >> 28) not in (4, 5) or (source_word >> 24) & 15 != 11:
            raise ValueError(f"Not a reviewed ARM BL MI/PL at 0x{pc:08X}")
        pattern = r"if \(arm_cond_passes\(0x[45]u\)\)"
        guard = (f"uint32_t _opcode_{suffix} = bus_read_u32(0x{pc:08X}u);\n"
                 f"    if ((_opcode_{suffix} & 0x0FFFFFFFu) != 0x{source_word & 0x0FFFFFFF:08X}u || "
                 f"((_opcode_{suffix} >> 28) != 4u && (_opcode_{suffix} >> 28) != 5u)) "
                 f"runtime_unimplemented_op(\"unreviewed RAM mutation\", 0x{pc:08X}u);\n"
                 f"    if (arm_cond_passes(_opcode_{suffix} >> 28))")
        block, count = re.subn(pattern, lambda _: guard, block)
        if count != 1:
            raise ValueError(f"Expected one condition guard at 0x{pc:08X}; found {count}")
    else:
        raise ValueError(f"Unknown mutable field: {field}")
    return block


def apply(generated, rom, metadata):
    for site in json.loads(metadata.read_text(encoding="utf-8")):
        pc, source = int(site["pc"], 0), int(site["source"], 0) - 0x08000000
        if not 0x02000000 <= pc < 0x02040000 or not 0 <= source <= len(rom)-4:
            raise ValueError("Mutable field is outside the reviewed EWRAM/ROM regions")
        pattern = re.compile(rf"(    /\* {pc:08X}  .*?)(?=    /\* [0-9A-F]{{8}}  |\Z)", re.DOTALL)
        found = 0
        for path in generated.glob("recompiled_*.cpp"):
            content = path.read_text(encoding="utf-8")
            match = pattern.search(content)
            if match:
                source_word = int.from_bytes(rom[source:source+4], "little")
                content = content[:match.start()] + transform(match[0], pc, source_word, site["field"]) + content[match.end():]
                path.write_text(content, encoding="utf-8")
                found += 1
        if found != 1:
            raise ValueError(f"Mutable site {site['pc']} has {found} generated owners; expected one")
