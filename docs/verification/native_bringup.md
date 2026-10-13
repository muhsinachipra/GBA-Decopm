# Native bring-up checkpoint — 2026-10-13

The Windows host builds locally and executes boot, title, main menu, Wild Race
introduction, player selection, and first-course selection with strict static
dispatch. **A full race and the v1.0 acceptance criteria remain unverified.**

## Verified evidence

The ROM SHA1 and SHA256 matched PROJECT_CONTEXT.md §1.1 before work.
The release CLI's default entry, `0x080000C0`, found one undefined function.
The cartridge header actually branches to `0x080000C8`; selecting that entry
found 3,747 candidate functions and produced a compiled static library.

The host uses framework commit `5e89943528aee7bc1c399bdbd035364a4b41dd10`.
Its latest analysis found **3,873 candidate functions: 173 ARM and 3,700 Thumb**,
with ten undefined-instruction findings still requiring review. These are
analyzer counts, not a complete function inventory or global coverage claim.

`GBARECOMP_STRICT_STATIC=1` disabled interpreter bridging, overlay compilation,
and healing-cache loading in the verified native runs. The successful probes
reported zero dispatch misses and zero interpreted fallback instructions.

| Scripted frame count | Observed scene | Internal comparison |
|---|---|---|
| 120 | Licensing screen | Framebuffer, IWRAM, CPU registers, PPU state and cycles match |
| 600 | Title screen during fade | Framebuffer, IWRAM, EWRAM, CPU registers, PPU state, cycles and IRQ count match |
| 932 | Main menu after Start | Same complete checkpoint comparison passes |
| 1,238 | Wild Race course selection | Same complete checkpoint comparison passes |

The comparison reference here is **the framework's interpreter**, using the
same hardware runtime and experimental BIOS backend. This establishes CPU
translation agreement at those checkpoints. It is **not independent mGBA
differential verification**, and does not qualify PPU/audio fidelity.
The debug server's final frame index is one less than the requested count.

Selected framebuffer SHA256 evidence:

| Checkpoint | SHA256 |
|---|---|
| 120 | `9a950f8a1085420a2d98d5f4d9013c7202d6550692d87f22e22b17b039d363e6` |
| 600 | `9d13f4f9c406e723366dc5ae593b4b340560a94cae4aec3533b0ee8d0bd6428a` |
| 932 | `372359d3276e59588b31e4d6e8ef274482abefdbd49c5370cdca101cb3fb7029` |

A bounded SDL window run presented 120 frames in 2.011117 seconds
(59.668 presented frames/second), with zero unmapped bus accesses and zero
unhandled IO accesses. This verifies window bring-up, not a race performance gate.

## RAM-installed code

Six reviewed ROM-backed copy spans are recorded in `native/analysis.toml`.
Additional observed entries are hand-authored there; generated maps stay private.
`tools/recomp/map_iwram.py` locates a unique 32-byte RAM anchor in the exact ROM,
extends the identical span, and emits address/size/hash metadata for review.
Maximal identical spans can include coincidental adjacent bytes, so their
boundaries were checked against disassembly before selecting copy sizes.

The relocated audio block at `0x020010F4` changes four immediate LSR fields
and four branch conditions. `native/mutable_sites.json` identifies the reviewed
sites. `tools/recomp/ram_fields.py` emits native arithmetic/control flow that
reads those fields and rejects unexpected opcode changes; it does not decode
or interpret instructions at runtime. Compiled synthetic checks exercise all
32 immediate LSR encodings, both reviewed branch conditions, and mutation guards.

## BIOS and oracle limitations

No retail BIOS was supplied in the local workspace. Bring-up used the
open-source mGBA 0.10.5 assembly shim, built locally with runtime SWI HLE.
Its source SHA256 is
`0f626f49cb2f0cef95c30cd7a3bbf8fd698085d15a3361a2bc6b9ac10030f062`;
the assembled 16 KiB image SHA1 is
`73528a5d6ea2c163e82956b1eee3b6116700d5c8`.
This shim leaves BIOS functionality incomplete; HLE timing and unimplemented
services require further verification. It is an experimental bring-up backend.
The BIOS image and its translated source remain ignored and local.

`tools/mgba/gdb_probe.py` is a scaffold. Headless SDL GDB startup timed out;
there was no successful port-2345 handshake. A separate ARM GCC/GDB package
installation also failed after network/DNS errors; no packages were upgraded.
ARM binutils were extracted from the downloaded MSYS2 package into ignored
`tools/bin/arm-tools/`. SDL2 2.32.10 was installed successfully.

## Reproduction and resume

From the repository root, with the pinned framework and tools installed:

```powershell
python tools/recomp/build_open_bios.py
python tools/recomp/build.py --bios work/open-bios/hle-bios.bin --bios-overlay tools/recomp/mgba-bios-analysis.toml
python tools/recomp/test_build.py
python tools/recomp/test_ram_fields.py
python tools/recomp/probe.py --bios work/open-bios/hle-bios.bin --scenario tools/recomp/scenarios/wild_course.json --output work/native/static-wild-course
python tools/recomp/probe.py --bios work/open-bios/hle-bios.bin --interp --scenario tools/recomp/scenarios/wild_course.json --output work/native/interp-wild-course
python tools/recomp/compare.py work/native/static-wild-course/capture.json work/native/interp-wild-course/capture.json
```

Local evidence: `work/native/*/capture.json`, screenshots and RAM snapshots.
The orchestration log is `work/native-bootstrap.log`, and build/generation logs are in `work/native/`.
The window log is `work/native/window120.log`. Never commit these snapshots,
screenshots, generated sources, executable, or runtime caches.

**Next coverage action:** rerun `wild_race.json` in strict mode. The previous
race-start attempt stopped at Thumb callback `0x083184FC`. Its function boundary
was reviewed, the seed was added, and the latest executable rebuilt successfully,
but that new race-start run has not yet been verified. An interpreter capture at
1,840 frames reached the Pacific Highway starting grid; this is not native-race evidence.

Then complete native race coverage, independent mGBA comparisons, save-chip
identification and round-trip, audio verification, other modes, and packaging.
