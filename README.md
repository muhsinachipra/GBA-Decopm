# Road Rash: Jailbreak (GBA) — Native Port Research

This project aims to run the USA GBA version of **Road Rash: Jailbreak** natively on modern PCs, starting with Windows. The primary approach is static recompilation of ARM/Thumb code to C/C++ with a GBA hardware runtime. Incremental matching decompilation supports readable symbols and modding, while mGBA provides the behavioral reference.

## Current status

The project is in early development. The ROM baseline has been verified, reconnaissance tooling is available, and the core analysis/recompilation toolchain has been installed locally. The next step is Ghidra GBA import and static analysis, followed by dynamic coverage collection.

**There is no playable native build or release package yet.** See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) Sections 8.6–8.7 for the latest evidence and next actions.

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

An optional `--nointro-dat` argument accepts a local No-Intro DAT for cross-checking. This script produces a reconnaissance report; the native game build remains a future milestone.

## Contributing

Read AGENTS.md, PROJECT_CONTEXT.md Sections 1, 3, 4, and 8, and the legal policy before making changes. Keep roadmap and tracker updates backed by evidence, and append a session entry before handing work off.

The repository contains documentation, hand-written tooling, and permitted reports. ROMs, BIOS images, extracted copyrighted assets, and ROM-derived generated code must remain local and must never be committed or distributed. See [docs/legal.md](docs/legal.md) for the full rules.
