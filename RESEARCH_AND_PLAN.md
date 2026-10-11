# Road Rash: Jailbreak (GBA) — Research & Execution Plan

> **ROLE OF THIS DOCUMENT:** This file is the single source of truth and persistent context repository for this project. Any AI agent or human joining the project MUST read this file first, and MUST update its tracker sections before ending a work session. Treat it as append-only for history (Section 8) and in-place-updatable for status.
>
> **Canonical path:** `E:\Project\Decopm\RESEARCH_AND_PLAN.md`
> **Document version:** 0.1.0
> **Last updated:** 2026-10-11 (Session 001 — initial research)
> **Current phase:** P0 (Scaffolding & Baseline) — IN PROGRESS

---

## 0. How To Use This Document (Handoff Protocol for AI Agents)

1. **Read before acting.** Read Section 1 (identity), Section 3 (strategy/decisions), Section 4 (roadmap), and Section 8 (tracker + session log) before doing any work.
2. **Verify the baseline.** Recompute the ROM SHA1/SHA256 and compare against Section 1.1. If they differ, STOP and log the discrepancy in Section 8 before proceeding. All tooling, symbol maps, and patches in this project are hash-gated to this exact revision.
3. **Update statuses in place** in Section 4 (roadmap checkboxes) and Section 8.2 (tracker table). Never silently change scope; record scope changes as new decisions in Section 8.3.
4. **Append to the Session Log (8.6)** at the end of every session: date, agent/session id, what was done, evidence (paths, hashes, diffs, logs), blockers, next actions. Never delete or rewrite prior entries; corrections go in a new entry referencing the old one.
5. **Status codes:** `[ ]` TODO · `[~]` IN PROGRESS · `[!]` BLOCKED · `[x]` DONE (works, verified) · `[-]` DROPPED (reason logged) · `[?]` NEEDS INVESTIGATION.
6. **Evidence rule:** A task may only be marked `[x]` with evidence: a command + observed output, a file path, a hash, a screenshot, a diff, or a cross-referenced log. "It should work" is not evidence.
7. **Legal rule (hard):** never commit the ROM, BIOS, extracted copyrighted assets, or generated ROM-derived code (recompiled C/C++) to any repository intended for distribution. See Section 2.9.
8. **If you are an agent with limited context:** the minimum viable context is Section 1.1 (baseline), Section 3 (decisions), Section 8.6 (latest session entries), Section 8.7 (next actions).

---

## 1. Project Overview

### 1.1 Target ROM — Baseline Identity (hash gate)

| Property | Value |
|---|---|
| File (working name) | `Road Rash - Jailbreak (USA).gba` |
| Path in repo | `E:\Project\Decopm\Road Rash - Jailbreak (USA).gba` |
| Size | 4,194,304 bytes (4 MiB / 32 Mbit) |
| Internal title (0xA0) | `ROADRASHJAIL` |
| Game code (0xAC) | `A9RE` |
| Maker code (0xB0) | `20` (ASCII "20") |
| Version (0xBC) | `0x00` |
| Complement check (0xBD) | `0x6A` — **verified OK** (recomputed `0x6A`) |
| Header checksum (0xBE) | `0x00` — **unusual/zero; dump authenticity should be cross-checked** (Task P0-05) |
| SHA1 | `48150529172ff411e3e1bd38b9a74d8b32e5fa59` |
| SHA256 | `f0af99188e7ffaf0b0ea95e1503365a7eaf2eac6c9bc01c18c0f5c5ed010d4b6` |
| Developer (GBA version) | Magic Pockets (France), per engine string and public credits |
| Publisher | Electronic Arts |
| Release | 2003 (US: 2003-09-11) |
| Genre | Combat motorcycle racer ("Road Rash" series, 6th entry) |

### 1.2 Project Goal

**Primary goal:** native execution of this exact ROM's game logic on modern PCs (Windows first), via **static recompilation** of ARM/Thumb machine code to C/C++, running against a re-implemented GBA hardware layer (PPU, audio, DMA, timers, IRQ, input, saves) — i.e., an *AOT-translated native port*, not an emulator.

**Secondary goal (support track):** incremental **matching decompilation** (source reconstruction that recompiles byte-identically) to provide human-readable symbols, type information, and modding capability; decompiled symbols are imported into the recompilation build (same pattern used by the Mario Kart: Super Circuit recomp with the `mksc` decomp).

**Definition of Done (v1.0):**
- Boots and plays through all single-player modes (Wild Race, Jailbreak/modes per manual) at full speed with correct rendering and audio.
- Save persistence (correct save chip emulation for the cartridge's actual save type).
- Automated differential verification vs mGBA oracle (Section 6) for at least: boot→title, menus, one full race, one save round-trip.
- No copyrighted Nintendo/EA content distributed with the build; player supplies ROM (and BIOS, per chosen runtime).

**Stretch goals:** link-cable/2P, widescreen, 60 FPS render smoothing, full-matching decomp milestones, mod package support.

### 1.3 Repository Context

- Working directory `E:\Project\Decopm` currently contains only the ROM. It is **not yet a git repository** (verified 2026-10-11).
- Host environment: Windows (win32), default shell PowerShell 7 (`pwsh`). Python 3.13.7 and Git 2.51.0 available. WSL status unverified (Task P0-02).
- Research tooling state: none installed yet (Ghidra, mGBA, devkitARM, recompilers all pending).

---

## 2. Research Findings

### 2.1 Methodology Landscape — Three Viable Paths

| Path | What it produces | Effort to first playable | Effort to complete | Fidelity | Moddability | Community tooling maturity |
|---|---|---|---|---|---|---|
| **A. Static recompilation (AOT translation)** | Native C/C++ generated from the ARM7TDMI binary + hardware runtime | Weeks (per existing frameworks) | Months (hardware edge cases) | Must be validated vs emulator; high achievable | Medium (generated code + symbol overlays) | Young but rapidly advancing; 3 independent GBA frameworks exist |
| **B. Matching decompilation → source port** | Reconstructed C source that rebuilds the ROM byte-identically, then a platform layer port | Years for a 4 MiB commercial game | Years | Highest (bit-exact logic) | Highest | Mature methodology (pret/zeldaret), but per-game manual effort is enormous |
| **C. Emulation (baseline/comparison only)** | mGBA/NO$GBA run the ROM | Immediate | Immediate | Reference | None | Very mature — used as the **oracle** for A and B |

**Strategic conclusion:** Pursue **A as the primary track** (fastest route to native execution and directly addresses the user's goal), with **B as an incremental support track** (start with high-value symbol regions, no obligation to reach 100%), and **C as the verification oracle** (mGBA) and as an asset-extraction engine. This is the same pattern used by the most successful console ports: recompilation for breadth, decompilation for depth.

### 2.2 The GBA Platform Model (Porting Surface)

Source: GBATEK (No$GBA technical reference, `problemkaputt.de/gbatek.htm`), fetched 2026-10-11.

**CPU / memory**
- ARM7TDMI @ 16.78 MHz, ARMv4T: 32-bit ARM **and** 16-bit Thumb instruction sets, interworking via `BX`/`BLX`; little-endian only; no MMU, no cache (but waitstates).
- Memory map (addresses the recompiled code will still address):
  - `0x00000000` BIOS 16 KiB (SWIs: CpuSet/CpuFastSet, Div/Sqrt/ArcTan, LZ77/RLE/Huffman decompression, Halt/IntrWait, BgAffineSet/ObjAffineSet, SoftReset).
  - `0x02000000` EWRAM 256 KiB (slow, 16-bit bus).
  - `0x03000000` IWRAM 32 KiB (fast, 32-bit bus; default IRQ stack at `0x03007F00`).
  - `0x04000000` I/O registers (~`0x400` bytes used).
  - `0x05000000` palette RAM (1 KiB, BGR555), `0x06000000` VRAM 96 KiB, `0x07000000` OAM 1 KiB.
  - `0x08000000-0x0DFFFFFF` ROM mirrors (waitstate 0/1/2), `0x0E000000` cartridge SRAM/Flash window (8-bit bus).
- ROM executes Thumb at full speed; ARM from ROM is 32-bit-fetch-limited, so real games copy hot ARM code to IWRAM (important for recompilation: **RAM-resident code**).

**Video (PPU)**
- 240×160, 60 fps; modes 0–5 (tile: 0/1/2; bitmap: 3/4/5); 4 BG layers, 128 OBJ sprites; affine rotation/scale; windows 0/1/OBJ; mosaic; alpha blending + brightness fade; 15-bit BGR555 color.
- Per-scanline effects driven by HBlank/VCount IRQs (raster effects) — requires a scheduler faithful to scanline timing in the runtime.

**DMA / timers / IRQ**
- 4 DMA channels (immediate, VBlank, HBlank, and "special" modes e.g. sound FIFO, and DMA3→ROM in some hardware).
- 4× 16-bit timers with cascading; IRQ controller (IE/IF/IME), VBlank/HBlank/VCount/Timer/Serial/Keypad/DMA sources.

**Sound**
- 2× DirectSound 8-bit PCM channels fed by 32-byte FIFO (Timer/DMA driven) + 4 legacy PSG channels (2 square, wave, noise), stereo volume/mixing registers.

**Input / serial / saves**
- KEYINPUT/KEYCNT; serial port for link cable (may be unused → confirm).
- Cartridge save chips: SRAM / Flash (512 Kib–1 Mib) / EEPROM (512 bit–8 Kib), accessed through `0x0E000000` with chip-specific protocols (laqieer has a battle-tested library, `libsavgba`). Save type for this ROM is **unknown → Task P2-06**.

**Implication for native port:** The recompiled game keeps the GBA memory map; the runtime must model the PPU, DMA, timers, IRQ timing, audio chain, input, and save chip. This is exactly what the three GBA static-recompiler projects provide (Section 2.4).

### 2.3 Matching Decompilation Toolkit & Workflow (State of the Art)

The pret/zeldaret model (verified from `pret/pokeemerald` INSTALL.md, `pret/agbcc`, `zeldaret/tmc`, `jellees/mksc`, 2026-10-11):

**Core loop:** split the ROM into code/data units → disassemble/translate → write C that compiles to the *exact* original object code → link all units into a ROM that matches the original SHA1 (`make compare` → `OK`). Progress = % of bytes/functions matched, tracked per unit.

**Toolchain**
- **Compiler:** `pret/agbcc` — a fork of GCC 2.95 used by most GBA decomp projects (build with `./build.sh`, install with `./install.sh ../PROJECT`). Some projects allow `make modern` with `arm-none-eabi-gcc` (devkitARM) for non-matching builds and `DINFO=1` debug ELFs.
- **Assemblers/binutils:** `arm-none-eabi-as`/`objdump` (binutils-arm-none-eabi); pret uses GNU as syntax + custom preprocessing (`preproc`) for split asm data.
- **Asset/data tools (per project):** `gbagfx` (tiles/palettes), `preproc` (extract data from asm), `ramscrgen`, `scaninc`, plus project-specific generators. zeldaret/tmc additionally has `progress.py`, `calcrom.pl`, `asmdiff.sh`, Jenkins CI.
- **Match verification:** `asm-differ` (simonlindholm) and now **objdiff** (`encounter/objdiff`) — compares built `.o` vs target `.o`, supports **ARM (GBA, DS, 3DS)**, powered progress reporting on **decomp.dev**; GUI, CLI, VS Code extension.
- **C generation assistance:** **m2c** (`matt-kempster/m2c`) supports target `gba` = "ARM (with APCS, little endian)"; context files for structs/prototypes; output flows into the permuter.
- **Matching brute-force:** **decomp-permuter** (`simonlindholm/decomp-permuter`) randomizes C (variable introduction, type changes, statement layout) against a compile-and-diff scorer; ARM32 supported; `permuter@home` distributed mode. Laqieer maintains **decomp-permuter-arm**, and an import path for ninja/make projects via `import.py`.
- **Build/build-system precedent:** pret projects are Makefile-based, ROM-hash pinned (`rom.sha1`), with CI. tmc uses Jenkins. objdiff can consume the build via `objdiff.json`.

**Realistic scope note:** Full matching decompilation of a commercial 4 MiB game is a multi-year, multi-person effort (e.g., tmc is years in and still WIP; MKSC required a dedicated decomp team). Therefore Track B must be **opportunistic** in this project: decompile the parts that pay off (symbols, game-state machine, physics, menus), import them as named symbols, and measure via objdiff/decomp.dev-style metrics.

### 2.4 GBA Static Recompilation Frameworks (Primary Enablers)

Three independent frameworks exist (all verified 2026-10-11). They translate ARM7TDMI ARM/Thumb → C/C++ ahead of time and link against a hardware runtime. None ships ROM data; all are ROM-hash gated.

#### 2.4.1 `mstan/gbarecomp` (GBARecomp) — most feature-complete (PRIMARY CANDIDATE)
- **Pipeline:** analyzer discovers code, follows control flow, tracks ARM/Thumb interworking, resolves direct and indirect dispatch → emitter produces sharded C++ → normal C++ compiler builds against shared runtime → runtime keeps an **interpreter / self-healing tier** for code that cannot be resolved statically (and a persistent "healing cache").
- **Runtime models:** PPU (selectable **HLE or LLE scanline renderer**, `GBARECOMP_SCANLINE_IMPLEMENTATION=HLE|LLE`), audio, DMA (LLE for ordinary-RAM DMA by default; HLE-DMA doc), timers, IRQ, saves (SRAM/EEPROM/Flash/Flash1M), GPIO devices, input; host RTC; RTC cartridges detected by SDK signature.
- **Product features already proven across titles:** adaptive widescreen (validated on multiple games), 60 FPS mods, `.gbamod` versioned mod packages, save states, link-cable + Wireless Adapter netplay with rollback, Android target, Emscripten/web target, per-game cartoon cover launcher.
- **Public game integrations** (evidence of framework generality): Minish Cap, Mega Man Zero, Super Mario Advance 2/4, Mario Kart: Super Circuit, DBZ Legacy of Goku I/II/Buu's Fury, Pokémon FRLG/RSE, WarioWare Twisted (gyro), Shrek GBA Video (64 MiB Mapper).
- **CLI usage:** `gbarecomp.exe build --rom "C:\Games\MyGame.gba" --output "C:\Projects\MyGameRecomp"` → generates sharded C++, runtime headers, CMake + `build.ps1`; `build.ps1` produces `build\Release\gbarecomp_game.lib`. Playable integration needs verified coverage + host app + cartridge config + validation; game repos serve as references (`docs/WINDOWS_GAME_SETUP.md`).
- **Strict mode:** `GBARECOMP_STRICT_STATIC=1` fails loudly on the first missing static PC instead of loading/creating a healing shard — ideal for coverage burn-down.
- **BIOS handling:** recompiles a user-supplied BIOS (`bios/gba_bios.toml`); no BIOS is needed to generate source. **No ROM/BIOS distributed.**
- **Why primary:** deepest hardware model, per-title validation tooling (coverage, differential, widescreen), Windows-native CLI + PowerShell build path (matches host), and a symbol-import pathway (`tools/symbol_import/import_decomp_symbols.py`, used with `jellees/mksc` in the MKSC project) that fits our Track B.

#### 2.4.2 `JRickey/gba-recomp` — Rust, zero-interpreter ambition (RESEARCH REFERENCE)
- **Design:** analyze → emit **C11** → compile → link (`recomp-core`); indirect branches resolved at runtime via mode-aware guest→native function table; RAM-resident code captured by a build-time interpreter profile and translated from a runtime snapshot; per-block cycle sums computed at recompile time with an event scheduler (cycle-count accuracy); MMIO accesses as catch-up sync points.
- **Function-boundary database:** `gamedb.sqlite` (CC0), keyed by ROM SHA-256; AI-assisted full mapping of every game in progress (as of its README: 169,778 functions mapped in 4 days; "one game fully mapped"). **Unlikely to contain our title → would require mapping ourselves.**
- **Features:** enhanced audio path (band-limited resampling), **shadow mixers for embedded audio middleware including the "GAX lineage"** (relevant! our ROM uses GAX 3.03A), screen simulation (panel color models, temporal response, pixel grid via wgpu), launcher, `gba-pack` standalone executables, netplay (WIP). Requires user BIOS for the launcher.
- **Commands:** `cargo build --release`; `./target/release/recomp play path/to/your.gba`.
- **Why reference:** its documented solutions to the exact hard problems we will hit (RAM code, cycle accuracy, GAX audio, function maps) are directly transferable knowledge, even if we use mstan's framework.

#### 2.4.3 `sp00nznet/gbarecomp` — minimal, conformance-first (FALLBACK CANDIDATE)
- **Design:** C toolkit; `translate` emits a CMake project that builds against a small GBA runtime with SDL2; **no BIOS image needed — BIOS calls are reimplemented in `src/runtime.c`** (simplifies distribution).
- **Validation methodology:** lockstep **conformance harness** against mGBA (`docs/conformance.md`): each recompiled function's calls run natively and in an interpreter from the same state and are compared; headless flags `--headless --frames N --screenshot --record --input --log-every --dump-at`, plus `GBA_VALIDATE`, `GBA_FUNC_TRACE`, `GBA_TRACE_INTERP`.
- **CLI:** `gbarecomp info|disasm|analyze|translate <rom.gba>`; `translate -o out --multi --entries entries.txt` (extra entry points, one hex address per line); analyzer finds jump tables, code pointers in ROM data, prologue-less leaf functions (docs/analysis.md).
- **Status:** alpha; one title in progress (Advance Wars, 165/165 functions conformant); **missing audio output, mosaic, RAM overlay recompilation** (Roadmap).
- **Why fallback:** simplest stack (no BIOS, no interpreter needed for distribution), excellent verification discipline; but younger and lacks audio, which we need (GAX).

#### 2.4.4 Lineage & Ecosystem
- The GBA recompilers follow the **N64Recomp** pattern (MIPS→C + N64ModernRuntime + RT64 renderer) that produced Zelda 64 Recompiled; analogous projects now exist for Xbox 360 (XenonRecomp/ReXGlue), PS2 (PS2Recomp), PS1 (mstan/psxrecomp; note mstan's psxrecomp "lifts R3000A MIPS to native C and recompiles the SCPH1001 BIOS itself as the kernel" — same BIOS-as-code philosophy as GBARecomp's BIOS recompilation).
- **Recompendium** (nio03.github.io/unricopie) catalogs 129 recomps / 44 ports / 126 decompilations / 33 tools (snapshot 2026-10): GBA entries include Minish Cap ports (Project Picori `999sian/tmc` PC port; 3DS port from `zeldaret/tmc`), and the MKSC recomp (`mstan/MarioKartSuperCircuitRecomp`) that consumes the `jellees/mksc` decomp for symbol names — **the exact Track A+B integration pattern we intend to replicate**.

### 2.5 Binary Analysis Tooling (Static + Dynamic)

**Static analysis**
- **Ghidra + GBA loader** (recommended, free): `SiD3W4y/GhidraGBA` loader defines GBA memory regions/peripherals (`gradle` build with `GHIDRA_INSTALL_DIR`; install zip via File→Install Extensions). Alternatives: `pudii/gba-ghidra-loader`; `RetroReversing/GhidraRetroReversing` ships precompiled loaders for Ghidra 11.1.2 / Java 21 (NES/GB/GBA/DS/PSP/PS1/PS2/SMS/MD/Dreamcast).
- **Ghidra debugging (dynamic-static fusion):** Ghidra's debugger can attach to mGBA's GDB stub (wrongbaud tutorial, 2020): in mGBA `Tools → Start GDB Server` (port 2345); in Ghidra debugger use an "IN-VM GNU gdb" launcher; effective gdb settings: `set architecture arm`, `set arm fallback-mode thumb`, `set arm force-mode thumb`, `target remote localhost:2345`; breakpoints, memory/register inspection work (gdb-multiarch noted as occasionally missing breakpoints — use `stepi` fallback; devkitARM gdb reported misbehaving with Ghidra registers).
- **IDA / radare2 / RetDec support:** Laqieer's GBA RE suite: `ida_gba_stuff` (loaders, plugins, scripts, configs, library signatures), **`gba_lib_func_sig`** — library function signatures of common GBA libraries for IDA/Radare2/RetDec/Ghidra (this is exactly how we identify SDK/middleware code fast), `gba-disasm-decomp-tools` (dockerized disasm/decomp CI), `IDABuddy`.
- **Decompilers for manual C recovery:** m2c (`--target gba`), Ghidra decompiler, IDA Hex-Rays (if licensed), RetDec.

**Dynamic analysis / tracing**
- **mGBA** is the workhorse: GDB stub (port 2345), **Lua scripting** (memory read/write, event callbacks, screenshots; docs at `mgba.io/docs/scripting.html`), savestates, frame dumps, debugger views (tile/map/Sprite viewers), memory search. Recommended for: function tracing, MMIO watchpoints (who reads `KEYINPUT`, who writes `DISPCNT`), DMA/IRQ tracing, RAM code detection, save-chip protocol capture, and as the **differential oracle**.
- **NO$GBA** (GBATEK author's emulator) — strong debugger, widely used historically for GBA RE.
- **BizHawk** — Lua scripting + savestates, good for automated input replay.
- **Emulator as asset factory:** because a correct emulator executes the game's own decompressors, we can dump decompressed graphics/audio/levels from VRAM/RAM at runtime instead of reversing compression formats first (critical given our ROM's high-entropy regions, Section 2.7).

**Compiler identification (for Track B):** unknown yet. The game (2003, Magic Pockets) could be built with ARM SDT, Metrowerks CodeWarrior, or a GCC-2.9x-era toolchain. Fingerprinting method: compile a corpus of C snippets with candidate compilers, compare instruction-selection/register-allocation patterns against the ROM (m2c + objdiff make this measurable). Until identified, Track B targets **semantic** C (readable, not byte-matching), with objdiff measuring match scores opportunistically.

### 2.6 Non-Pokémon GBA Decompilation Precedents

| Project | Game | Notes / lessons |
|---|---|---|
| `zeldaret/tmc` | Zelda: Minish Cap (USA/JP/EU + 2 demos) | Large, active, multi-version; Makefile + Jenkins + `progress.py`; warns "some parts of the ROM may not be 'shiftable' yet"; ships no assets. Its SHA1s are authoritative ROM IDs. |
| `jellees/mksc` | Mario Kart: Super Circuit (US) | **Racer-genre precedent**; builds `sha1: 9d327c030c3e2d9007990518594f70c3340ac56f`; its symbol data feeds the MKSC recomp — model for our symbol overlay. |
| `pret/pokeemerald`, `pret/pokefirered` | Pokémon Gen 3 | Workflow tooling (agbcc, gbagfx, preproc, scaninc), `make compare`, Windows setup via WSL1/msys2/Cygwin; the reference for build-system conventions. |
| `FireEmblemUniverse/fireemblem8u` | Fire Emblem: Sacred Stones | Evidence that agbcc-style matching works across engines/genres (GBA strategy RPG). |
| `psxports/RoadRashJailbreak-xport` | Road Rash: Jailbreak **PSX** (different codebase!) | Early-stage decomp port of the PSX game (EA Redwood Shores code). Useful only as **design-level reference** (mode names, UI concepts); zero source compatibility with the GBA build. Do not confuse the two. |

### 2.7 Target-Specific Findings (Live Reconnaissance of This ROM)

Performed 2026-10-11 with an inline Python analysis (script kept outside the repo; methodology reproducible via Task P0-06):

- **Developer engine fingerprint:** ASCII string `* Engine by www.MagicPockets.com*` occurs 5×. Confirms the GBA game runs Magic Pockets' in-house engine.
- **Audio middleware identified:** `GAX Sound Engine 3.03A (Mar  5 2003)`, plus API strings `GAX2_INIT`, `GAX2_NEW`, `GAX2_NEW_FX`, `GAX_FX_REVERB`, `GAX_HALFRATE_FX`. => Audio porting must handle GAX 3.x (DirectSound-based software mixer); JRickey/gba-recomp documents GAX-lineage shadow-mixer work (Section 2.4.2).
- **Instruction mix (heuristic census):** ~4,478 Thumb `PUSH {lr}`-style prologue candidates vs ~33 ARM `STMFD sp!`-style — indicative of a **predominantly Thumb** codebase (typical for GBA; ARM blobs will exist in IWRAM, e.g. mixer/IRQ hot paths). Exact count requires proper disassembly (Task P1-04).
- **Entropy map (64 KiB blocks):** `0x000000–0x0FFFFF` ≈ 7.8–8.0 (high → **compressed blobs**, likely graphics/audio/levels); `0x100000–0x2EFFFF` ≈ 5.4–6.8 (mixed data/tables); `0x2F0000–0x3EFFFF` ≈ 6.1–7.6 (more data/code mix); final block at `0x3F0000` = 4.18 (padding/blank tail). Overall `0x00` bytes 9.8%, `0xFF` 1.6%. Conclusion: expect **custom compression** for a large fraction of the 4 MiB; do not plan around direct raw asset parsing.
- **String evidence of content:** level/mode names are recoverable from ASCII/relative-offset strings, e.g. `Pacific Highway`, `Suburban Dump`, `WILD`, `COP`, `TIME`, `SURVIVA[L]`, `MUL-PLAYER` — useful anchors for locating the level table and game-mode state machine (Tasks P2-04, P4-07).
- **No Nintendo SDK banner string found** (normal; SDK identity must be determined via function signatures, `gba_lib_func_sig`).
- **Save type:** still unknown (strings alone inconclusive); determine dynamically via mGBA watchpoints on `0x0E000000` reads/writes (Task P2-06).

### 2.8 Known Challenges & Risk Register Summary

| ID | Challenge | Why it matters here | Mitigation direction |
|---|---|---|---|
| C1 | **Code/data separation** | 4 MiB ROM; compressed data early; jump tables embedded | Analyzer + entries file + interpreter fallback; refine with mGBA execution traces; strict-static coverage burn-down (GBARecomp `GBARECOMP_STRICT_STATIC`) |
| C2 | **Indirect dispatch** | Virtual calls/function-pointer tables common in C++-era engines | Runtime guest→native dispatch table (mstan, JRickey); per-function entries; conformance harness |
| C3 | **IWRAM-resident code** | GAX mixer + IRQ handlers likely copied to IWRAM at boot | Build-time interpreter profile (JRickey), healing/interpreter tier (mstan), manual map once observed |
| C4 | **Custom compression** | ≥1 MiB high-entropy blobs | Dynamic dumping from emulator memory; BIOS SWI tracing; format RE only where needed |
| C5 | **Audio (GAX 3.03A)** | GAX is middleware with its own mixer semantics; 8-bit DirectSound fidelity | Baseline: hardware-level fidelity (FIFO + PSG). Enhancement: GAX shadow mixer (reference JRickey); verify by ear + null-tests vs mGBA audio |
| C6 | **Timing / raster effects** | Racer with per-scanline road effects; timing affects physics feel | Cycle-aware scheduler; frame-level differential vs mGBA; JRickey's per-block cycle budget approach as design reference |
| C7 | **Compiler/toolchain unknown (Track B)** | Blocks byte-matching C | Fingerprint compilers with objdiff; start semantic-only; agbcc likely candidate if GCC-era |
| C8 | **Scope: full decomp** | Multi-year effort | Opportunistic decompilation only; measure with objdiff, never block Track A |
| C9 | **Framework immaturity/churn** | The three recompilers are young, fast-moving | Pin revisions (submodules); ROM-hash gating; keep a per-tool "adoption log" (Section 8.3) |
| C10 | **Windows host friction** | Some decomp tooling assumes Unix/WSL; recompilers assume MSYS2/MinGW toolchains | WSL1/2 for make-based stacks (per pret INSTALL); MSYS2/VS2022 for gbarecomp builds; document exact commands |
| C11 | **Legal** | ROM-derived output must not be distributed | Hard rules in Section 2.9; hash-gated local builds only |
| C12 | **Dump authenticity** | Header checksum byte is `0x00` | Cross-check against No-Intro/redump hashes; if a better dump surfaces, re-baseline (Task P0-05) |

### 2.9 Legal & Distribution Constraints (Read Carefully)

- The ROM is copyrighted by Electronic Arts (publisher) and its developers. This project is a preservation/interoperability research effort; **do not distribute** the ROM, BIOS, extracted assets, or ROM-derived generated source.
- Static recompilers produce C/C++ **derived from the ROM** — treat all generated code, symbol maps derived by automated lifting, and dumped assets as **private build artifacts**. Keep them out of version control (`.gitignore`), out of release packages, and never publish them.
- Public releases, if any, should follow the prevalent pattern: a launcher/build tool that ingests the user's own legally obtained ROM locally and verifies it by hash; ship no game data and no derived code. (See mstan/gbarecomp & game repos' "Legal" sections; JRickey/gba-recomp's clean-room statements; sp00nznet/gbarecomp's "output never distributed".)
- Matching decompilation output (hand-written C reconstruction) is a different artifact class; still, keep the repository asset-free (no graphics, no audio, no ROM windows) exactly as pret/zeldaret projects do.
- Never extract or use leaked SDKs, leaked source, or confidential documents. Everything in this plan uses clean-room, publicly documented behavior (GBATEK, emulator sources as *fact references* only, published tooling).

---

## 3. Recommended Technical Strategy (Decision Record)

**Decisions made 2026-10-11 (Session 001):**

| ID | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D1 | Primary execution path = **static recompilation**, not full decomp-first | Only realistic route to a native, playable build for a 4 MiB commercial title without a multi-year team | Full matching decomp first (rejected: years to first playable); pure emulation (rejected: not "native execution") |
| D2 | Primary framework = **`mstan/gbarecomp`** | Most feature-complete GBA framework; Windows-native CLI; HLE/LLE PPU; strict-static coverage mode; proven across many commercial games; symbol-import path for decomp integration | `sp00nznet/gbarecomp` (kept as **fallback**; no BIOS needed but no audio yet); `JRickey/gba-recomp` (kept as **reference**; zero-interpreter ambition and GAX audio knowledge) |
| D3 | Verification = **differential vs mGBA oracle** (frame hashes, RAM diffs, savestate-based A/B, lockstep function conformance where available) | Proven methodology from sp00nznet/gbarecomp conformance harness; prevents silent drift | Manual playtesting only (rejected: insufficient) |
| D4 | Track B (decompilation) is **opportunistic and symbol-first** | Provides names/types for debugging and modding without blocking Track A; matches MKSC precedent (decomp symbols imported into recomp) | Wait for 100% decomp (rejected: years); no decomp at all (rejected: loses long-term moddability and semantic fidelity) |
| D5 | Audio strategy = **hardware-fidelity first** (DirectSound FIFO + PSG in runtime), **GAX-aware enhancements later**; never ship GAX code | Fidelity baseline is verifiable; GAX shadow-mixer knowledge exists in JRickey's project; middleware code cannot be shipped | Immediate HLE of GAX (rejected: unverifiable early); ignore audio (rejected: unacceptable) |
| D6 | Toolchain host = **native Windows for recompiler + Ghidra + mGBA; WSL for make-based decomp builds** | recompiler CLI ships Windows binaries; decomp toolchains (agbcc, pret-style makefiles) are Unix-oriented; pret INSTALL recommends WSL1/2 on Windows | All-WSL (rejected: complicates emulator/Ghidra integration); all-native (rejected: build friction) |
| D7 | Keep repo **not yet git-initialized until P0**; then commit only this document, tooling configs, scripts, and (later) hand-written decomp C — never ROM/BIOS/generated code | Clean baseline and legal hygiene | Commit everything (rejected: legal) |

**Target architecture (Track A):**

```
 ROM (hash-gated) ──► GBARecomp analyzer ──► generated C++ shards (private)
                          │                         │
                          │                         ▼
                          │               + shared GBA runtime (PPU/DMA/IRQ/audio/saves)
                          │                         │
                          ▼                         ▼
                 symbol overlay ◄──── Track B: matching decomp (agbcc/gcc) ──► objdiff/decomp.dev metrics
                 (names/types)          (hand-written C for selected subsystems)
                          │
                          ▼
              native host app (SDL2 window, input, save files, settings)
                          │
                          ▼
              differential verification vs mGBA (frames/RAM/audio)
```

---

## 4. Granular Execution Roadmap

> Status legend: `[ ]` TODO · `[~]` IN PROGRESS · `[!]` BLOCKED · `[x]` DONE · `[-]` DROPPED · `[?]` NEEDS INVESTIGATION. Keep this section in sync with Section 8.2.
> Task IDs are stable; add new tasks with the next free number in the phase. Never renumber.

### Phase P0 — Scaffolding & Baseline (current)
- [x] **P0-01** Baseline ROM identity recorded (SHA1/SHA256/size/header) — see §1.1. Evidence: hash + header dump, 2026-10-11.
- [x] **P0-02** Host capability inventory (Python 3.13.7, Git 2.51.0 present; working dir not a git repo; WSL status unverified). Evidence: `python --version`, `git --version`, `Get-ChildItem`.
- [~] **P0-03** Write and review this `RESEARCH_AND_PLAN.md` (Session 001 deliverable).
- [ ] **P0-04** `git init` in `E:\Project\Decopm`; add `.gitignore` that excludes: ROMs (`*.gba`, `*.gb`, `*.sav`), BIOS (`*.bin` except tool configs), `generated/`, `build/`, `work/`, `*.o`, Ghidra projects (`*.gpr`, `*.rep`), emulator states. Commit only: `RESEARCH_AND_PLAN.md`, `.gitignore`, `tools/` scripts, `docs/`.
- [ ] **P0-05** Verify dump authenticity: cross-check SHA1 against No-Intro/redump databases; investigate zero header checksum (0xBE). If a verified retail dump differs, re-baseline the entire document (§1.1) via a new session-log entry.
- [ ] **P0-06** Recreate the recon tool as a committed script `tools/recon/rom_recon.py` (header parse, checksum verify, strings harvest with keyword filter, entropy map, pattern census) and commit its *output report* (not the ROM) under `docs/recon/`.
- [ ] **P0-07** Legal checklist added to repo (`docs/legal.md`): no ROM/BIOS/assets/generated-code in VCS or releases; hash-gating policy.
- [ ] **P0-08** Install asset below (Section 5) and record exact versions in Section 8.4 (tools table).

### Phase P1 — Static Analysis & Map Building
- [ ] **P1-01** Install Ghidra (latest stable) + JDK 21; install a GBA loader (`SiD3W4y/GhidraGBA`, or `RetroReversing` precompiled for Ghidra 11.1.2). Evidence: import ROM, discover functions, screenshot of memory map.
- [ ] **P1-02** Apply `laqieer/gba_lib_func_sig` signatures (IDA/radare2/RetDec/Ghidra formats) to auto-name common library functions; record which libraries are detected (Nintendo SDK? libgcc? commercial middleware?).
- [ ] **P1-03** Produce the initial function inventory: count, address ranges, ARM/Thumb split, size histogram. Export as `docs/recon/ghidra_functions.csv` (address,name,mode,size) — this file is generated analysis (derived from ROM): keep local/uncommitted unless deemed safe; default **uncommitted**.
- [ ] **P1-04** Confirm ARM/Thumb distribution with proper disassembly (replace the heuristic census in §2.7). Identify ARM-only regions (expect IWRAM trampolines, IRQ, GAX).
- [ ] **P1-05** Map the code/data boundary: identify main entry (ROM header entry point), IRQ vector table (copied to `0x03007F00`), runtime library layout, and the engine's top-level dispatch.
- [ ] **P1-06** Data-format recon (static): confirm compression signatures in the high-entropy regions; check for BIOS LZ77/RLE/Huffman headers (first byte type + 24-bit length) at blob offsets; list candidate blob table.
- [ ] **P1-07** String cross-reference: anchor level names (`Pacific Highway`, `Suburban Dump`, …) to code/data via Ghidra xrefs; locate the level table and mode strings.

### Phase P2 — Dynamic Analysis & Function Coverage
- [ ] **P2-01** Install mGBA (latest); verify GDB stub (`Tools → Start GDB Server`, port 2345) with gdb-multiarch or devkitARM gdb: `set architecture arm`, `set arm fallback-mode thumb`, `target remote localhost:2345`.
- [ ] **P2-02** Build an mGBA **Lua trace suite** under `tools/mgba/`: (a) code-coverage logger (log PC ranges executed during scripted playthroughs); (b) MMIO write logger (DISPCNT/BLDCNT/DMA/IRQ/FIFO); (c) `0x0E000000` save-chip access logger; (d) IWRAM snapshot/diff to detect RAM-installed code at boot and at runtime.
- [ ] **P2-03** Scripted playthrough set (input macros → savestates): boot/title/idle, enter race, crash, menu, save, load. Store just the input scripts + savestate *hash* (not state files) in repo.
- [ ] **P2-04** Fuse coverage into a function map: annotate every Ghidra function as seen/not-seen; produce `entries.txt` (extra entry points for the recompiler) from indirect-dispatch targets observed dynamically.
- [ ] **P2-05** Identify the **GAX driver** memory footprint: locate IWRAM-resident GAX code, its song/instrument tables, and FIFO A/B feeding pattern; document in `docs/findings/audio_gax.md`.
- [ ] **P2-06** Determine the **save type** (EEPROM vs Flash vs SRAM) via `0x0E000000` access pattern; verify by saving in-game under mGBA and diffing the `.sav`.
- [ ] **P2-07** Capture decompressed asset dumps (from VRAM/palette/OAM/RAM at stable points) as *research references* under a local-only, uncommitted `work/assets/` folder.
- [ ] **P2-08** Confirm PPU feature set actually used: enumerate BG modes, affine usage, window/blend/mosaic usage across scenes (from MMIO logs). Output: `docs/findings/ppu_usage.md` — drives runtime work in P4.

### Phase P3 — First Native Bring-up (Track A)
- [ ] **P3-01** Install MSYS2/MinGW64 + CMake + Ninja + SDL2 (vcpkg or MSYS2 packages) per `gbarecomp` docs. Verify a hello-world CMake+SDL2 build.
- [ ] **P3-02** Download `gbarecomp-cli-windows-x86_64.zip` (mstan/gbarecomp release); pin its version in §8.4. Generate a project: `.\gbarecomp.exe build --rom "...\Road Rash - Jailbreak (USA).gba" --output "work\RRJ_recomp"`.
- [ ] **P3-03** Build generated library (`build.ps1` → `gbarecomp_game.lib`). Resolve compile errors; log any generated-code gaps.
- [ ] **P3-04** Assemble a minimal host app + `game.toml` cartridge config using the closest public game repo (e.g. `MarioKartSuperCircuitRecomp`) as the reference; get the game to **boot to the Magic Pockets/EA logo** and reach the title screen. Evidence: screenshot + frame log.
- [ ] **P3-05** Turn on coverage instrumentation (`GBARECOMP_STRICT_STATIC=1` for coverage burn-down runs; healing cache off; interpreter traces on) and record **static coverage %** as a tracked baseline metric.
- [ ] **P3-06** Feed `entries.txt` (P2-04) into analysis; re-generate; record coverage delta.
- [ ] **P3-07** If mstan pipeline fails structurally on this ROM (documented reasons), activate fallback: build `sp00nznet/gbarecomp` and repeat P3-02..P3-05 there. Record the comparison in §8.3 as a decision update.

### Phase P4 — Hardware Layer Completion (Runtime)
- [ ] **P4-01** PPU: verify all modes/effects from P2-08 render correctly (affine BGs, windows, blending, mosaic, OBJ affine/priority). Differential screenshots vs mGBA per scene.
- [ ] **P4-02** DMA: verify all 4 channels incl. HBlank audio FIFO feeding and any "special" usage.
- [ ] **P4-03** IRQ/timers: verify VBlank/HBlank/VCount/timer IRQ timing end-to-end (raster effects, sound rate).
- [ ] **P4-04** Input: keyboard/gamepad mapping, correct KEYINPUT semantics, any KEYCNT IRQs.
- [ ] **P4-05** Saves: implement/validate the save chip determined in P2-06; round-trip a real save file from mGBA into the native build and back.
- [ ] **P4-06** BIOS calls: confirm SWI coverage used by the game (decompression is the critical one); ensure HLE/recompiled BIOS path matches.
- [ ] **P4-07** Game-specific hooks (only where unavoidable): widescreen/camera factors, speed hacks — implemented as opt-in mods, never hard-coded (see mstan `.gbamod` pattern).

### Phase P5 — Audio (GAX 3.03A)
- [ ] **P5-01** Baseline: hardware-fidelity audio path (DirectSound FIFO A/B + PSG) — capture reference audio from mGBA for 3 scenes; spectral/A-B comparison.
- [ ] **P5-02** GAX state instrumentation: from P2-05 map GAX song/voice structures; log voice state while playing under mGBA.
- [ ] **P5-03** Optional GAX shadow mixer (float mixing from GAX voice state) with continuous cross-check against the hardware path; degrade loudly, never silently (pattern from JRickey).
- [ ] **P5-04** Output resampling (band-limited), DC blocker, soft-clip; keep "faithful" mode default.

### Phase P6 — Decompilation Support Track (Track B)
- [ ] **P6-01** Stand up the pret-style build skeleton for a *single overlay/region* (not the whole game): `tools/`, `Makefile`, agbcc build (WSL), `rom.sha1` gate. Reference: zeldaret/tmc + jellees/mksc layouts.
- [ ] **P6-02** Compiler fingerprinting: compile a C corpus with agbcc and (if obtainable legally) other era compilers; diff codegen vs ROM snippets with objdiff; decide matching compiler. Record in §8.3.
- [ ] **P6-03** First decompiled function(s): start with the boot/IRQ path and one anchored level-table accessor (from P1-07); flow: Ghidra → m2c (`--target gba`) → C → objdiff → decomp-permuter(-arm) for near-matches.
- [ ] **P6-04** Symbol overlay: export named symbols (address,name) and feed mstan/gbarecomp's symbol import (`tools/symbol_import/import_decomp_symbols.py`) so runtime logs/debug surfaces show real names.
- [ ] **P6-05** Progress metrics: add objdiff/decomp.dev-style reporting (even a simple `progress.py` counting matched functions/bytes) and publish locally.

### Phase P7 — Verification & Acceptance
- [ ] **P7-01** Build the differential harness: boot both mGBA and native build from identical states; compare per-frame framebuffer hashes (allow configurable tolerance for presentation-only differences) and EWRAM/IWRAM hash diffs at checkpoints.
- [ ] **P7-02** Lockstep function conformance (where feasible, borrowing sp00nznet's harness design): interpreter vs native per function on randomized inputs.
- [ ] **P7-03** Regression suite: scripted scenarios (title, each mode, save/load, crash recovery) run headless in CI on every change; store results in `docs/verification/`.
- [ ] **P7-04** Performance gate: 60 fps with headroom on a mid-range PC; profile hot paths.

### Phase P8 — Packaging & Release Engineering
- [ ] **P8-01** Launcher flow: user points at own ROM (hash-checked) + BIOS (if required by chosen stack); no bundled game data.
- [ ] **P8-02** Save migration/import from mGBA for players.
- [ ] **P8-03** Release checklist (legal + technical): no derived code in artifacts; reproducibility notes; credits for all tools/communities. Consider the mstan `.gbamod` package format for optional enhancements.
- [ ] **P8-04** Optional stretch: widescreen, 60 FPS render mod, netplay from framework support.

### Phase P9+ — Long-Term (opportunistic)
- [ ] **P9-01** Expand Track B coverage (game-state machine, physics, menus) with community help; keep matching behind, semantics first.
- [ ] **P9-02** Engine-dossier: document the Magic Pockets engine (modules, formats, GAX integration) — potentially reusable across their other GBA titles.
- [ ] **P9-03** Revisit `JRickey/gba-recomp` gamedb: if our title gets mapped upstream (or we contribute a map), re-run under that framework for a zero-interpreter build comparison.

---

## 5. Environment Setup (Windows-First)

> Record exact versions in Section 8.4 as they are installed. Commands assume PowerShell 7 unless noted.

**5.1 Core tools**
- Ghidra (latest, JDK 21) — `ghidra.re/ghidra_docs/...` or GitHub releases; then install GBA loader extension (SiD3W4y/GhidraGBA build: `gradle` with `GHIDRA_INSTALL_DIR`; or RetroReversing precompiled zip for Ghidra 11.1.2).
- mGBA (latest) — for debugging (GDB stub + Lua) and as oracle.
- Python 3.13 (present) + `pip install m2c`-style usage from source (`matt-kempster/m2c`), plus `decomp-permuter` (`pip install pynacl toml Levenshtein`), optional.
- Git (present).
- objdiff CLI/GUI (single exe from GitHub releases).

**5.2 Track A toolchain (native Windows)**
- MSYS2/MinGW64 or Visual Studio 2022 Build Tools (Desktop C++), CMake ≥ 3.16, Ninja, SDL2 (vcpkg: `vcpkg install sdl2:x64-windows`).
- mstan/gbarecomp CLI (release zip) + a reference game repo (e.g. `MarioKartSuperCircuitRecomp`) for host-app and `game.toml` patterns.
- Fallback: sp00nznet/gbarecomp (CMake; MSVC supported, headless on clang-cl).
- Optional: Rust (stable) for JRickey/gba-recomp and objdiff-from-source.

**5.3 Track B toolchain (WSL1/2 per pret INSTALL)**
```bash
wsl --install -d Ubuntu --enable-wsl1     # PowerShell as Admin; then: wsl --set-version Ubuntu 1
sudo apt update && sudo apt install build-essential binutils-arm-none-eabi git libpng-dev
git clone https://github.com/pret/agbcc && cd agbcc && ./build.sh && ./install.sh ../<project>
```
devkitARM alternative for modern builds: devkitPro installer → `gba-dev` component; Debian/Ubuntu via `dkp-pacman -S gba-dev`.
Homebrew-style extras for Track B: `decomp-permuter` (with `laqieer/decomp-permuter-arm` if needed), `asm-differ`, `objdiff`, `m2c`, `gba_lib_func_sig`.

**5.4 Suggested install root** `E:\Project\Decopm\tools\` for binaries and `E:\Project\Decopm\work\` for generated/uncommitted artifacts (both `.gitignore`d).

---

## 6. Verification & Acceptance Strategy

**Principle:** the emulator is the oracle; the native build must be *differentially indistinguishable* on observable behavior, with tunable tolerance only for presentation-layer enhancements.

1. **State-anchored differential runs:** establish savestates in mGBA at checkpoints (boot logo, title, menu, race start, mid-race, save screen). Run mGBA N frames → hash framebuffer + RAM regions; run native build from equivalent state → compare hashes. Tooling: mGBA Lua for hashing; native build's headless/dump flags (mstan has TCP debugging/traces/snapshots; sp00nznet has `--frames/--screenshot`).
2. **Lockstep conformance (per function):** run the same function natively and in the interpreter from identical machine state on captured inputs; diff register/memory effects (sp00nznet `docs/conformance.md` model; `GBA_FUNC_TRACE`, `GBA_TRACE_INTERP`).
3. **Coverage metrics:** % of executed PCs that are statically translated (target 100% before release; `GBARECOMP_STRICT_STATIC=1` as the hard gate).
4. **Save round-trip:** create save in mGBA → load in native build → save in native → reload in mGBA; byte-compare `.sav` (accounting for chip protocol differences).
5. **Audio:** record mGBA reference, null-test the faithful path (expect near-identical for hardware-level path), and perceptual A/B for enhanced path.
6. **Regression suite** (P7-03) runs headless; any hash drift is a failure until explained in the session log.

**Metric definitions (to track over time):**
- `coverage_static = translated_functions / executed_functions` (from coverage traces)
- `coverage_dynamic = executed_PCs_matched / executed_PCs_total`
- `framebuffer_match_rate = matched_frame_hashes / compared_frames`
- `decomp_match = matched_functions / total_functions` (Track B; objdiff "fuzzy" and "exact" separately)

---

## 7. Repository Layout (Proposed)

```
E:\Project\Decopm\
├─ RESEARCH_AND_PLAN.md          # THIS FILE (source of truth)
├─ .gitignore                    # excludes ROM/BIOS/generated/work
├─ Road Rash - Jailbreak (USA).gba   # local only, NEVER committed
├─ docs/
│  ├─ legal.md                   # P0-07
│  ├─ recon/                     # recon reports (text only)
│  ├─ findings/                  # audio_gax.md, ppu_usage.md, ...
│  └─ verification/              # differential run logs
├─ tools/
│  ├─ recon/rom_recon.py         # P0-06
│  ├─ mgba/                      # Lua trace suites (P2-02)
│  └─ symbol_import/             # wrappers around gbarecomp symbol import
├─ symbols/                      # hand-authored symbol maps (address,name) — reviewed, non-derived only
├─ decomp/                       # Track B skeleton (P6) — hand-written C only
├─ work/                         # NOT COMMITTED: generated C++, build dirs, dumps, savestates
└─ releases/                     # NOT COMMITTED: packaged builds (user-supplied ROM required)
```

---

## 8. Dynamic Progress Tracker

### 8.1 Milestones

| ID | Milestone | Target phase | Status | Evidence |
|---|---|---|---|---|
| M0 | Research + plan + baseline documented | P0 | `[~]` (this doc) | RESEARCH_AND_PLAN.md v0.1.0 |
| M1 | Toolchain installed & verified | P0 | `[ ]` | Section 8.4 |
| M2 | Static function/data map + entries.txt | P1–P2 | `[ ]` | docs/recon/*, entries.txt |
| M3 | Native build boots to title screen | P3 | `[ ]` | screenshot + frame log |
| M4 | In-race gameplay + PPU parity | P3–P4 | `[ ]` | differential runs |
| M5 | Saves round-trip | P4 | `[ ]` | save diff report |
| M6 | Audio baseline (hardware-fidelity) | P5 | `[ ]` | reference recordings |
| M7 | Full single-player playability | P7 | `[ ]` | regression suite green |
| M8 | First decompiled symbols overlaid | P6 | `[ ]` | objdiff report, symbol import log |
| M9 | Release-quality package | P8 | `[ ]` | release checklist signed |

### 8.2 Tracker Table (task-level status summary)

| Phase | Title | Status | Notes |
|---|---|---|---|
| P0 | Scaffolding & baseline | `[~]` | Doc written; git init + dump verification pending |
| P1 | Static analysis & map building | `[ ]` | Blocked on tool installs (P0-08) |
| P2 | Dynamic analysis & coverage | `[ ]` | |
| P3 | First native bring-up | `[ ]` | |
| P4 | Hardware layer completion | `[ ]` | |
| P5 | Audio (GAX) | `[ ]` | |
| P6 | Decompilation support track | `[ ]` | |
| P7 | Verification & acceptance | `[ ]` | |
| P8 | Packaging & release | `[ ]` | |
| P9 | Long-term / stretch | `[ ]` | |

### 8.3 Decision Log (append-only)

| # | Date | Decision | Rationale | Supersedes |
|---|---|---|---|---|
| D1 | 2026-10-11 | Static recompilation as primary path | Fastest route to native execution; mature-enough tooling (3 frameworks) | — |
| D2 | 2026-10-11 | `mstan/gbarecomp` primary; `sp00nznet/gbarecomp` fallback; `JRickey/gba-recomp` reference | Feature depth, Windows CLI, coverage tooling, proven titles | — |
| D3 | 2026-10-11 | mGBA as differential oracle | Established methodology (lockstep conformance precedent) | — |
| D4 | 2026-10-11 | Decomp track = opportunistic, symbol-first | Multi-year scope realistically; symbols deliver value early (MKSC precedent) | — |
| D5 | 2026-10-11 | Audio: hardware-fidelity baseline, GAX enhancements later | Verifiability, legal cleanliness | — |
| D6 | 2026-10-11 | WSL for decomp builds, native Windows for recomp/Ghidra/mGBA | Tooling fit; pret INSTALL guidance | — |
| D7 | 2026-10-11 | No ROM/BIOS/generated code in VCS ever | Legal hygiene | — |

*(Future entries: add new rows; if changing D1–D7, add a new row with "Supersedes Dx" and update the roadmap accordingly.)*

### 8.4 Tools & Versions (fill as installed)

| Tool | Version | Install path | Status | Notes |
|---|---|---|---|---|
| Python | 3.13.7 | system | `[x]` verified 2026-10-11 | recon script ran |
| Git | 2.51.0.windows.1 | system | `[x]` verified 2026-10-11 | repo not initialized yet |
| Ghidra | — | — | `[ ]` | + GBA loader extension |
| mGBA | — | — | `[ ]` | GDB stub + Lua |
| devkitARM / binutils-arm-none-eabi | — | — | `[ ]` | Track B |
| agbcc | — | — | `[ ]` | build in WSL |
| m2c | — | — | `[ ]` | `--target gba` |
| decomp-permuter (+arm) | — | — | `[ ]` | |
| objdiff | — | — | `[ ]` | ARM support |
| gbarecomp CLI (mstan) | — | — | `[ ]` | pin release tag/commit |
| gbarecomp (sp00nznet) | — | — | `[ ]` | fallback |
| gba-recomp (JRickey) | — | — | `[ ]` | reference only |
| MSYS2/MinGW64 + CMake + Ninja + SDL2 | — | — | `[ ]` | Track A host |
| WSL distro | — | — | `[?]` | verify WSL1 availability |

### 8.5 Open Questions

| # | Question | Impact | How to answer | Status |
|---|---|---|---|---|
| Q1 | Is the header checksum `0x00` normal for this dump; is there a better verified dump? | Baseline validity | No-Intro/redump lookup (P0-05) | OPEN |
| Q2 | Which compiler/toolchain built the game (for Track B matching)? | Track B fidelity | Fingerprint with objdiff + candidate compilers (P6-02) | OPEN |
| Q3 | Save chip type? | Runtime correctness | mGBA `0x0E000000` trace (P2-06) | OPEN |
| Q4 | How much code is ARM vs Thumb, and where is IWRAM-installed code? | Coverage strategy | P1-04, P2-02 | OPEN |
| Q5 | Which compression formats are used in the first MiB? | Asset pipeline (if needed) | P1-06 + dynamic dumps | OPEN |
| Q6 | Does the game use link-cable or any cartridge GPIO? | Scope | P2-02 MMIO/serial traces | OPEN |
| Q7 | Does mstan/gbarecomp resolve this ROM cleanly without custom entries? | Track A feasibility | P3-02..P3-06 | OPEN |
| Q8 | Does m2c parse Thumb-heavy GNU as output for this target cleanly? | Track B velocity | P6-03 trial | OPEN |

### 8.6 Session Log (append-only)

**Session 001 — 2026-10-11 — Research (agent: initial session)**
- Baseline: ROM parsed and hashed (SHA1 `48150529172ff411e3e1bd38b9a74d8b32e5fa59`); complement check verified OK; header checksum byte is `0x00` (flagged, Q1).
- Recon executed (inline Python, methodology reproducible): Thumb-dominant census; entropy map (first 1 MiB ≈ 7.8–8.0 → compressed blobs); found `* Engine by www.MagicPockets.com*` ×5; found `GAX Sound Engine 3.03A (Mar  5 2003)` + GAX2 API strings; harvested level/mode name strings (Pacific Highway, Suburban Dump, …).
- Web research completed (19 sources consulted; full list §9): three GBA static recompilers profiled; pret/zeldaret decomp workflow and tooling profiled; Ghidra GBA loaders + Ghidra/mGBA joint debugging verified; laqieer GBA RE suite identified; non-Pokémon decomp precedents (tmc, mksc) identified; MKSC recomp's decomp-symbol-import pattern identified as our Track A+B bridge.
- Deliverable: this document v0.1.0 created at `E:\Project\Decopm\RESEARCH_AND_PLAN.md`.
- Blockers: none. Caveat: WSL availability unverified; tool installs pending.
- Next actions: see §8.7.

*(Append new sessions below. Format: `**Session NNN — YYYY-MM-DD — <title> (agent: <id>)**` + bullets for done/evidence/blockers/next.)*

### 8.7 Next Actions (Top Priority Queue)

1. **P0-04** `git init` + `.gitignore` (exclude ROM/BIOS/derived artifacts) and commit this document.
2. **P0-08** Install core tools: Ghidra (+GBA loader), mGBA, devkitARM/binutils; verify each (record in §8.4).
3. **P0-05** Verify dump authenticity against No-Intro/redump (Q1).
4. **P1-01..P1-05** Ghidra project: function inventory, library signature pass, code/data boundary, entry points.
5. **P2-02** mGBA Lua trace suite skeleton (coverage + MMIO + IWRAM diff), then run first scripted playthrough for the function map (P2-04).

### 8.8 Evidence Index (paths to key artifacts)

| Artifact | Path | Note |
|---|---|---|
| This plan | `E:\Project\Decopm\RESEARCH_AND_PLAN.md` | source of truth |
| ROM baseline report | §1.1 of this file; regenerate via P0-06 | hashes + header |
| Recon findings | §2.7 of this file | to be re-run as committed script (P0-06) |
| Function map / entries | (pending) `work/recon/entries.txt` | generated; uncommitted by default |
| Differential reports | (pending) `docs/verification/` | committed summaries |

---

## 9. References (consulted 2026-10-11)

**GBA hardware**
- GBATEK — GBA/NDS technical reference: `https://problemkaputt.de/gbatek.htm`
- mGBA emulator: `https://github.com/mgba-emu/mgba`; scripting docs: `https://mgba.io/docs/scripting.html`

**Static recompilation (GBA)**
- mstan/gbarecomp (GBARecomp framework): `https://github.com/mstan/gbarecomp`
- sp00nznet/gbarecomp: `https://github.com/sp00nznet/gbarecomp`
- JRickey/gba-recomp: `https://github.com/JRickey/gba-recomp`
- MKSC recomp (worked example incl. decomp symbol import): `https://github.com/mstan/MarioKartSuperCircuitRecomp`
- Recompendium (catalog): `https://nio03.github.io/unricopie/en/`
- N64Recomp (lineage): `https://github.com/N64Recomp/N64Recomp`

**Matching decompilation toolchain**
- pret/pokeemerald (workflow + INSTALL.md): `https://github.com/pret/pokeemerald`
- pret/agbcc: `https://github.com/pret/agbcc`
- zeldaret/tmc (Minish Cap decomp): `https://github.com/zeldaret/tmc`
- jellees/mksc (Mario Kart: Super Circuit decomp): `https://github.com/jellees/mksc`
- m2c decompiler: `https://github.com/matt-kempster/m2c`
- decomp-permuter: `https://github.com/simonlindholm/decomp-permuter`
- objdiff: `https://github.com/encounter/objdiff`; progress tracking: `https://decomp.dev/`

**GBA reverse-engineering tools**
- Laqieer GBA RE suite (ida_gba_stuff, gba_lib_func_sig, gba-disasm-decomp-tools, decomp-permuter-arm, libsavgba): `https://laqieer.github.io/reverse-engineering.html`
- Ghidra GBA loaders: `https://github.com/SiD3W4y/GhidraGBA`, `https://github.com/pudii/gba-ghidra-loader`, `https://github.com/RetroReversing/GhidraRetroReversing`
- Ghidra + mGBA joint debugging tutorial: `https://wrongbaud.github.io/posts/ghidra-debugger/`

**Homebrew / modern GBA build stacks**
- gba-toolchain (CMake; libgba, tonclib, grit, maxmod, agbabi): `https://github.com/felixjones/gba-toolchain`
- libtonc documentation: `https://gbadev.net/tonc/`

**Target context**
- Road Rash: Jailbreak (developer/publisher, Magic Pockets for GBA): MobyGames/Wikipedia/Wikiwand entries; PSX decomp port (different codebase): `https://github.com/psxports/RoadRashJailbreak-xport`

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **Matching decompilation** | Reconstructing C/asm such that it compiles byte-identically to the original binary (the pret/zeldaret methodology). |
| **Static recompilation (AOT)** | Translating the original machine code to C/C++ ahead of time; no interpreter/JIT at runtime for translated code. |
| **Oracle** | The reference implementation used for differential testing (here: mGBA running the authentic ROM). |
| **Lockstep conformance** | Running native and reference code from identical state and diffing observable effects. |
| **Healing / interpreter tier** | Runtime fallback that executes (and optionally caches) code the static analyzer could not resolve. |
| **HLE / LLE** | High-/Low-Level Emulation. HLE implements device *behavior* (e.g., audio mixer semantics); LLE reimplements device *mechanics* (registers, FIFOs, cycle timing). |
| **IWRAM / EWRAM** | GBA internal work RAM: 32 KiB fast (code often copied here) / 256 KiB slow. |
| **MMIO** | Memory-mapped I/O — hardware registers accessed at fixed addresses (`0x04000000`+). |
| **SWI** | ARM software interrupt — BIOS service calls (decompression, math, memory copy). |
| **GAX** | Third-party commercial GBA audio middleware ("GAX Sound Engine"); this game embeds v3.03A. |
| **Track A / Track B** | This project's parallel workstreams: A = static recompilation (primary); B = matching decompilation (support). |
