# HANDOFF: KTA-REL-0.1 (Lane 02 v0.1 accepted and released)
Date: 2026-09-29 · Branch `ccr-0bee19c7-psyma2` · Tag `KTA-REL-0.1` · Supersedes `LANE_02_HANDOFF_v0.1.md` §8–9

## 1. State in one line
Lane 02 v0.1 was accepted with repairs. R1–R5 are done, the validation suite is GREEN, the owner decisions are applied, and release KTA-REL-0.1 is built and tagged. **The builder is paused** until the owner hands over the dev cases and gives the go-ahead.

## 2. What changed (this checkpoint)
- **Owner decisions D1–D6** are recorded in `02_STATE/OWNER_DECISIONS_PENDING.md`.
- **Authoritative changes:**
  - Constitution v0.1-r1 (KTA-004).
  - Blueprint v0.1-r1 (KTA-005, 006, 007, 008).
  - Lane Map, Source Manifest.
  - Registries: KTA-004..008, DEC-005 amended, DEC-007..011, EXP-V0-00..04, PARK-001/002/003/005.
  - Current State.
  - `KTA/CLAUDE.md`: release workflow and blind-evaluation isolation.
- **Repairs:**
  - R1: null vs inconclusive.
  - R2: INV-16 confidential boundary, with the revised P1.
  - R3: trust and progress.
  - R4: `kta_metrics.py`.
  - R5: `03_CURRENT_WORK/regression/` with `test_regression.py`.
- **Tools added:** `validate_all.py`, `build_release.py`, `verify_release.py`, and `tools/fixtures/` (reproducible fixture builders).
- **Protocol:** `03_CURRENT_WORK/BLIND_EVAL_PROTOCOL_v0.1.md`. It contains no cases.

## 3. Verify
```
pip install jsonschema openpyxl
python KTA/tools/validate_all.py      # expect GREEN 5/5
python KTA/tools/kta_metrics.py       # simulation: DUAR 2/3, safety gate clear
```

## 4. Remaining
- **Drive mirror:** pending the owner's manual upload (`06_RELEASES/README.md`).
- **Remote Git tag:** the tag push was refused (HTTP 403; the session can push only its branch). The owner creates tag `KTA-REL-0.1` on commit `f4a71d4` in GitHub → Releases (steps in `06_RELEASES/RELEASE_LOG.md`).
- **Blind evaluation:** waiting on the owner's 3 seed cases and the isolated case-generation session (protocol §8).
- **Pilot consent text:** needs final owner approval in pilot decision batch 2, which comes after the blind evaluation.
- **Not started:** the drafting/compiler prompt and the human pilot, both on hold by owner instruction.

## 5. Exact next action for the builder
**Wait.** Resume only when the owner does one of these:
- (a) confirms the Drive upload → mark it CONFIRMED in `06_RELEASES/RELEASE_LOG.md` and the Source Manifest release log;
- (b) hands over the **DEV** cases (never the sealed ones) and says to start the drafting prompt → build `03_CURRENT_WORK/ENGINE_DRAFTING_PROMPT_v0.1.md`, iterating on the simulation and dev cases only, then prepare a freeze tag for the owner's confirmation.
