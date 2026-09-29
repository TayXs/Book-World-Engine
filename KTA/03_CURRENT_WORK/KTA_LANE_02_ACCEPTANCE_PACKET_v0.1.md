# KTA LANE 02 ACCEPTANCE PACKET v0.1
Owner checkpoint · 2026-09-29 · Status: **AWAITING OWNER ACCEPTANCE**
Nothing in §7 has been applied. All authoritative files are unchanged.

---

## 0. Read this first (2 min)
- **Recommendation:** ACCEPT WITH SPECIFIED REPAIRS (§9). There are 5 small, non-material repairs.
- **New defect found while preparing this packet:** FM-23, "no effect" vs "not enough data" (§5, repair R1).
- **Main limitation:** every test so far is closed-loop, because one process wrote the rules, the test users and the checker. A blind evaluation on unseen cases is proposed before any real humans (§6).
- **Your reply:** six decisions, D1–D6 (§8). Defaults: `D1A D2A D3A D4A D5A D6A`

---

## 1. What Lane 02 now does

### In plain language
A person arrives worried or curious about how AI will change their work. KTA does not answer the question they ask directly. It:
1. checks that this is the right place for them (scope and safety);
2. finds out what they are actually trying to change (their goal);
3. maps what they *actually do*, task by task, rather than their job title;
4. lists what is *unknown* and who can resolve each unknown: the user, a small real-world test, research, or an explanation;
5. chooses 1–3 areas to focus on, and states what to **set aside**;
6. designs one small, safe test on the person's own work. They write down a prediction before they start;
7. checks in, grades the evidence, and adapts the next step using rules agreed in advance.

### End-to-end flow
```
Messy goal ("Will AI take my job?")
   │
   ▼  D0 scope check ── acute? ──► signpost only, no mission
   │
   ▼  Intake (~14 min, 11 core questions)
   │   goal · role · last week's tasks · time split
   │   · AI use · work-material rules · time budget
   │
   ▼  Task Map (tasks + 0–3 traits, no risk scores)
   │
   ▼  Uncertainty Ledger (each unknown → who resolves it)
   │   ask user │ experiment │ research │ explain
   │
   ▼  Mission Planner (20 rules)
   │   focus 1–3 · sequence · OMISSIONS · exit criteria
   │
   ▼  First ActionExperiment
   │   hypothesis · user's prediction · measures
   │   · safe materials · pre-agreed branches
   │
   ▼  Checker (15 invariants) → operator review → deliver (≤10 min read)
   │
   ▼  Check-in (12 questions, neutral first)
   │   evidence graded E0–E3
   │
   ▼  Decision table (A1–A18) → revised packet r2 → loop
```

---

## 2. Final architecture
| Component | What it is | File |
|---|---|---|
| **Output Contract** | The Mission Packet: one JSON document per user per revision. It maps to the 10 required capabilities and has 15 invariants. | `MISSION_GENERATION_OUTPUT_CONTRACT_v0.1.md`, `schemas/mission_packet` |
| **Diagnostic Architecture** | Questions derived backward from the packet. 11 core cards plus 3 conditional ones. Each card has a "change test". D0 scope triage. Follow-ups are gated on their value. | `DIAGNOSTIC_ARCHITECTURE_v0.1.md`, `diagnostic_question_registry_v0.1.json` |
| **Task Map** | Output-anchored tasks. 11 traits on a 0–3 scale, each with a source and a confidence. Beliefs about future value are hypotheses. **No automation-risk scores.** | `TASK_MAP_SCHEMA_v0.1.md` |
| **Mission Planner** | 20 rules (MPR-01..20), each tagged as selection, sequencing, omission or adaptation. Precedence: safety > scope > evidence > identity > budget. | `MISSION_PLANNER_RULES_v0.1.md` |
| **ActionExperiment** | A pre-registered, measurable, safe test with branches written in advance. Library of 9 archetypes. | `ACTION_EXPERIMENT_SCHEMA_v0.1.md` |
| **Feedback & Adaptation** | Check-in questions CQ-v0.1, evidence grades E0–E3, blocker vocabulary, decision table A1–A18, revision packets. | `FEEDBACK_ADAPTATION_LOGIC_v0.1.md` |
| **Checker** | Validates the schemas, invariants INV-01..15, planner warnings, decision-table consistency, the revision chain and registry traceability. Also runs the generic-advice lint and a swap-test aid. **27 mutation tests.** | `tools/kta_check.py`, `tools/test_kta_check.py` |

The central idea is the **Uncertainty Ledger.** A general LLM answers every unknown from its own training. KTA routes each unknown to whoever can actually resolve it, and it treats the user's own real-world observation as evidence.

---

## 3. Invariants
### 3a. CURRENT-rule candidates (behavioral; they should hold whatever the pilot shows)
| ID | Rule | Enforced by |
|---|---|---|
| B-01 | Scope triage comes first. People in acute situations get a signpost and no mission. | INV-01, MPR-02 |
| B-02 | **Confidential-information boundary** (the principle is proposed as CORE; see §8 D2) | INV-08, INV-16 (R2) |
| B-03 | No automation-risk scores or replacement odds. Lane 02 describes work; Lane 03 judges claims. | INV-10 |
| B-04 | Unverified world facts are shown only as hypotheses. The first experiment never depends on them. | INV-06, MPR-12 |
| B-05 | Every element is grounded in facts about this user. A plan that would fit anyone fails. | INV-03, AT-1, AT-2 |
| B-06 | Omission is mandatory: every plan says what to set aside and when to revisit it, and the user sees it. | INV-04, MPR-15 |
| B-07 | Each unknown is routed to the party that can resolve it. | INV-09, MPR-11 |
| B-08 | Experiments are pre-registered and observable: the user's prediction comes first, there is at least one measure that isn't a rating, and branches cover "not attempted" and "null". | INV-05, 12, 14 |
| B-09 | Attention budget: the plan fits the user's stated time and reads in ≤10 minutes. | INV-07, MPR-17 |
| B-10 | Harm first: any harm report escalates and overrides every other rule. | A1, INV-13 |
| B-11 | No pushing: a decline is respected, and two non-attempts in a row lead to a rediagnosis or an offer to stop. | A5, A18 |
| B-12 | Identity protection: tasks the user values are never targeted for automation without their opt-in. | MPR-08 |
| B-13 | Traceability: every revision links to its parent and to the decision that produced it. Nothing is overwritten. | INV-11 |
| B-14 | n=1 evidence stays personal. This applies the existing **CORE** Evidence Rule. | Feedback §8 |

### 3b. PROVISIONAL implementation rules (tunable after evidence)
- Intake size: 11 cards, ≤15 min, ≤5 follow-ups.
- 11 traits on a 0–3 scale.
- 1–3 focus areas and 2–6 steps.
- Lexicographic focus ranking.
- The leverage-to-destination pairing rule.
- The 9-archetype library.
- Experiment limits: ≤90 min, a window of ≤14 days, 9 filters.
- Check-in no later than the window + 3 days.
- The CQ-v0.1 wording.
- Evidence grades E0–E3, with E2 as the threshold for resolving an unknown.
- The thresholds in decision table A1–A18.
- Ledger of ≤10 items.
- INV-15 (thin task map), the light-touch focus rule, micro mode (<30 min/week) and the timing filter.

---

## 4. Simulation results
All cases are fictional, and all packets pass the checker (0 errors, 0 warnings).

**Accountant (SIM-ACC)**
- Archetype: *leverage*.
- Focus: variance-pack drafting (30% of time), plus the ops analysis the user wants more of (the destination for freed time).
- First test: a Copilot vs. usual-way shadow test on **made-up numbers**, because the permitted data scope was unknown.
- Result: 22 vs 38 minutes, with 2 corrections (E3) → *continue*. Revision r2 moves to last month's real section, after IT approved the data scope.

**Graphic designer (SIM-DES)**
- Archetype: *protect*.
- Diagnosis: one bundled project fee hides which part of the work clients value.
- First test: an audit of the user's own past projects, with no tool used, because client contracts restrict AI.
- Result: not attempted, blocker "time" → *simplify* to 3 projects in two 15-minute sittings.

**Sales professional (SIM-SAL)**
- Archetype: *transition* (to enterprise AE).
- The AI-SDR worry was set aside, because it concerns outbound work this person doesn't do.
- Caught: the user's personal-chatbot email habit conflicts with the company policy they described.
- First test: a tally of enterprise-AE requirements from public job postings.
- Result: mixed → *investigate further*, plus a new research item.

**Low-exposure electrician (SIM-LOW)**
- Archetype: *clarify*. Light-touch, micro mode (20 min/week).
- A 20-minute voice-notes test on a made-up job.
- The worry about AI replacing hands-on work becomes an omission with a watch trigger.

**Out of scope (SIM-OOS)**
- Laid off, rent due, not sleeping → signpost only. No task map and no mission.

**Where the missions materially differed:**
- **What was unknown:** tool capability for this user (accountant), the economics of the work (designer), the gap to a target role (sales), or whether to worry at all (electrician).
- **Test type and data:** shadow test on synthetic data, an audit with no tool, a probe of public data, and a synthetic-job test.
- **Safety gate:** data scope unknown, contracts restrict, tools approved, no policy known.
- **Omissions came from each user's own words:** the IT webinar, the website rebuild, the sales certification, and the hands-on worry.
- **Check-in paths:** continue, simplify, and investigate further.

---

## 5. Failure-mode findings
**Fixed (15):**
- FM-01: a revision broke history links → history exception added.
- FM-03: a transition focus was not accepted as a destination for freed time → rule widened.
- FM-04: the light-touch rule picked the wrong task → now picks the most predictable task that isn't identity-protected.
- FM-05: clarify's explain-first step came before research → now uses user-local facts only.
- FM-06: the generic-advice lint gave a false positive → narrowed.
- FM-07: a time constraint clashed with when the task happens → timing filter plus a retrospective variant.
- FM-08: `data_class` was ambiguous → defined.
- FM-09: "tool approved, but for which data?" → treated as unknown until confirmed.
- FM-10: for freelancers, the rules come from clients → wording fixed.
- FM-11: a policy conflict in a current habit was missed → cross-check rule added.
- FM-13: the operator caught an engine miss every time → checklist item added.
- FM-18: a thin task map made a valid packet impossible → INV-15.
- FM-19: a prohibitive policy was unhandled → rule added.
- FM-20: "rediagnose" was undefined → mini-protocol added.
- FM-22: a decline couldn't be recorded → `declined` status and rule A18.

**Merged (1):** FM-02 → FM-01.

**Unresolved (6), and why:**
| ID | Issue | Why it's still open |
|---|---|---|
| FM-12 | "Less looks like less": a generic answer has more bullets | Needs evidence of real user preference, plus Lane 04 presentation work |
| FM-14 | An audit-first test may feel like homework | Needs attempt-rate evidence |
| FM-15 | Research load on the operator | Needs a Lane 03 reuse cache and a capacity plan |
| FM-16 | No contrast set outside the simulation | Proposed (the simulated users), but not yet independent |
| FM-17 | Author bias | Can only be tested with unseen cases (§6) |
| FM-21 | Escalation playbook | Drafted but untested. The signpost wording needs your approval. |

**New in this review (1):**
- **FM-23:** rule A16 treats "measured, no effect" (informative) the same as "too little data" (inconclusive). Two fixtures mislabel inconclusive results as null (SIM-DES B4, SIM-SAL B4). SIM-LOW's null → stop branch contradicts A16's "modify". → **Repair R1.**

**Honest note:** stress traces ST-1..5 were paper exercises. Only INV-15, A5 and A18 have regression tests. Repair R5 turns the rest into fixtures.

---

## 6. Validation limitations and the proposed blind evaluation
### The closed loop
One development process, in one session, wrote the rules, the simulated users, the packets, the checker and the tests. As a result:
- The fixtures pass **by construction**. They were written knowing the rules.
- The checker proves that the specs are **internally consistent**, not that the plans are **good**. A packet can pass all 15 invariants and still be a poor plan.
- The mutation tests catch only the violations their author thought of.
- The simulated intakes are clean, cooperative and articulate.
- The naive-LLM baselines were *described*, not captured.
- **No engine exists yet.** Packets were written by hand following the rules. Whether an LLM given the specs produces good packets has not been tested.

### Proposed stage: Blind/Adversarial Evaluation (BAE, proposed EXP-V0-00)
| Item | Proposal |
|---|---|
| Cases | 16 unseen cases, written **without access to the specs**. Split into 6 *dev* cases (used for repairs) and 10 *sealed test* cases (opened only for the final run). |
| Case mix | Messy or contradictory intake; a user who volunteers confidential data; a user who asks for risk scores; prohibited policy; freelancer contracts; non-desk work (nurse, warehouse); a manager; someone between jobs; a subtle acute case; a low-engagement user who refuses; highly exposed work (translator, copywriter); an AI-expert user; a stated goal that is wrong; plain-language or low-literacy phrasing. |
| Freeze | Cases are sealed **before** the drafting prompt is final. The prompt is version-frozen before the test run. The builder never edits cases. |
| Baselines | For every case, capture the verbatim answers of 2 general assistants to the same goal. |
| Review | An independent reviewer (you, and/or a separate AI session with no spec access) scores **blind**, with the source labels removed. Rubric: grounding, omission quality, experiment safety, evidence discipline, actionability, attention cost, and preference versus the baselines. |
| Red team | Adversarial intakes that try to break the invariants: "use my client files", "just give me a % risk", injected instructions. |
| Pass bar (proposed) | 0 safety or confidentiality violations · 0 unverified facts shown as fact · ≥80% of packets pass the checker with ≤1 automatic repair · swap-test failures ≤10% · blind reviewer rates KTA more actionable in ≥60% of pairs · generic convergence in ≤1 case |
| After it | Repairs, then a re-run on the sealed cases only once. A second repair round needs fresh cases. |

---

## 7. Proposed authoritative changes (exact diffs; NOT APPLIED)

### 7.1 Data model delta (D3)
| Object | Change | Defined in |
|---|---|---|
| UserProfile | Kept. In V0 it exists only inside a packet's `context`, and no standalone profile is stored (privacy). | Contract §5.4 |
| Goal | Kept. Now `goal`: stated vs diagnosed goal, archetype, horizon, success signals, baseline. | Contract §5.3 |
| Mission | Kept. Implemented as a **versioned Mission Packet**: focus, sequence, omissions, exit criteria, claims, operator log. | Contract |
| **TaskMap** | **New.** Tasks with 0–3 traits, sensitivity and hypotheses. No risk scores. | Task Map spec |
| **UncertaintyItem** | **New.** An entry in the ledger, typed by who resolves it. A ResearchQuestion is a `world_fact` item with a research spec, which is the interface to Lane 03. | Contract §5.6 |
| EvidenceClaim | Kept. Owned by Lane 03. Lane 02 references it only. | Lane 03 (to spec) |
| ActionExperiment | Kept. Now fully specified. | AX spec |
| **FeedbackRecord** | **New.** One check-in, with its evidence grade. | Feedback spec |
| **AdaptationDecision** | **New.** The decision, the rules applied, the ledger changes, and a link to the next revision. | Feedback spec |
| Outcome | Kept as the **aggregate concept** used by metrics. It is derived from FeedbackRecords, AdaptationDecisions and mission exits, not stored separately. | Feedback §9 |

### 7.2 Master Blueprint
```diff
 ### Core Product Principles
-- Privacy by Minimization. Collect only context materially necessary to improve the user’s outcome.
+- Privacy by Minimization. Collect only context materially necessary to improve the user’s outcome.
+- Confidential Information Boundary (CORE). KTA must never require, request or encourage a person to enter confidential employer, client, customer or other organizational information into an AI environment its owner has not approved — including KTA itself. KTA works from abstraction, redaction and the minimum necessary context.

 ### System Architecture
-Goal Intake → Context and Task Mapper → Mission Planner → Research Engine → Evidence Engine → Personalization → Explanation Engine → Action Engine → User Experiment → Feedback Engine → Mission Adaptation.
+Goal Intake (with scope triage) → Context and Task Mapper → Mission Planner (routes each uncertainty to ask / experiment / research / explain) → Research Engine → Evidence Engine → Explanation Engine → Action Engine → User Experiment → Feedback Engine → Mission Adaptation.
+Personalization (selection, sequencing, omission, adaptation) is a property of the Mission Planner and Mission Adaptation, not a separate stage. In V0 these are logical functions performed by an operator with LLM assistance, not separate services. Lane 02 owns the first ActionExperiment and check-in interface; Lane 05 owns ongoing adaptation and cross-user intervention intelligence.

 ### Current Data Objects
-UserProfile. Goal. Mission. EvidenceClaim. ActionExperiment. Outcome.
+UserProfile (within the mission context). Goal. Mission (versioned Mission Packet). TaskMap. UncertaintyItem (incl. ResearchQuestion). EvidenceClaim. ActionExperiment. FeedbackRecord. AdaptationDecision. Outcome (aggregate, derived from FeedbackRecords, AdaptationDecisions and mission exits).

 ### Current North Star
-Meaningful Action Rate: the share of users who receive an intervention, attempt it, and report that it produced useful insight or improvement. This metric is provisional until pilot evidence supports or replaces it.
+PROVISIONAL, under V0 evaluation — not locked. Candidate: Decision-Useful Action Rate (definition in DEC-005 as amended). Meaningful Action Rate is retained as a comparison metric until the V0 decision gate. Supporting metrics: attempt, completion, decline, evidence quality, usefulness, trust, mission progress, real-world decision change; guardrails: harm/regret and attention cost.

 ### Current Development Stage
-Pre-V0 product definition and governance setup.
+Pre-V0. Lane 02 Mission Generation Engine v0.1 accepted with specified repairs (<acceptance date>).

 ### Current Build Priority
-Mission Generation Engine v0.1: intake → Task Map → Mission Planner → first ActionExperiment → check-in criteria.
+V0 readiness: Lane 02 repairs → engine drafting prompt → blind/adversarial evaluation on unseen cases → repairs → small human-assisted pilot → decision gate before application development.
```

### 7.3 Current State
```diff
 ### Stage
-Pre-V0 product definition. Lane 02 Mission Generation Engine v0.1 is specified in draft (all 9 build steps, 2026-09-29) and awaits owner acceptance.
+Pre-V0. Lane 02 v0.1 accepted with specified repairs (<date>).

 ### Current Objective
-Build Mission Generation Engine v0.1.
+V0 readiness (repairs → drafting prompt → blind evaluation → pilot).

 ### Current Build Area
-Diagnostic intake → Task Map → Mission Planner → first ActionExperiment → check-in criteria.
+Lane 02 repairs R1–R5; engine drafting prompt; blind/adversarial evaluation (EXP-V0-00).

 ### Approved Governance
 - KTA-GOV-001 — Structured Project Governance.
-- KTA-GOV-002 — Chat Independence & Continuity.
-- KTA-GOV-003 — External Source of Truth using Google Drive.
+- KTA-GOV-002 — Session Independence & Continuity (amended, KTA-004).
+- KTA-GOV-003 — Dual-Layer Source of Truth: Git workspace + Drive governance/release mirror (amended, KTA-004).
+- DEC-007 — Confidential Information Boundary (CORE).

 ### Current North Star
-Meaningful Action Rate is provisional pending pilot evidence.
+Decision-Useful Action Rate is the PROVISIONAL candidate under V0 evaluation; Meaningful Action Rate retained for comparison. Not locked.

 ### Pending Material Proposals
-MCP-1 source of truth · MCP-2 data-safety rule · MCP-3 Blueprint reconciliation · MCP-4 North Star definition. None of them has been applied.
+None.

 ### Recovery Instruction
-When a new chat replaces an old one, read this Current State document first, then the Master Blueprint, then the latest relevant lane handoff and Registry entries before continuing work.
+When a new AI session replaces an old one, read this Current State document first, then the Master Blueprint, then the latest relevant lane handoff and Registry entries. In the Git workspace, also read 02_STATE/PROJECT_STATE.json, PROGRESS.md and NEXT_ACTION.md. If the Git workspace and the latest Drive release disagree, apply the sync rule in the Constitution.
```

### 7.4 Governance: Constitution (D1), MATERIAL_CHANGE_PROPOSAL
```diff
 ### Chat Independence Rule
-No material project knowledge may depend on a single ChatGPT conversation. When a working chat ends or reaches a limit, a replacement chat resumes from authoritative project artifacts rather than reconstructing the project from memory.
+### Session Independence Rule
+No material project knowledge may depend on a single AI conversation or session, in any tool. When a working session ends or reaches a limit, a replacement session resumes from authoritative project artifacts rather than reconstructing the project from memory.

 ### External Source of Truth Rule
-Google Drive is the durable external repository for authoritative Knowledge → Action project state. ChatGPT memory and conversation history assist development but do not independently establish product authority.
+### Dual-Layer Source of Truth Rule
+1. The Git repository (TayXs/Book-World-Engine, folder KTA/) is the canonical active development workspace for code, schemas, tests, specifications, working artifacts and operational state files.
+2. Google Drive is the canonical governance and release mirror and the independent recovery layer. It holds, for every accepted milestone, the approved Master Blueprint, Current State, Registries, accepted handoff and a portable release bundle.
+3. A release is an owner-accepted milestone with a release ID (KTA-REL-x.y). It exists as a Git tag and as a Drive release folder containing the same bundle, verified by a SHA-256 manifest.
+4. Synchronization: at every accepted milestone, update the approved governance files in Git, build the release bundle, tag it, publish the bundle and the governance files to Drive, verify the hashes, and record the release in the Change Registry.
+5. Conflict resolution:
+   a. Working artifacts (code, schemas, tests, drafts): Git wins. Drive copies are snapshots.
+   b. Governance files (Constitution, Blueprint, Current State, Registries): the latest Drive release is authoritative for approved state. A Git difference is valid only if it is backed by a registered, owner-approved change not yet released; otherwise it is moved to a proposal and Git is restored to the release.
+   c. An owner edit made directly in Drive is an owner-authored change. It must be imported into Git and registered at the start of the next session, before other work.
+   d. If the same governance file changed in both places since the last release, stop; present both versions to the owner; do not merge automatically.
+   e. AI memory and conversation history never establish product authority.
+6. Recovery: rebuild Git from the latest Drive release bundle plus the Git remote; rebuild Drive from the latest release tag.

 ### Recovery Protocol
-A replacement chat should read, in order: KTA CURRENT STATE, KTA MASTER BLUEPRINT, the latest relevant lane handoff, and applicable Registry entries. It should then continue from the recorded next task.
+A replacement session should read, in order: KTA CURRENT STATE, KTA MASTER BLUEPRINT, the latest relevant lane handoff, and applicable Registry entries — and, in the Git workspace, the operational state files — then check Git against the latest Drive release per the Dual-Layer rule, and continue from the recorded next task.

 ### Governing Decisions
 - KTA-GOV-001 — Structured Project Governance. Status: CORE.
-- KTA-GOV-002 — Chat Independence & Continuity. Status: CORE.
-- KTA-GOV-003 — External Source of Truth using Google Drive. Status: CORE.
+- KTA-GOV-002 — Session Independence & Continuity. Status: CORE (amended by KTA-004).
+- KTA-GOV-003 — Dual-Layer Source of Truth (Git workspace + Drive governance/release mirror). Status: CORE (amended by KTA-004).
```
The same decision propagates to: `SOURCE_MANIFEST` (adds the release log), `KTA/CLAUDE.md` (adds the sync step at checkpoints and the start-of-session Drive check), and the Lane Map (02 owns the first-experiment and check-in interface, 05 owns ongoing adaptation).

**Practical blocker:** the Google Drive connected to this environment cannot see the KTA Drive files. Sync needs either the right Google account connected, or you uploading the bundle Claude builds. This is part of D1.

### 7.5 Registries (rows to add or change)
**Change Registry**
| ID | Change | Status |
|---|---|---|
| KTA-004 | Session independence plus the dual-layer source of truth (§7.4). Amends KTA-002 and KTA-003. | CORE |
| KTA-005 | Blueprint reconciliation: data model, architecture wording, lane interface (§7.1–7.2) | CURRENT |
| KTA-006 | Confidential Information Boundary added to the Blueprint's Core Product Principles | CORE |
| KTA-007 | Release KTA-REL-0.1: Lane 02 v0.1 accepted, with bundle hash and Git tag | CURRENT |

**Decision Registry**
| ID | Decision | Status |
|---|---|---|
| DEC-005 (amend) | North Star: Decision-Useful Action Rate is the candidate under V0 evaluation, not locked. MAR is retained for comparison. The supporting metrics are listed. | PROVISIONAL |
| DEC-007 | Confidential Information Boundary principle | CORE |
| DEC-008 | Lane 02 behavioral invariants B-01..B-14 | CURRENT |
| DEC-009 | Confidential-information implementation rules P1–P7 (see D2) | CURRENT |
| DEC-010 | Lane 02 v0.1 specification and parameters (§3b), accepted with repairs R1–R5 | PROVISIONAL |

**Experiment Registry:** EXP-V0-00 blind evaluation (new) · EXP-V0-01..03 (as proposed before) · EXP-V0-04 evaluation of DUAR vs MAR.
**Parking Lot:** PARK-001..005, as proposed before. PARK-004 (independent review) is absorbed into EXP-V0-00.

---

## 8. Owner decisions

### D1 · Project storage: MATERIAL_CHANGE_PROPOSAL
Your model has been adopted: **Git** is the canonical workspace, and **Drive** is the canonical governance and release mirror and the recovery layer. The exact wording and sync/conflict rule are in §7.4.
- **A** Approve the wording, and connect the Google account that owns the KTA Drive files so Claude can sync *(recommended)*
- **B** Approve the wording; you upload each release bundle manually
- **C** Revise the wording (tell me what to change)

### D2 · Confidential information: classification and propagation
The principle is approved. Proposed classification:
- the **principle** is **CORE** (DEC-007): a trust boundary that doesn't depend on experiments;
- the **rules** are **CURRENT** (DEC-009), because they will evolve.

The rules:
- **P1 Intake abstraction:** ask about functions and outputs, never documents, names, figures or identifiers. The operator redacts anything volunteered *before* any LLM drafting. This is a new **INV-16**, plus a checker lint for identifiers.
- **P2 Materials:** INV-08. Work material goes only into approved tools with a confirmed scope; otherwise public, synthetic or redacted material is used.
- **P3** An unknown scope counts as not approved.
- **P4** A current habit is cross-checked against the rules, without blame.
- **P5** How to handle a prohibitive policy.
- **P6** Real pilot data is never stored in Git.
- **P7** Only controlled-vocabulary fields are aggregated, and only with opt-in.

Propagates to: the Blueprint principle, the Decision Registry, the Contract (INV-08/16), Diagnostic §7/§10, MPR-14, the AX safety fields, the checker, the pilot consent text and the operator runbook.

Note: "…**including KTA itself**" means KTA's own intake runs on abstractions only.
- **A** Approve CORE principle + CURRENT rules, including the KTA-itself scope *(recommended)*
- **B** Make both CURRENT
- **C** Revise

### D3 · Blueprint data model
The delta is in §7.1, and the Blueprint diff is in §7.2. It would be applied only after D5.
- **A** Approve the delta as shown *(recommended)*
- **B** Request changes

### D4 · North Star: evaluation of your candidate
**Your candidate:** "Decision-Useful Action Rate: the percentage of recommended ActionExperiments that users attempt and that produce interpretable evidence or meaningful progress that informs the next mission decision."

**Its strengths:**
- The denominator is *recommended* experiments, so non-attempts count against it.
- It rewards informative null results.
- It measures the loop, which is KTA's differentiator.

**Recommended refinements:**
1. **"Interpretable evidence"** means graded E2 or higher and not *inconclusive*. Null results count. This depends on repair R1.
2. **"Meaningful progress"** means an *observed* change in one of the user's success signals, at E2 or higher. Otherwise "felt useful" slips back in.
3. **"Informs"** means the AdaptationDecision cites that check-in under a result-driven rule (A11, A13–A15, and A16a after R1).
4. The **denominator** includes declined and no-response experiments.
5. Report a **per-user companion** metric: users with ≥1 decision-useful action per cycle.
6. Always pair it with **Real-World Decision Rate**: the user names a work decision or behavior that was changed or confirmed. DUAR measures whether *the system* learns; KTA's goal is a useful result in the user's work.
7. **Anti-gaming:** track the share of experiments that target high-impact unknowns, plus their effort, so trivial tests can't inflate DUAR.
8. **Guardrail:** a serious harm invalidates the cohort's DUAR.

**Supporting metrics:**
- attempt, completion, decline;
- evidence-grade mix;
- usefulness (CQ-11);
- **trust** (a new question, CQ-13: "How much do you trust the reasoning? Was anything shown as fact wrong?");
- **mission progress** (confidence change against the baseline, success signals observed, exits);
- Real-World Decision Rate;
- harm/regret and attention cost;
- LLM-baseline preference (pilot);
- operator change rate.

On the simulation, as an illustration only: DUAR = 2 of 3 check-ins (accountant yes, sales yes, designer no).
- **A** Adopt the refined DUAR as the PROVISIONAL candidate, keep MAR for comparison, and decide at the V0 gate *(recommended)*
- **B** Adopt your wording unchanged, as the PROVISIONAL candidate
- **C** Track both, with no primary metric

### D5 · Lane 02 acceptance
- **A** ACCEPT WITH SPECIFIED REPAIRS R1–R5 *(recommended)*
- **B** Accept as-is
- **C** Not yet

### D6 · Who writes the unseen cases for the blind evaluation
- **A** You write 3–5 seed cases; a separate AI session **with no spec access** writes the rest and a third session reviews blind *(recommended; this needs your authorization for those sessions)*
- **B** Only separate AI sessions
- **C** You and a human colleague

**Reply:** `D1A D2A D3A D4A D5A D6A`, or change any letter.

---

## 9. Acceptance recommendation: **ACCEPT WITH SPECIFIED REPAIRS**
**Why accept:**
- The Lane 02 brief is fully covered: 9 of 9 deliverables.
- The specs are internally consistent and machine-checked.
- The simulation pass condition is met with no generic convergence.
- The failure-mode process worked: 22 found, 15 fixed.
- The remaining uncertainty can only be reduced by the next stages (drafting prompt, blind evaluation, pilot). Those stages need a frozen, accepted baseline.

**Why not "as-is":**
- one confirmed spec defect (FM-23);
- the approved privacy principle is not yet implemented at KTA's own intake;
- the metric data for D4 (trust, progress) isn't captured yet;
- the stress traces are not regression-tested.

**Specified repairs** (all non-material; to be done before the drafting prompt):
- **R1** Split `null_result` (measured, no effect) from a new `inconclusive` result class. Split A16 into A16a (null → follow the branch) and A16b (inconclusive → fix the measurement). Relabel SIM-DES B4 and SIM-SAL B4. Update the schemas, the checker and the tests.
- **R2** Add INV-16, intake abstraction and operator redaction, plus an identifier lint (after D2).
- **R3** Add CQ-13 (trust) and mission-progress fields to the FeedbackRecord (for D4).
- **R4** Add `tools/kta_metrics.py`, which computes DUAR, MAR and the supporting metrics from records.
- **R5** Turn stress traces ST-1..5 into fixtures and regression tests.

---

## 10. Post-acceptance sequence
1. **Apply the approved changes.** Blueprint, Current State, registries and governance, with propagation. Release **KTA-REL-0.1** (Git tag + Drive bundle).
2. **Repairs R1–R5.** Checker and tests green.
3. **Seal the unseen cases** (D6) *before* the prompt is finalized, with a dev/test split.
4. **Drafting/compiler prompt**: intake notes → `packet_r1.engine.json` → checker → automatic repair loop. Iterate on the simulation and the *dev* cases only. Then freeze and version it.
5. **Blind/adversarial evaluation** on the sealed test cases, with captured LLM baselines and blind review (EXP-V0-00).
6. **Repairs** from the evaluation. Re-run once. A second round needs fresh cases.
7. **Pilot readiness:** decision batch 2, consent text, a dry run.
8. **Small real-human V0 pilot**, 6–8 people, human-assisted.
9. **Decision gate before serious app development:** go, revise or rethink (Pilot §9). The North Star is decided here (DUAR vs MAR).
