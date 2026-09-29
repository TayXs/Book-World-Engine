# KTA-REL-0.1: Release Notes
Date: 2026-09-29 · Milestone: **Lane 02 Mission Generation Engine v0.1, accepted with repairs R1–R5**
Governance: Constitution Dual-Layer Source of Truth rule (KTA-004), manual release mode (D1 option B).

## What this release contains
- **Authority, revision v0.1-r1:**
  - Constitution: Session Independence and the Dual-Layer Source of Truth.
  - Master Blueprint: Confidential Information Boundary (CORE), reconciled architecture and data model, North Star candidate (DUAR) with a separate safety gate, updated stage.
  - Lane Map.
  - Source Manifest, with a release log.
- **Registries:** KTA-004..008, DEC-005 (amended), DEC-007..011, EXP-V0-00..04, PARK-001/002/003/005.
- **Lane 02 specs at 0.1-rev2:**
  - Output Contract (INV-01..16).
  - Diagnostic Architecture (with the §6a confidential boundary at intake).
  - Task Map.
  - Mission Planner (MPR-01..20).
  - ActionExperiment (9 archetypes).
  - Feedback & Adaptation (A1–A18, with A16 split into A16a and A16b).
  - Simulation, Failure-Mode Review, V0 Pilot Preparation.
  - Blind Evaluation Protocol.
- **Tools:**
  - `kta_check.py`: schemas, invariants, decision table, INV-16 lint.
  - `kta_metrics.py`: DUAR, MAR, supporting metrics, safety gate.
  - `validate_all.py`.
  - Fixture builders.
  - 52 tests.
- **Fixtures:** 5 simulation users and 5 stress-trace regression cases.

## Repairs completed
| Repair | Change |
|---|---|
| R1 | Split `null_result` (measured, no effect) from `inconclusive` (too little evidence). FM-23. |
| R2 | Confidential Information Boundary implementation: INV-16, intake preface, redaction pass, lint, consent wording (DEC-009, P1 revised by the owner). |
| R3 | CQ-13 trust and CQ-14 mission progress. |
| R4 | The metrics tool, with the safety gate kept separate from DUAR (owner decision D4 amendment). |
| R5 | Stress traces ST-1..5 as automated regression fixtures. |

## Validation at release
`python KTA/tools/validate_all.py` → **GREEN**, 5/5 steps:
- fixtures are reproducible;
- the registry mirror matches;
- `kta_check`: 0 errors, 0 warnings;
- 52 tests pass;
- state files are valid.

## Known limitations carried forward
- Validation so far is closed-loop. The blind evaluation (EXP-V0-00) comes next.
- No drafting/compiler prompt exists yet.
- The pilot consent text still needs final owner approval (pilot decision batch 2).
- The Drive mirror is pending the owner's manual upload.
