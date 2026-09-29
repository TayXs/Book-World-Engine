# KTA ARCHITECTURE REFINEMENT REVIEW v0.1

Status: WORKING FILE (non-authoritative). Material proposals here have no effect until the owner approves them.
Date: 2026-09-29 · Reviewer: Claude Code · Scope: bounded review required by `CLAUDE.md` before Lane 02 execution.

## 0. What was reviewed

| Source | Authority | Integrity |
|---|---|---|
| `01_AUTHORITY/KTA_PROJECT_CONSTITUTION_v0.1.md` | 1 | SHA-256 OK |
| `01_AUTHORITY/KTA_MASTER_BLUEPRINT_v0.1.md` | 2 | SHA-256 OK |
| `04_REGISTRIES/KTA_REGISTRIES_v0.1.xlsx` (all 6 sheets) | 3 | SHA-256 OK |
| `02_STATE/*` | 4 | SHA-256 OK |
| `05_HANDOFFS/RESUME_PROMPT.md` | 5 | SHA-256 OK |
| `03_CURRENT_WORK/KTA_LANE_02_…CONTINUATION_v0.1.md` | 6 | SHA-256 OK |
| `01_AUTHORITY/KTA_PROJECT_LANE_MAP_v0.1.md`, `SOURCE_MANIFEST_v0.1.md` | supporting | SHA-256 OK |

**State recovery result.** All 18 files match `CHECKSUMS_SHA256.json`. The recovered state is internally consistent: stage = pre-V0 product definition; lane = 02; objective = Mission Generation Engine v0.1; next artifact = Mission Generation Output Contract. No experiments are active, no ideas are parked, no material changes are pending.

**Drive check.** The Source Manifest names four Google Drive file IDs as the originals. The Google Drive connector available in this session returned *not found* for them (the connected account cannot see those files). The handover ZIP is therefore the best available authoritative state. This matters for AR-01.

## 1. Classification key

- `NO_CHANGE_NEEDED`: examined; the current rule holds.
- `NON_MATERIAL_REFINEMENT`: clarifies or implements an already-approved rule. Implemented now, or implemented inside the Lane 02 drafts.
- `MATERIAL_CHANGE_PROPOSAL` (MCP): changes a CORE or CURRENT rule, the market, the mission, a metric, the scope, or major architecture. **Waits for the owner.** Batched in `02_STATE/OWNER_DECISIONS_PENDING.md`.

## 2. Summary

| Class | Count | IDs |
|---|---|---|
| MATERIAL_CHANGE_PROPOSAL | 4 | AR-01, AR-08, AR-10, AR-15 |
| NON_MATERIAL_REFINEMENT | 16 | AR-02, 03, 04, 05, 06, 07, 09, 11, 12, 13, 14, 16, 17, 18, 19, 20 |
| NO_CHANGE_NEEDED (incl. parked or evidence-pending) | 5 | AR-21 to AR-25 |

**Most important finding (AR-11).** Almost every section of the specified mission packet could be produced by a strong general-purpose LLM in one well-prompted conversation. KTA can't be defended on the packet alone. It has to be defended on three things a general LLM does not structurally do:
1. **Route each unknown to the right resolver.** Ask the user, observe it through an experiment, research it against evidence, or explain it. A general LLM answers all four from its own weights.
2. **Pre-register and observe real-world experiments** on the user's own work, then adapt.
3. **Accumulate structured outcome data** across users. This builds intervention intelligence that no general model has.

The Lane 02 drafts are designed around these three points. That changes no doctrine: it operationalizes DEC-004 (CORE) and the Lane 05 remit.

## 3. Findings

### A. Contradictions and ambiguities

**AR-01 · Source of truth: Google Drive vs repository · `MATERIAL_CHANGE_PROPOSAL`**
- *Current rule:* KTA-GOV-003 / KTA-003 (CORE) make Google Drive the durable source of truth. The Constitution's Chat Independence and Recovery rules are written for ChatGPT. Meanwhile, `CLAUDE.md` tells Claude Code to use the local filesystem as durable memory.
- *Problem:* There are now two unsynchronized stores. This session cannot reach the Drive originals, so every Claude Code session will write to git while Drive stays at the handover snapshot. Silent drift is the exact failure the Constitution exists to prevent. The XLSX registry is also hard to diff or edit from a phone or from Claude Code.
- *Proposal:* Make the git repository folder `KTA/` (repo `TayXs/Book-World-Engine`) the canonical working source of truth. Treat Drive as a mirror, refreshed at milestones. Reword the Chat Independence rule so it covers any AI tool or session, not only ChatGPT. Allow a Markdown rendering of the registries to become canonical later.
- *Affected:* Constitution, KTA-GOV-002/003, Source Manifest, Lane 00, Lane 08.

**AR-02 · Authority order differs between `CLAUDE.md` and the Constitution · `NON_MATERIAL_REFINEMENT` (implemented)**
- The Constitution lists "Approved Change and Decision Registry" at rank 3 and experiments at rank 5. `CLAUDE.md` puts "Registries" as a whole at rank 3. The registry workbook's own Overview sheet marks the Experiment Registry and Parking Lot as *non-authoritative*.
- *Resolution:* Read rank 3 as the **Change and Decision registries only**, which is consistent with both approved sources. `KTA_CURRENT_STATE.md` is the product-state snapshot. `PROJECT_STATE.json` is the operational work pointer and never overrides product doctrine. A clarifying note was added to `CLAUDE.md`.

**AR-03 · Three overlapping "unknown" sections in the packet · `NON_MATERIAL_REFINEMENT` (implemented in contract)**
- The Lane 02 packet lists *Known Unknowns*, *Knowledge Gaps* and *Research Questions* separately, with no boundary between them.
- *Resolution:* One **Uncertainty Ledger**. Each entry is typed by *who can resolve it*:

  | Kind | Answered by | Route |
  |---|---|---|
  | `user_context` | the user already knows | ask |
  | `personal_empirical` | only observation in the user's real context | experiment |
  | `world_fact` | external evidence (Lane 03) | research |
  | `understanding_gap` | the user needs a concept to decide well | explain (Lane 04) |

  The three spec sections become filtered views of the ledger. This removes duplication and gives the Mission Planner one prioritization surface.

**AR-04 · "Personalization" is both a pipeline stage and a property · `NON_MATERIAL_REFINEMENT` (interpretation; Blueprint wording goes to AR-10)**
- The Blueprint architecture places "Personalization" as a stage after the Evidence Engine. The Blueprint also defines personalization as *selection, sequencing, omission, adaptation*, which is Mission Planner and Feedback work. A separate late stage invites cosmetic rewriting, which the Blueprint forbids.
- *Resolution:* In Lane 02, personalization is a cross-cutting property. Every planner rule is tagged with the personalization act it performs, and every packet element must carry a user-grounded `relevance`.

**AR-05 · Lane ownership overlap between Lane 02 and Lane 05 · `NON_MATERIAL_REFINEMENT` (implemented)**
- Lane 02 must specify the ActionExperiment schema and the feedback logic. The Lane Map gives ActionExperiments, check-ins and adaptation to Lane 05.
- *Resolution:* Lane 02 owns the **interface**: the first experiment and the check-in criteria inside the mission packet. Lane 05 owns ongoing adaptation intelligence and cross-user learning. Both drafts are marked "Lane 02 draft; Lane 05 steward".

**AR-06 · Date anomaly · `NON_MATERIAL_REFINEMENT` (noted)**
- `PROJECT_STATE.json` says `last_updated: 2026-09-30`, but this session's clock reads 2026-09-29 UTC. This is probably a timezone difference. State files now use UTC timestamps.

### B. Hidden assumptions

**AR-07 · Users can accurately report their tasks and time · `NON_MATERIAL_REFINEMENT` (in Diagnostic Architecture)**
- Self-reports of time use and of "judgment" are noisy, and people tend to overstate how much judgment their own work needs.
- *Resolution:* Use concrete recall ("last week, what did you produce?") and behavioral proxies. For example: "Could you write instructions someone else could follow?" is a proxy for repeatability. "Who notices if it goes wrong?" is a proxy for accountability. Engine-inferred values are flagged with source and confidence. A `time_audit` experiment archetype exists to verify the map when it matters.

**AR-08 · Experiments may break employer AI and confidentiality policies · `MATERIAL_CHANGE_PROPOSAL` (conservative default applied to drafts now)**
- The most natural experiment is "try AI on a real task". For an accountant, designer or salesperson, that often means putting client or employer data into a third-party tool. This can breach contracts, regulations or policy, and it could cause real harm. Nothing in the current rules prevents it.
- *Proposal (new CURRENT decision):* KTA never recommends entering confidential employer or client data into tools the employer has not approved. Experiments default to public, synthetic or fully redacted material. `employer_ai_policy` is a required intake field; if it is unknown, the first experiment must not touch work data, and a `policy_check` step is added. The drafts apply this default now because it only restricts. Ratification makes it a registered rule.
- *Affected:* Lanes 02, 05, 06, 07; public promises.

**AR-09 · The first mission assumes a threat framing · `NON_MATERIAL_REFINEMENT` (internal archetypes only)**
- "Stay Valuable…" presumes a defensive goal. Real users may want to *protect* their position, *leverage* AI for advancement, *transition* to another role, or simply *clarify* whether to worry at all.
- *Resolution:* Internal `goal_archetype` field inside the same mission. This does not change DEC-003. Whether the public mission name should change is evidence-pending; see AR-23.

### C. Missing components

**AR-10 · The Blueprint data objects miss the Lane 02 core · `MATERIAL_CHANGE_PROPOSAL` (Blueprint propagation)**
- The Blueprint lists UserProfile, Goal, Mission, EvidenceClaim, ActionExperiment and Outcome. It has no TaskMap, even though the Blueprint's own build priority names one. It also has no Uncertainty/ResearchQuestion, CheckIn/FeedbackRecord, or decision record for adaptations. The architecture diagram shows Personalization as a stage (AR-04).
- *Proposal:* When the Lane 02 handoff is approved, reconcile the Blueprint:
  - add `TaskMap`, `UncertaintyItem` (which includes ResearchQuestion), `FeedbackRecord` and `AdaptationDecision`;
  - describe Personalization as a property of planning and adaptation;
  - record the Lane 02/05 interface.

  One Blueprint edit, applied once, as the Propagation Rule requires.

**AR-11 · The general-LLM substitution risk is not guarded · `NON_MATERIAL_REFINEMENT` (built into the Lane 02 contract and simulation)** See §2.
- *Resolution inside Lane 02:*
  - Packet invariants: every element must be grounded in user-specific facts; the omission list is mandatory; the first experiment must target an open uncertainty *and* a real task.
  - A **swap test**: a packet fails if its mission or experiment would still fit a different user.
  - A **generic-convergence lint**.
  - A **naive-LLM baseline comparison** in the simulation and the pilot.
  - Schemas use controlled vocabularies (task traits, experiment archetypes, blocker types, outcome grades) so outcomes can be aggregated across users later. That aggregation is the defensible asset.

**AR-12 · No scope or safety triage · `NON_MATERIAL_REFINEMENT` (implements the approved V0 scope)**
- Some people who arrive will be in acute situations: just laid off with a financial emergency, in an employment or legal dispute, or in psychological distress. A mission packet is the wrong response for them.
- *Resolution:* Diagnostic stage D0 runs a light scope check. The outcomes are: in scope; in scope with operator attention; or out of scope, where the person is signposted and gets no mission. The referral wording must be approved before the pilot (see pilot prep).

**AR-13 · No mission exit criteria, no baseline, no harm path · `NON_MATERIAL_REFINEMENT` (in contract and feedback logic)**
- Missing so far: when a mission ends, a baseline to compare feedback against, and a path for experiments that backfire.
- *Resolution:*
  - Exit criteria: goal met; no remaining uncertainty whose answer would change a decision; user opts out; or risk detected.
  - Minimal baseline: the user's own prediction before each experiment, plus a starting confidence rating on the goal.
  - A `harm_report` field in feedback, which triggers the `escalate` decision.

**AR-14 · No operator role or attribution log for the human-assisted V0 · `NON_MATERIAL_REFINEMENT` (in pilot prep)**
- If a human operator quietly improves the packets, pilot success cannot be attributed to the engine.
- *Resolution:* The packet carries an `operator_log` recording each human change and its reason. Pilot analysis compares engine drafts against delivered packets.

### D. Weak interfaces and evidence, trust, privacy and feedback risks

**AR-15 · The North Star metric is easy to satisfy and hard to trust · `MATERIAL_CHANGE_PROPOSAL`**
- *Current (DEC-005, PROVISIONAL):* Meaningful Action Rate is the share of users who receive an intervention, attempt it, and report useful insight or improvement.
- *Problems:*
  - Self-report inflation, which is worse when a human operator is in the loop.
  - "Useful insight" is a low bar that a generic chatbot also clears.
  - It does not record whether something was actually *observed*.
  - It has no guardrail against burden or harm.
- *Proposal:* Keep MAR as the North Star with an **operational definition**. An experiment counts only if it was attempted **and** the check-in records a specific observation graded E2 or higher (E3 measured, E2 specific qualitative; see Feedback Logic) **and** the user names a decision or behavior it changed or confirmed. Add three pilot diagnostics that are not North Star:
  - **Attention Cost**: minutes per mission cycle.
  - **Harm/Regret reports**.
  - **LLM-Baseline Preference**: the user compares the KTA packet with a generic LLM answer to the same goal.
- *Affected:* DEC-005, Lanes 05 and 07.

**AR-16 · The Lane 02 ↔ Lane 03 evidence interface is undefined · `NON_MATERIAL_REFINEMENT` (Lane 02 side only)**
- *Resolution:* A `world_fact` ledger entry carries its research spec:
  - the question;
  - which mission elements depend on it;
  - whether it is blocking;
  - the required evidence strength;
  - the freshness need;
  - what each plausible answer would change.

  Until Lane 03 returns an EvidenceClaim, a dependent element can only be shown as a labeled hypothesis. Lane 03 owns the EvidenceClaim schema.

**AR-17 · The first experiment could rest on unverified claims · `NON_MATERIAL_REFINEMENT` (planner rule)**
- *Resolution:* "Evidence Before Recommendation" applies to the first experiment too. Its rationale and its safety must not depend on unverified `world_fact` items. It should reduce a `personal_empirical` uncertainty, because personal evidence doesn't need external verification to be valid for the user's own decisions. It is still labeled n=1 and is never generalized.

**AR-18 · Privacy: task maps are employment-sensitive · `NON_MATERIAL_REFINEMENT` (in schemas)**
- *Resolution:*
  - Never collect employer, client or colleague names, or pay, unless a specific downstream use exists.
  - Each field carries a `sensitivity` tag.
  - Tasks carry a `data_sensitivity` value that constrains experiments.
  - Pilot retention and consent terms are drafted in pilot prep and **need owner approval before use**, because they are external promises.

**AR-19 · Feedback validity · `NON_MATERIAL_REFINEMENT` (in Feedback Logic)**
- The risks are demand effects, recall bias, and treating completion as success.
- *Resolution:*
  - Ask neutral questions before evaluative ones.
  - The user writes a prediction before acting, and it is compared with the result.
  - Every experiment needs at least one observable measure.
  - Feedback evidence is graded E0–E3, and weak evidence carries less weight in adaptation.
  - A "no effect" result counts as valid learning.
  - Two "not attempted" results in a row trigger re-diagnosis, not more pushing.

### E. Unnecessary complexity and premature commitments

**AR-20 · Heavy structure for a human-assisted V0 · `NON_MATERIAL_REFINEMENT` (interpretation)**
- The 11-stage architecture and the 14-dimension task rating would be a large burden for both the user and the operator.
- *Resolution:*
  - Treat the architecture stages as **logical functions, not services**. In V0, Research, Evidence and Explanation are operator activities with checklists.
  - The user supplies only task name, output, frequency, rough time share and friction. The engine or operator infers the other dimensions and flags them. The user confirms only the ones that would change the plan.
  - "Personal Relevance Map" is a derived view over per-element `relevance` fields, not a separately authored section.

### F. Examined, no change now

**AR-21 · Core thesis, core loop, principles, V0 exclusions · `NO_CHANGE_NEEDED`.** They are coherent and specific enough to build against.

**AR-22 · Task-based rather than job-title analysis · `NO_CHANGE_NEEDED`.** It matches the direction of task-level research on technology exposure. Any specific exposure figures are `world_fact` items for Lane 03 and are not asserted in Lane 02.

**AR-23 · Public mission name and first market · `NO_CHANGE_NEEDED` now; evidence-pending.** Record goal-archetype frequency in the pilot. Revisit DEC-002 and DEC-003 with that data.

**AR-24 · Core Promise wording ("will determine what matters") · `NO_CHANGE_NEEDED` now; flagged for Lane 07.** It slightly overclaims certainty compared with the "explicit uncertainty" principle. Revisit before any public copy.

**AR-25 · Reuse opportunity: Truthcast · `NO_CHANGE_NEEDED` (parking candidate).** The same repository contains Truthcast, a separate project. It does claim extraction, evidence research and a mechanical "bar" that removes weak claims. That is close to the Lane 03 Evidence Engine and Trust Layer. Proposed Parking Lot entry: revisit when Lane 03 specification starts.

## 4. Non-material refinements implemented in this pass

1. `CLAUDE.md`: authority clarification (AR-02) and repo-location note.
2. Repo-root `CLAUDE.md`: routes new sessions to `KTA/CLAUDE.md`, so a phone "Read CLAUDE.md and resume" works.
3. `04_REGISTRIES/KTA_REGISTRIES_v0.1_RENDERED.md`: a plain-text rendering of the XLSX for diffing and phone reading. The XLSX stays authoritative.
4. `KTA/README.md`: note that `CHECKSUMS_SHA256.json` certifies the *as-received* handover. Git history now tracks integrity.
5. State files now use UTC timestamps (AR-06).
6. AR-03, 04, 05, 07, 09, 11, 12, 13, 14, 16, 17, 18, 19 and 20 are implemented inside the Lane 02 drafts as they are written.

## 5. Does anything block Lane 02?

No. All four MCPs can wait:
- **AR-08** is applied now as a restrictive default.
- **AR-10** is propagation work to apply at the Lane 02 handoff.
- **AR-15** affects only pilot metrics (build step 9).
- **AR-01** affects storage, not product design.

Lane 02 proceeds under the current rules.
