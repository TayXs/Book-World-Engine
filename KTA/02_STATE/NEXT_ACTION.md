# NEXT ACTION

**Builder paused. Waiting on the owner** (see `05_HANDOFFS/RELEASE_KTA-REL-0.1_HANDOFF.md` §5).

Owner actions:
1. Upload the KTA-REL-0.1 bundle to Drive (`06_RELEASES/README.md`), then say "Drive upload for KTA-REL-0.1 done".
2. Write 3 seed cases and run the isolated case-generation session (`03_CURRENT_WORK/BLIND_EVAL_PROTOCOL_v0.1.md` §8). Keep the SEALED blocks outside this repo. Give the builder only the DEV block.

Builder, when the owner gives the go-ahead with the DEV cases:
- Save them as `03_CURRENT_WORK/eval_dev/DEV_CASES_v0.1.md`.
- Build `03_CURRENT_WORK/ENGINE_DRAFTING_PROMPT_v0.1.md` (intake notes → redaction → packet → checker → repair loop), iterating on the simulation and dev cases only.
- Propose a freeze tag for the owner to confirm.
- **Never read sealed cases before the freeze.**

Validation: `python KTA/tools/validate_all.py` must be GREEN before any release.
