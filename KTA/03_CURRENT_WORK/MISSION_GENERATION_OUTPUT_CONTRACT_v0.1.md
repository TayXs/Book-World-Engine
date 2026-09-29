# MISSION GENERATION OUTPUT CONTRACT v0.1
Lane 02: Mission & Diagnostic Engine · Build step 1 of 9

Status: **DRAFT**. Authorized Lane 02 work, not yet owner-accepted. Lane-spec authority (rank 6) applies once the Lane 02 handoff is accepted.
Machine form: `schemas/mission_packet.schema.json` and `schemas/uncertainty_item.schema.json`. The sub-schemas for task map, experiment and feedback are defined in build steps 3, 5 and 6.
Checker: `../tools/kta_check.py`, added in step 7.

---

## 1. Purpose

The **Mission Packet** is the one structured output of the Mission Generation Engine for one user on one mission. Everything downstream works from it:
- Lane 03 researches the packet's research questions.
- Lane 04 explains the packet to the user.
- Lane 05 runs the packet's experiment and check-in.

Every other Lane 02 artifact is derived *backward* from this contract. A diagnostic question exists only if it fills a packet field. A planner rule exists only if it produces a packet decision.

## 2. Design commitments

| # | Commitment | Source rule |
|---|---|---|
| C1 | The packet is the unit of generation, delivery and revision. Revisions are new packets linked to their parent; nothing is overwritten. | KTA-001 traceability |
| C2 | Plain JSON. A human operator, any LLM, or a mix can produce it. | Model Independence |
| C3 | Every element is **grounded**: it points to the user facts that justify it. An element that could fit anyone is invalid. | DEC-004; AR-11 |
| C4 | No world claim appears without an evidence status. Unverified claims are shown only as hypotheses. | Evidence Before Recommendation; AR-16 |
| C5 | Each unknown is routed to the party able to resolve it: user, experiment, research or explanation. | AR-03 |
| C6 | The packet says what is *left out* as well as what is included. | Personalization = selection + omission |
| C7 | The packet collects no more personal data than a downstream field needs. | Privacy by Minimization; AR-18 |

## 3. Lifecycle

```
            ┌──────────── out_of_scope ──▶ (no mission; signpost only)
intake ──▶ draft ──▶ operator_reviewed ──▶ delivered ──▶ active ──▶ check-in
                                                                 │
                         revised packet (revision n+1) ◀─────────┤
                                                                 └──▶ closed
```

`meta.status` takes one of these values: `draft`, `operator_reviewed`, `delivered`, `active`, `superseded`, `closed` or `out_of_scope`. In V0, a packet cannot be `delivered` until it has been `operator_reviewed`.

## 4. Sections and how they map to the 10 required capabilities

| # | Capability (Lane 02 brief) | Packet field | Producer | Consumer |
|---|---|---|---|---|
| — | Metadata | `meta` | engine | all |
| — | Scope and safety triage | `scope_check` | diagnostic stage D0 | operator |
| 1 | Goal Definition | `goal` | diagnostic stage D1 + planner | all |
| 2 | Context and Constraints | `context` | stages D3 and D5 | planner, L05 |
| 3 | Task Map | `task_map` | stage D2 (schema in step 3) | planner, L03 |
| 4 | Known Unknowns | `uncertainty_ledger`, kinds `user_context` and `personal_empirical` | diagnostics + planner | planner, L05 |
| 5 | Knowledge Gaps | `uncertainty_ledger`, kind `understanding_gap` | planner | L04 |
| 6 | Research Questions | `uncertainty_ledger`, kind `world_fact` with its `research` block | planner | **L03** |
| 7 | Mission Architecture | `mission.focus_areas`, `.sequence`, `.omissions`, `.exit_criteria` | planner (step 4) | L04, user |
| 8 | Personal Relevance Map | **Derived view**: the `relevance` object carried by every element | all producers | L04 |
| 9 | First ActionExperiment | `first_experiment` (schema in step 5) | planner | **L05**, user |
| 10 | Feedback Criteria | `feedback_plan` + `first_experiment.branches` | planner (step 6) | **L05** |
| — | Claims shown to the user | `claims` | planner, L03 | L04 |
| — | Human changes (V0) | `operator_log` | operator | pilot analysis |

Capabilities 4 to 6 are views over one ledger, not three hand-written lists (AR-03). Capability 8 is computed from `relevance` fields, not authored separately (AR-20).

## 5. Field specification

The notation follows the schema. Required fields are marked **R**.

### 5.1 `meta` (R)
| Field | Type | Notes |
|---|---|---|
| `contract_version` **R** | `"0.1"` | |
| `packet_id` **R** | `MP-<userref>-r<n>` | |
| `user_ref` **R** | pseudonymous string | Never a real name or email address. |
| `mission_type` **R** | `"stay_valuable_ai_work"` | The only value allowed in V0 (DEC-003). |
| `revision` **R** | integer ≥ 1 | |
| `parent_packet_id` | string | Required when `revision` > 1. |
| `decision_ref` | `AD..` id | Required when `revision` > 1: the AdaptationDecision that produced this revision. |
| `status` **R** | enum (see §3) | |
| `created_at` **R** | ISO-8601 | |
| `generated_by` **R** | `{method: human\|llm\|hybrid, engine_version, model_ref?}` | `model_ref` records which model was used; the design does not depend on it. |

### 5.2 `scope_check` (R)
| Field | Type | Notes |
|---|---|---|
| `result` **R** | `in_scope` \| `in_scope_operator_attention` \| `out_of_scope` | |
| `flags` | list of enum | `acute_job_loss_financial_distress`, `legal_or_employment_dispute`, `psychological_distress`, `not_in_work_or_seeking`, `outside_mission_domain`, `under_18`, `other` |
| `note` | string | For `out_of_scope`: the signpost given. The wording needs owner approval before the pilot. |

If `result = out_of_scope`, the packet **must not** contain `task_map`, `mission` or `first_experiment` (INV-01).

### 5.3 `goal` (R unless out of scope)
| Field | Type | Notes |
|---|---|---|
| `stated_goal` **R** | string | The user's own words. A light paraphrase is acceptable. |
| `diagnosed_goal` **R** | string | One sentence: the change the user is actually trying to make. |
| `divergence_note` | string | Required if the diagnosed goal differs materially from the stated goal. Explains why. |
| `archetype` **R** | `protect` \| `leverage` \| `transition` \| `clarify` | Internal only (AR-09). |
| `horizon_months` **R** | integer 3–36 | |
| `success_signals` **R** | list (≥1) of strings | Things someone could *observe*, not feelings. |
| `baseline` **R** | `{goal_confidence_0_10, main_concern, captured_at}` | The minimum needed to compare against later (AR-13). |

### 5.4 `context` (R unless out of scope)
| Field | Type | Notes |
|---|---|---|
| `role` **R** | `{function, seniority_band, sector_band, employment_type}` | Generic labels only. **No employer, client or colleague names.** |
| `time_budget_minutes_per_week` **R** | integer | What the user can realistically spend on the mission. Caps every plan. |
| `employer_ai_policy` **R** | `{status, approved_tools[], notes}` | `status` is one of `allows_listed_tools`, `restricts`, `prohibits`, `none_known`, `unknown` or `not_applicable`. |
| `ai_experience` **R** | `none` \| `tried` \| `occasional` \| `regular` | |
| `constraints` | list of `{id C.., type, statement, source}` | `type` is one of `time`, `budget`, `policy`, `access`, `skill`, `personal` or `other`. |
| `capabilities` | list of `{id CAP.., statement, source}` | Existing strengths that are relevant to the mission. |
| `preferences` | `{format, notes}` | `format` is one of `text`, `audio`, `checklist` or `mixed`. |
| `provenance` | map from field name to source | Source is one of `user_stated`, `user_confirmed`, `operator_inferred` or `engine_inferred`. |

### 5.5 `task_map` (R unless out of scope)
Defined in `TASK_MAP_SCHEMA_v0.1` (step 3). The packet relies on these properties of it:
- Each task has an ID of the form `T..`.
- Each task has a time share and traits, and each trait carries a source and a confidence.
- There is **no automation-risk score** (INV-10).

### 5.6 `uncertainty_ledger` (R unless out of scope; ≥1 entry)
Each entry is an `UncertaintyItem` (`schemas/uncertainty_item.schema.json`):

| Field | Type | Notes |
|---|---|---|
| `id` **R** | `UQ..` | |
| `statement` **R** | string | The unknown, phrased as a question. |
| `kind` **R** | `user_context` \| `personal_empirical` \| `world_fact` \| `understanding_gap` | Who can resolve it (AR-03). |
| `route` **R** | `ask` \| `experiment` \| `research` \| `explain` \| `defer` | The chosen resolution path. |
| `impact` **R** | `high` \| `medium` \| `low` | Would the answer change the focus, the sequence or the experiment? |
| `blocking` **R** | bool | `true` if some delivered element is only valid once this is resolved. |
| `decision_links` **R** | list of element IDs | The `F..`, `S..`, `AX..` or `CL..` elements whose content depends on the answer. |
| `task_links` | list of `T..` | |
| `current_belief` | `{statement, confidence, basis}` | The working assumption until the item is resolved. |
| `status` **R** | `open` \| `resolved` \| `deferred` \| `dropped` | |
| `resolution` | `{summary, source, ref, date, evidence_grade}` | Required when `resolved`. `evidence_grade` is E0–E3 (defined in step 6). |
| `research` | object | **Required when `kind = world_fact`** (AR-16). See below. |
| `relevance` **R** | Relevance object (§5.11) | |

The allowed routes for each kind:

| Kind | Allowed routes | Normal route |
|---|---|---|
| `user_context` | ask, defer | ask |
| `personal_empirical` | experiment, ask, defer | experiment |
| `world_fact` | research, defer | research |
| `understanding_gap` | explain, defer | explain |

`research` block, which is the Lane 02 → Lane 03 interface:

| Field | Notes |
|---|---|
| `question` **R** | A factual question someone can investigate. Not the user's personal question. |
| `required_strength` **R** | `strong`, `moderate` or `indicative`: what the dependent decision needs. |
| `freshness` **R** | For example `"≤12 months"`. AI capability claims go stale quickly. |
| `preferred_source_types` | For example `primary_study`, `official_statistics`, `vendor_docs_tested`, `practitioner_report`. |
| `answer_changes` **R** | A list (≥1) of `{if, then}`: what each plausible answer would change in the mission. If no answer would change anything, the question should be `defer`red. |
| `evidence_claim_ref` | The EvidenceClaim ID returned by Lane 03. |
| `status` **R** | `queued`, `in_progress`, `answered` or `unanswerable`. |

### 5.7 `mission` (R unless out of scope)
| Field | Type | Notes |
|---|---|---|
| `focus_areas` **R** | 1–3 × `{id F.., title, task_ids[≥1], uncertainty_ids, rationale, priority, relevance}` | *Selection.* Each focus area must be anchored in at least one task. |
| `sequence` **R** | 2–6 × `{id S.., step_type, description, targets[], depends_on[], timebox_days, owner, relevance}` | *Sequencing.* `step_type` is one of `ask`, `experiment`, `research`, `explain` or `decide`. `owner` is `user`, `operator` or `engine`. |
| `omissions` **R** | ≥1 × `{id O.., what, why_omitted, revisit_condition, relevance}` | *Omission.* What the user can safely set aside for now, and when to look at it again. |
| `exit_criteria` **R** | ≥1 × `{type, statement}` | `type` is one of `goal_met`, `no_decision_relevant_uncertainty`, `user_opt_out`, `risk_detected` or `custom`. |
| `attention_budget` **R** | `{user_minutes_planned_total, plan_weeks}` | Must fit within `time_budget_minutes_per_week × plan_weeks` (INV-07). |

### 5.8 `first_experiment` (R unless out of scope)
An `ActionExperiment` (step 5). The contract requires:
- It targets ≥1 **open** uncertainty whose route is `experiment` and ≥1 task.
- It fits within the time budget.
- It passes the safety rules (INV-08).
- It has a user prediction recorded *before* acting.
- It has branches that cover the `not_attempted` and `null_result` cases.

### 5.9 `feedback_plan` (R unless out of scope)
| Field | Notes |
|---|---|
| `checkin_at_days` **R** | ≤ the experiment's `window_days` + 3. |
| `nudge_at_days` | An optional mid-window reminder. In V0 the operator sends it. |
| `channel` **R** | `operator_message`, `email`, `in_app` or `call`. |
| `question_set` **R** | `"CQ-v0.1"`, the standard check-in questions (step 6), plus any `custom_questions`. |
| `mission_triggers` **R** | Mission-level rules, each `{condition, decision}`. At minimum they must cover harm reported → `escalate`, and not attempted twice in a row → `rediagnose`. |

### 5.10 `claims` (R; may be empty)
Every factual or evaluative statement the delivered packet will *show the user* about the world:

| Field | Notes |
|---|---|
| `id` **R** | `CL..` |
| `text` **R** | |
| `claim_type` **R** | `world_fact`, `personal_evidence` or `engine_judgment` |
| `evidence_status` **R** | `verified`, `user_local` or `unverified` |
| `shown_as` **R** | `fact`, `hypothesis` or `judgment` |
| `evidence_ref` / `uncertainty_id` | Links to the EvidenceClaim or the ledger item. |

A `world_fact` that is not `verified` **must** be `shown_as: hypothesis` (INV-06). `personal_evidence` is labeled as applying to this user only (n=1).

### 5.11 The Relevance object (used everywhere)
```json
{ "why_for_this_user": "string, must mention something specific to the user",
  "grounded_in": ["T02", "C01", "goal", "context.employer_ai_policy"] }
```
`grounded_in` needs at least one entry. Valid entries are:
- a task ID;
- a constraint or capability ID;
- `goal` or `goal.<field>`;
- `context.<field>`;
- an uncertainty ID.

Put together, these relevance objects form the **Personal Relevance Map**.

### 5.12 `operator_log` (R in V0; may be empty)
Each entry is `{at, path, change: added|edited|removed|approved, reason}`. This lets pilot analysis tell engine output apart from human improvement (AR-14).

### 5.13 `delivery`
`{format, estimated_user_minutes}`. The user should be able to read a delivered packet in **≤10 minutes** (Minimum Necessary Attention).

## 6. Invariants (machine-checked by `kta_check.py`)

| ID | Rule |
|---|---|
| INV-01 | **Scope.** `out_of_scope` means there is no `task_map`, `mission` or `first_experiment`. Any other result means all three, plus `goal`, `context`, `uncertainty_ledger` and `feedback_plan`, are present. |
| INV-02 | **Reference integrity.** Every ID that is referenced also exists in the packet. IDs are unique. |
| INV-03 | **Grounding.** Every focus area, sequence step, omission, uncertainty and experiment has `relevance.grounded_in` with ≥1 valid reference. Every focus area has ≥1 task. |
| INV-04 | **Omission.** There is at least 1 omission. |
| INV-05 | **Targeting.** There are 1–3 focus areas and exactly one first experiment. The experiment targets ≥1 open uncertainty of route `experiment` and ≥1 task. |
| INV-06 | **Evidence gate.** The experiment's `depends_on` list contains no open `world_fact`. A `world_fact` claim that is not `verified` must be shown as a hypothesis. |
| INV-07 | **Budget.** Experiment effort ≤ `time_budget_minutes_per_week × window_weeks`. Planned attention ≤ `time_budget × plan_weeks`. |
| INV-08 | **Safety** (AR-08). Confidential, regulated or internal work material may be used only if the employer policy is `allows_listed_tools` and the tool is on the approved list. If the policy is `unknown`, material must be `public`, `synthetic`, `redacted_nonconfidential` or `none`. |
| INV-09 | **Ledger hygiene.** Kind and route are compatible. Every `world_fact` has a `research` block. Every open high-impact item is targeted by a sequence step or the experiment, or it is `deferred` with a reason. |
| INV-10 | **Forbidden content.** No `automation_risk`, `risk_score`, `replace_probability` or similar key or percentage. No `employer_name`, `client_name`, `colleague_name` or `salary` fields. |
| INV-11 | **Revision chain.** `revision > 1` requires `parent_packet_id` and `decision_ref`. |
| INV-12 | **Branch coverage.** The experiment's branches include `not_attempted` and `null_result`. |
| INV-13 | **Check-in timing.** `checkin_at_days` ≤ experiment `window_days` + 3. The mission triggers include `escalate` and `rediagnose`. |
| INV-14 | **Pre-registration.** The experiment has a `prediction.user` field. Its value is filled in before the status moves past `accepted`. |

## 7. Differentiation acceptance tests (human- or LLM-judged; see the simulation)

| ID | Test | Fail condition |
|---|---|---|
| AT-1 | **Swap test.** Give this packet's focus areas and experiment to a different simulated user. | They fit the other user just as well. |
| AT-2 | **Generic-convergence lint** (flagged by the machine, judged by a human). | A focus area, step or experiment title is built on generic advice ("learn AI tools", "improve communication", "focus on human skills", "take a course", "upskill", "embrace AI", "stay curious") and is not tied to a named task *and* uncertainty. |
| AT-3 | **Naive-LLM contrast.** Compare with a one-shot answer to "How do I stay valuable as AI changes my work as a <role>?". | Fewer than 3 packet elements are substantively absent from the naive answer. Candidates: a specific omission, a pre-registered prediction on the user's own task, a routed unknown, a policy-safe experiment design, branch rules. |
| AT-4 | **Attention.** | Delivered reading time exceeds 10 minutes. |

## 8. What a packet must never contain
- Automation-risk percentages, replacement probabilities or occupation "scores". Lane 02 describes work; claims about the world belong to Lane 03.
- An external factual claim with no evidence label.
- Names of employers, clients or colleagues, pay details, or any identifiers not needed downstream.
- A list of courses or tools that isn't linked to a specific task and uncertainty.
- More than 3 focus areas or more than 1 active experiment (V0).
- An instruction to put confidential work material into a tool that isn't approved.

## 9. Examples
Complete, validated packets for three simulated users are in `simulation/` (step 7).

## 10. Open items for later steps
- The E0–E3 evidence grades and the check-in question set CQ-v0.1 are defined in step 6.
- The EvidenceClaim schema belongs to Lane 03. Lane 02 relies only on `evidence_claim_ref` and `verified`.
- Explanation formatting belongs to Lane 04. Lane 02 supplies `relevance` and `claims`.

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. Implements review items AR-03, 04, 09, 11, 13, 14, 16, 17, 18 and 20 in the contract. |
