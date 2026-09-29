# TASK MAP SCHEMA v0.1
Lane 02: Mission & Diagnostic Engine · Build step 3 of 9

Status: **DRAFT**, authorized Lane 02 work.
Machine form: `schemas/task_map.schema.json`, embedded in the Mission Packet as `task_map`.
Upstream: Output Contract §5.5 and Diagnostic cards DQ-06 to DQ-10.

---

## 1. Purpose and boundary
The Task Map records **what this person actually does**, not their job title. It is the candidate space for every focus area and experiment.

**Evidence boundary.** Lane 02 records *what the user does* and *what the user believes*. It never records how exposed the world makes a task.

| Belongs in the Task Map | Does not belong in the Task Map |
|---|---|
| "Builds the monthly variance pack; ~30% of time; same steps each month" | "This task is 70% automatable" |
| "User believes clients will pay less for resizing work" (`future_value.basis = user_belief`) | "Demand for resizing work is falling" stated as fact |
| "User tried an AI tool on call notes; saved ~10 min but had to fix names" (personal evidence) | Any occupation-level risk score or replacement probability |

Anything that sounds like a claim about the world becomes an `exposure_hypothesis` linked to a `world_fact` uncertainty. Lane 03 checks it (AR-16, INV-10).

## 2. Task fields
| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | `T01`… | R | |
| `name` | string | R | The user's own words. |
| `description` | string | R | What is done, in one or two sentences. |
| `output` | string | R | What is handed over, decided or changed. Tasks are anchored on outputs, not activities. |
| `frequency` | `daily` \| `weekly` \| `monthly` \| `quarterly` \| `ad_hoc` | R | |
| `time_share` | `{band, pct_estimate?, source, confidence}` | R | `band`: `large` (≥25%), `medium` (10–24%), `small` (<10%). A rough % is optional; precision is not claimed. |
| `traits` | object (§3) | R | Every trait value carries `value` (0–3), `source` and `confidence`. |
| `data_sensitivity` | `none` \| `internal` \| `confidential` \| `regulated` | R | Drives experiment safety (INV-08). |
| `stakeholders` | list of enum | — | `internal_manager`, `internal_team`, `client`, `public`, `regulator`, `vendor` or `other`. Never names. |
| `ai_current_use` | `{level, note?}` | R | `level`: `none`, `tried`, `occasional` or `regular`. |
| `future_value` | `{direction, basis, uncertainty_id?}` | — | `direction`: `rising`, `stable`, `declining` or `unclear`. `basis`: `user_belief` or `operator_hypothesis`. **No numbers.** If this field affects the plan, `uncertainty_id` must point to a `world_fact` item. |
| `exposure_hypothesis` | `{statement, uncertainty_id}` | — | A qualitative hypothesis for Lane 03 to test. `uncertainty_id` is required. |
| `evidence_flags` | list of `UQ..` | — | The world-fact questions this task depends on. |
| `confirmed_by_user` | bool | R | Did the user confirm the operator's or engine's summary of this task? |

## 3. Traits: a 0–3 ordinal scale
0 = none or very low · 1 = low · 2 = moderate · 3 = high. Four steps are enough to separate candidates without pretending to be precise.

| Trait | Meaning | 0 | 3 | Primary source |
|---|---|---|---|---|
| `predictability` | Same steps each time | every instance is novel | a fixed recipe | DQ-08a |
| `information_retrieval` | Effort spent finding and gathering information | none | dominant | inferred |
| `analysis_intensity` | Working through data, logic or comparison | none | core of the task | inferred |
| `judgment_intensity` | Decisions under ambiguity that have consequences | none | constant | DQ-08a |
| `relationship_intensity` | Depends on trust, persuasion or reading people | solo | the task *is* the relationship | inferred / DQ-08b |
| `accountability` | Personal answerability for the outcome | none | external consequences (client, regulator, money) | DQ-08b |
| `creativity_synthesis` | Producing something new from many inputs | none | core | inferred |
| `tool_dependency` | Tied to specific systems or tools | none | cannot be done outside them | inferred |
| `autonomy` | The user controls *how* the task is done | fully prescribed | fully the user's call | inferred / DQ-13 |
| `friction` | How painful or tedious the task feels | enjoyable | dreaded | DQ-08c |
| `identity_value` | How much the user values doing it personally | glad to lose | "I'd miss it" | DQ-08c |

*Not traits:*
- `time_share` and `frequency` are structural fields.
- `future_value` is a belief or hypothesis, never a score.
- `evidence_flags` are links to the ledger.

Two traits are not in the Lane 02 brief's candidate list and are added here:
- **`autonomy`**: whether the user can actually experiment on the task.
- **`identity_value`**: the planner must not target a task the user values for automation without the user's say (MPR-08).

The brief's "time burden" is covered by `time_share`, "perceived pain" by `friction`, "future-value relevance" by `future_value`, and "evidence-required flags" by `evidence_flags`.

## 4. How DQ-08 answers map to traits
| Probe answer | Trait values set (source `user_stated`, confidence `medium`) |
|---|---|
| (a) "Yes, easily" | predictability 3, judgment 1 |
| (a) "Mostly, with exceptions" | predictability 2, judgment 2 |
| (a) "No, it depends on reading the situation" | predictability 1, judgment 3 |
| (a) "I couldn't really explain it" | predictability 1, judgment 3, **confidence `low`**. The skill may be tacit or the process may be unclear, so it becomes an uncertainty candidate. |
| (b) "Nobody much / quickly fixed" | accountability 1 |
| (b) "My manager; rework" | accountability 2, add `internal_manager` |
| (b) "A client, regulator or money is affected" | accountability 3, add `client` / `regulator` |
| (c) "Glad to lose it" | identity_value 0, friction 3 |
| (c) "Neutral" | identity_value 1, friction 1–2 (inferred) |
| (c) "I'd miss it" | identity_value 3, friction 0–1 (inferred) |

## 5. Inference rules for traits the user isn't asked about
1. The operator or engine may infer a trait from `description` and `output`. Inferred traits get `source: operator_inferred` or `engine_inferred`, and their confidence is **`medium` at most**.
2. **Confirmation rule.** Some inferred traits are *decisive*: changing the value by 1 would change which focus area or experiment the planner picks. Each decisive inferred trait must either be confirmed by the user (a one-line yes/no in D6) or get an uncertainty item.
3. Inferences are never made from the job title alone. Two accountants can have opposite maps.
4. When the user's statement and an inference conflict, the user's statement wins. The conflict is noted in the trait's `note` and may become an uncertainty item.

## 6. Map-level fields
| Field | Notes |
|---|---|
| `tasks` | 3 to 10 tasks. Fewer than 3 means the intake needs another pass. More than 10 means tasks should be merged by output. |
| `coverage_estimate` | `{band: high\|medium\|low, source}`: how much of the user's work time the listed tasks cover. `low` (under about 50%) creates an uncertainty item and a candidate `time_audit`. |
| `unlisted_work_note` | Optional. What is known to be missing. |
| `map_confidence` | `low`, `medium` or `high`. Set to `low` if the time shares are guesses *and* coverage is not high. |
| `verified_by` | `none`, or the FeedbackRecord ID of a `time_audit` that verified the map. |

## 7. Derived views
These are computed from the map and are **not stored**. The planner uses them.
| View | Rule |
|---|---|
| **Leverage candidates** | time_share ∈ {large, medium} ∧ predictability ≥ 2 ∧ judgment ≤ 2 ∧ autonomy ≥ 2 |
| **Anchor-value candidates** | time_share ∈ {large, medium} ∧ judgment ≥ 2 ∧ (relationship ≥ 2 ∨ accountability ≥ 2) |
| **Identity-protected** | identity_value = 3 |
| **Sensitivity-constrained** | data_sensitivity ∈ {confidential, regulated} (plus `internal` when the policy is unknown) |
| **Fear–size mismatch** | the user's main concern names a task with time_share = small |

## 8. Privacy
- Tasks describe functions and outputs, such as "a key client's monthly report". They never name a client, employer or colleague.
- `data_sensitivity` records *what kind* of material a task handles. The material itself is never collected.
- The map belongs to the user's packet. Any cross-user aggregation, in Lane 05 or 08, uses only the controlled-vocabulary fields (traits, bands, enums) and never free text. Aggregating across users needs pilot consent (see pilot prep).

## 9. Example (abridged)
```json
{ "id": "T01", "name": "Month-end variance pack",
  "description": "Pull actuals vs budget from the ERP, explain variances over threshold, send pack to ops managers.",
  "output": "Monthly management pack with variance commentary",
  "frequency": "monthly",
  "time_share": { "band": "large", "pct_estimate": 30, "source": "user_stated", "confidence": "medium" },
  "traits": {
    "predictability": { "value": 2, "source": "user_stated", "confidence": "medium" },
    "judgment_intensity": { "value": 2, "source": "user_stated", "confidence": "medium" },
    "accountability": { "value": 3, "source": "user_stated", "confidence": "medium" },
    "friction": { "value": 2, "source": "user_stated", "confidence": "medium" },
    "identity_value": { "value": 1, "source": "user_stated", "confidence": "medium" },
    "analysis_intensity": { "value": 2, "source": "operator_inferred", "confidence": "medium" }
  },
  "data_sensitivity": "confidential",
  "stakeholders": ["internal_manager"],
  "ai_current_use": { "level": "none" },
  "exposure_hypothesis": { "statement": "Drafting variance commentary from a variance table is within reach of current general AI tools at reviewable quality.", "uncertainty_id": "UQ03" },
  "confirmed_by_user": true }
```
Full maps are in `simulation/`.

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. Adds the `autonomy` and `identity_value` traits. `future_value` is a belief or hypothesis, never a score. |
