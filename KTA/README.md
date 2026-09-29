# KTA Claude Code Mobile Handover v0.1

This is the Claude Code-optimized continuation package for Knowledge → Action.

Start with:
`00_START/MOBILE_START_HERE.md`

The root `CLAUDE.md` is the persistent project instruction file.

This package adds:
- Claude Code-specific project instructions;
- durable local state files;
- an independent architecture-refinement pass;
- phone-friendly owner interaction;
- material-change approval batching;
- context-reset recovery instructions;
- checkpoint discipline;
- optional git-based state tracking.

The original authoritative KTA project artifacts are preserved inside the package.

## Integrity note (added 2026-09-29)
`CHECKSUMS_SHA256.json` certifies the handover package **as received**. All 18 files verified OK on import (git commit `114706b`). Files have changed since then, so git history is now the integrity and version record, not that manifest.

## Validation and releases (added 2026-09-29)
- Run everything with `pip install jsonschema openpyxl && python KTA/tools/validate_all.py`. It must be GREEN.
- Releases live in `06_RELEASES/`, each with a Git tag and a checksum-verified bundle (Constitution Dual-Layer rule). The current release is **KTA-REL-0.1**.
