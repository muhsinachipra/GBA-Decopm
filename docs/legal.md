# Legal Policy & Checklist

Effective 2026-10-11. Applies to every contributor (human or AI agent) and every artifact in this repository.

## 1. Never commit, publish, or distribute

- The game ROM (`Road Rash - Jailbreak (USA).gba`) — copyrighted by Electronic Arts. Owned locally by the user; used for interoperability research only.
- GBA BIOS images (`*.bin`) in any form.
- Extracted game assets (graphics, audio, music, level data, text) in any form.
- ROM-derived generated code: static-recompiler output (C/C++ shards), automatically lifted symbol maps, decompiler output, execution traces that include ROM windows.
- Save files / savestates created from the commercial game where redistribution would embed game data.
- Leaked SDKs, leaked source, leaked documentation, or any confidential material. Everything in this project uses clean-room, publicly documented behavior (GBATEK, published open-source tooling).

## 2. Where derived or local-only artifacts may live

- Local-only, `.gitignore`d directories: `work/`, `build/`, `generated/`, `releases/`.
- Committed content is limited to: project documentation, hand-written tooling scripts, hand-written decompilation C (asset-free, pret/zeldaret pattern), and small text reports that contain only hashes, addresses, sizes, and short identifier strings (no ROM windows, no asset data).

## 3. Hash-gating policy

- All tooling, symbol maps, and patches are gated to the exact ROM revision:
  - SHA1 `48150529172ff411e3e1bd38b9a74d8b32e5fa59`
  - SHA256 `f0af99188e7ffaf0b0ea95e1503365a7eaf2eac6c9bc01c18c0f5c5ed010d4b6`
  - CRC32 `8834af99`, MD5 `0a4da0bbdad29f2faa5584b49b0a4f5d`, 4,194,304 bytes.
- Verified against the No-Intro DAT (2026-07-07): `Road Rash - Jailbreak (USA)`, serial `A9RE`. See `docs/recon/nointro_verification.md`.
- If recomputed hashes differ from the above, STOP, log the discrepancy in `PROJECT_CONTEXT.md` §8.6, and do not proceed.

## 4. Public release pattern (if ever)

- Ship no game data and no ROM-derived code.
- A launcher/build tool may ingest the user's own legally obtained ROM locally and verify it by hash.
- Release artifacts must pass the checklist in §6.

## 5. Incident log

| Date | Incident | Remediation | Residual risk |
|---|---|---|---|
| 2026-10-11 | ROM was committed and pushed to the public GitHub repo `muhsinachipra/GBA-Decopm` (commit `0dbaf60`, pushed 06:48 UTC; live for ~10 minutes; 0 forks) | `.gitignore` added; ROM untracked (`git rm --cached`); initial commit rewritten to `1faf5c3` without the ROM; `--force-with-lease` push purged the remote reference; verified raw fetch returns 404 and the contents API shows only `.gitignore` + `RESEARCH_AND_PLAN.md` | GitHub may retain unreferenced objects reachable by exact SHA until garbage collection; third-party caches/archives are outside our control. If strict removal is required, open a GitHub Support request referencing commit `0dbaf60a18acc5774fbd7c7ac436a9927ac73cb0` and blob `e3160957abb1f37c64dc0f7e3c1632e4b89b97f4`. |

## 6. Pre-commit checklist

1. `git status --short` — every path is allowed by §2.
2. `git diff --cached --stat` — no binary blobs, no large assets.
3. `git check-ignore` confirms the ROM and BIOS are ignored.
4. Reports contain only hashes/addresses/short identifiers — no ROM windows.
5. Commit messages are accurate; never attach derived files "just this once".
