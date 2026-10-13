# Road Rash: Jailbreak (GBA) — Native Port Research

This project aims to run the USA GBA version of **Road Rash: Jailbreak** natively on modern PCs, starting with Windows. The primary approach is static recompilation of ARM/Thumb code to C/C++ with a GBA hardware runtime. Incremental matching decompilation supports readable symbols and modding, while mGBA provides the behavioral reference.

## Current status

The Windows host builds locally and reaches the title and Wild Race course-selection menus with strict static dispatch. Internal comparisons against the framework interpreter pass at several boot/menu checkpoints. Full races, independent mGBA comparisons, saves, audio fidelity, and the remaining modes still need verification.

**There is no release package yet; the local native build is experimental.** See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) Sections 8.6–8.7 and the [bring-up report](docs/verification/native_bringup.md) for evidence and resume commands.

## Start here

| Document | Purpose |
|---|---|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Project identity, research, decisions, roadmap, toolchain, and session history |
| [AGENTS.md](AGENTS.md) | Repository working instructions and handoff requirements |
| [Legal policy](docs/legal.md) | Artifact handling, repository restrictions, and pre-commit checks |
| [ROM verification](docs/recon/nointro_verification.md) | No-Intro dump verification and header findings |
| [Reconnaissance report](docs/recon/rom_recon_report.md) | Baseline hashes, entropy, instruction patterns, and string anchors |

## Local reconnaissance

The existing [reconnaissance script](tools/recon/rom_recon.py) uses Python's standard library. Python 3.13.7 is the currently verified version; the full toolchain inventory is in PROJECT_CONTEXT.md Section 8.4. Downloaded tools are local and are not included in a clone.

1. Supply your own local `Road Rash - Jailbreak (USA).gba` file. Compare its SHA1 and SHA256 with PROJECT_CONTEXT.md Section 1.1 before analysis. Stop if either differs.
2. From the repository root in PowerShell, inspect the script's options:

   ```powershell
   python tools/recon/rom_recon.py --help
   ```

3. Generate a report in the ignored local workspace:

   ```powershell
   New-Item -ItemType Directory -Force work/recon | Out-Null
   python tools/recon/rom_recon.py "Road Rash - Jailbreak (USA).gba" --out work/recon/rom_recon_report.md
   ```

An optional `--nointro-dat` argument accepts a local No-Intro DAT for cross-checking.

## Local native build

The [build wrapper](tools/recomp/build.py) verifies both ROM hashes from PROJECT_CONTEXT.md, generates source under ignored `work/`, and builds the [hand-written Windows host](native/main.cpp). The host checks the ROM and the BIOS image translated into that build before launching.

Use the pinned `mstan/gbarecomp` checkout at `tools/bin/gbarecomp-src`, revision `5e89943528aee7bc1c399bdbd035364a4b41dd10`, with its `external/arm-recomp-core`, `external/recomp-net`, and `external/rbengine` submodules initialized. Install MSYS2 MinGW GCC, CMake, Ninja and SDL2; the verified local paths are in PROJECT_CONTEXT.md §8.4. Downloaded dependencies are not included in this repository.

```powershell
python tools/recomp/build.py --bios path/to/your/local-bios.bin
```

For the experimental open-source BIOS path used during bring-up, see the [reproduction instructions](docs/verification/native_bringup.md). That path needs the pinned mGBA source and local ARM binutils. A retail BIOS build still requires its own verified analysis/coverage; neither BIOS backend has full-game acceptance evidence yet.

Launch a matching local build with:

```powershell
work/native/build/RoadRashJailbreakRecomp.exe --rom "Road Rash - Jailbreak (USA).gba" --bios work/open-bios/hle-bios.bin --bios-hle --window
```

All generated game/BIOS code, binaries, captures, saves and assets remain local. The repository contains only the host, hand-written tooling/configuration, input schedules, documentation and permitted reports.

## Contributing

Read AGENTS.md, PROJECT_CONTEXT.md Sections 1, 3, 4, and 8, and the legal policy before making changes. Keep roadmap and tracker updates backed by evidence, and append a session entry before handing work off.

The repository contains documentation, hand-written tooling, and permitted reports. ROMs, BIOS images, extracted copyrighted assets, and ROM-derived generated code must remain local and must never be committed or distributed. See [docs/legal.md](docs/legal.md) for the full rules.
