# LANE 02 HANDOFF v0.1: Mission Generation Engine
Date: 2026-09-29 · From: Claude Code session 1 · Branch: `ccr-0bee19c7-psyma2` (repo `TayXs/Book-World-Engine`, folder `KTA/`)

## 1. Status in one line
All 9 Lane 02 build steps have a **draft** deliverable. The specs are at `0.1-rev1`, and they are machine-checked (0 errors; 27 tests passing). Nothing is owner-accepted yet. The authority docs are unchanged. **4 material decisions are pending** (none of them block further work).

## 2. What changed (artifacts)
| # | Build step | Artifact (under `03_CURRENT_WORK/`) |
|---|---|---|
| — | Architecture refinement review | `KTA_ARCHITECTURE_REFINEMENT_REVIEW_v0.1.md` (25 findings) |
| 1 | Output contract | `MISSION_GENERATION_OUTPUT_CONTRACT_v0.1.md` + `schemas/mission_packet`, `uncertainty_item`, `common` |
| 2 | Diagnostic architecture | `DIAGNOSTIC_ARCHITECTURE_v0.1.md` + `diagnostic_question_registry_v0.1.json` |
| 3 | Task map | `TASK_MAP_SCHEMA_v0.1.md` + `schemas/task_map` |
| 4 | Planner rules | `MISSION_PLANNER_RULES_v0.1.md` (MPR-01..20) |
| 5 | ActionExperiment | `ACTION_EXPERIMENT_SCHEMA_v0.1.md` + `schemas/action_experiment` (9 archetypes) |
| 6 | Feedback and adaptation | `FEEDBACK_ADAPTATION_LOGIC_v0.1.md` + `schemas/feedback_record`, `adaptation_decision` |
| 7 | Simulation | `THREE_USER_SIMULATION_v0.1.md` + `simulation/SIM-{ACC,DES,SAL,LOW,OOS}` |
| 8 | Failure-mode review | `FAILURE_MODE_REVIEW_v0.1.md` (22 findings, 15 fixed) |
| 9 | Pilot preparation | `V0_PILOT_PREPARATION_v0.1.md` |
| tools | Verification | `../tools/kta_check.py`, `../tools/test_kta_check.py`, `../tools/render_registries.py` |

**To verify** (from the repo root):
```
pip install jsonschema
python KTA/tools/kta_check.py
python -m unittest KTA/tools/test_kta_check.py
```

## 3. The design in brief
1. **Mission Packet.** One JSON contract per user and revision. It has 15 invariants and 4 differentiation tests.
2. **Uncertainty Ledger.** Every unknown is typed by *who can resolve it*, and routed to ask, experiment, research or explain. This is KTA's core difference from a general LLM, which answers everything from its own weights.
3. **Intake by backward derivation.** 11 core question cards, about 14 minutes. Each card states the packet fields it feeds and a change test.
4. **Task Map.** Output-anchored tasks with 11 ordinal traits, each carrying a source and a confidence. There are no risk scores; exposure is a hypothesis sent to Lane 03.
5. **Planner.** 20 rules, each tagged as selection, sequencing, omission or adaptation, with a precedence order: safety > scope > evidence > identity > budget. Every leverage focus needs a destination for the time it frees.
6. **Experiment.** Pre-registered, with an observable measure, safe by default, and with branches written in advance.
7. **Feedback.** Neutral questions come first. Evidence is graded E0–E3. A decision table (A1–A18) maps results to next moves. n=1 evidence never becomes a general rule.

## 4. Still proposed (owner decisions)
- **Batch 1** (`02_STATE/OWNER_DECISIONS_PENDING.md`):
  - MCP-1: source of truth
  - MCP-2: data-safety rule
  - MCP-3: Blueprint reconciliation
  - MCP-4: North Star definition
- **Batch 2** (`V0_PILOT_PREPARATION_v0.1.md` §10): recruitment channel, operator, storage, retention and incentive. Asked after batch 1.
- **DEC-008:** accepting the Lane 02 v0.1 specs as the pilot specification (`04_REGISTRIES/PROPOSED_REGISTRY_UPDATES_v0.1.md`).

## 5. Rejected or parked
- **Parked** (proposed Parking Lot PARK-001..005):
  - reusing Truthcast for Lane 03;
  - the public mission name;
  - the Core Promise wording;
  - an independent adversarial review;
  - v0.2 field renames.
- **Rejected inside the specs:**
  - automation-risk scores;
  - long rating grids;
  - `policy_check` as a standalone experiment;
  - generic filler omissions;
  - treating a decline or a null result as success or failure.

## 6. Needs evidence (only the pilot can answer)
- Do users value selection and pre-registered experiments over a longer generic answer? (FM-12; EXP-V0-01)
- Attempt rates by archetype (FM-14; EXP-V0-02).
- Accuracy of self-reported task maps (EXP-V0-03).
- How much of packet quality the operator contributes (FM-13).
- Whether E2+ evidence at check-in is realistic.

## 7. Affected lanes
- **02:** complete for v0.1.
- **03:** receives the research-question interface. The EvidenceClaim schema is still to be written.
- **04:** must present omissions and reasoning as value (FM-12).
- **05:** takes over the ActionExperiment and Feedback logic, plus the learning across users.
- **06:** no software yet. Schemas are ready when needed.
- **07:** pilot preparation.
- **08:** proposed registry rows.

## 8. Next stage
Lane 02 v0.1 is specified. **The next stage is V0 pilot readiness**, in this order:
1. The owner answers batch 1. Claude then applies the approved changes: Constitution/Blueprint edits, registry rows, and a regenerated mirror.
2. **Engine drafting template** (non-material, can start now): the prompt and packet skeleton an LLM uses to draft `packet_r1.engine.json` from intake notes, validated by `kta_check.py`.
3. The owner answers batch 2, and the consent text is finalized.
4. A dry run with a volunteer or with the owner, then the pilot (Lane 07).

Other gaps to schedule: a Lane 03 minimum spec (the EvidenceClaim schema and a research-reuse cache) and a Lane 04 minimum spec (packet presentation).

## 9. Exact next action
> **Update, 2026-09-29:** the owner has called an acceptance checkpoint. **Do not start the drafting prompt.** Lane 02 is waiting for owner decisions D1–D6 in `03_CURRENT_WORK/KTA_LANE_02_ACCEPTANCE_PACKET_v0.1.md`. The acceptance packet's §10 replaces the order below.

If batch 1 is answered: apply the approved changes and propagate them (Propagation Rule).
If it is not: build `03_CURRENT_WORK/ENGINE_DRAFTING_TEMPLATE_v0.1.md` together with an example that runs one simulated intake through the template to a packet that passes `kta_check.py`.
