# Agent Instructions

These instructions apply throughout this repository.

## Read first

- Treat [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) as the source of truth for project identity, research, decisions, roadmap, tools, and progress.
- Before working, read Sections 1, 3, 4, and 8, especially the latest session entries (8.6) and next actions (8.7).
- Follow [docs/legal.md](docs/legal.md) for artifact handling and the pre-commit checklist.
- If status summaries conflict with newer evidence in the session log, use the latest verified evidence and correct the active summaries. Preserve historical entries.

## Project direction

- Prioritize the Windows native port through static recompilation (Track A).
- Matching decompilation (Track B) supports symbols and understanding; it must not block Track A.
- Use mGBA as the reference for behavior and differential verification.
- Use the tool paths and versions recorded in PROJECT_CONTEXT.md Section 8.4; verify availability before relying on them.

## ROM baseline and repository rules

- Recompute the local ROM's SHA1 and SHA256 and compare them with PROJECT_CONTEXT.md Section 1.1 before working. If either differs, stop and log the discrepancy in Section 8.6 before proceeding.
- Gate ROM tooling, symbol maps, and patches to that exact revision. Keep the authoritative hashes in PROJECT_CONTEXT.md rather than duplicating them here.
- Never commit, publish, or distribute ROMs, BIOS images, extracted copyrighted assets, ROM-derived generated code or symbol maps, traces containing ROM bytes, or saves containing game data.
- Keep derived artifacts in ignored local directories such as work/, build/, generated/, and releases/. Downloaded tools and archives belong in ignored tools/bin/ and tools/dl/.
- Commit only permitted documentation, hand-written tooling/configuration, asset-free hand-written decompilation source, and reports limited to hashes, addresses, sizes, and short identifiers. Check docs/legal.md Section 6 before committing.

## Verification and handoff

- Run checks appropriate to the change and record commands and observed results. Mark a task done only with evidence.
- Update affected roadmap checkboxes (Section 4) and tracker rows (8.2) together. Keep task IDs stable; record scope or strategy changes in the decision log (8.3).
- Before ending a work session, append a dated entry to Section 8.6 with the agent/session ID, changes, evidence, blockers, and next actions. Never rewrite previous entries; append corrections referencing them.
- Update Section 8.7 when priorities change. Keep detailed research and progress in PROJECT_CONTEXT.md; keep this file focused on working instructions.
