# FEEDBACK & ADAPTATION LOGIC v0.1
Lane 02: Mission & Diagnostic Engine · Build step 6 of 9 · **Lane 02 draft; Lane 05 steward** (AR-05)

Status: **DRAFT**, authorized Lane 02 work.
Machine form: `schemas/feedback_record.schema.json` and `schemas/adaptation_decision.schema.json`.
Upstream: the ActionExperiment branches and the packet's `feedback_plan`.

---

## 1. Purpose and boundary
This step turns what happened into the next decision. It captures more than whether the experiment was completed:
- what was observed;
- how strong that evidence is;
- what blocked the user;
- what changed in the user's understanding;
- whether anything went wrong.

**Lane 02** owns the first check-in and the rules that produce revision 2 of the packet. **Lane 05** owns the longer-run adaptation intelligence and any learning across users.

## 2. Check-in protocol
| Item | V0 default |
|---|---|
| Nudge | At `nudge_at_days` (mid-window). One line with the prediction and the measure template repeated. |
| Check-in | At `checkin_at_days`, which is ≤ the experiment window + 3 days. |
| Length | ≤ 10 minutes of user time. |
| Channel | Operator message or call. The check-in can be done as a short async form. |
| No response | Reminder at +2 days, then an operator message at +5 days. After that: `attempt_status = no_response`, and decision rule A7 applies. |
| Operator stance | Read the questions as written. Don't signal hope for a particular result. Normalize null results: "Plenty of experiments show nothing; that's useful too." Ask for records before impressions. |

## 3. Question set CQ-v0.1
The order is deliberate: neutral facts first, then comparison, then evaluation. Asking for ratings last reduces demand effects (AR-19).

| # | Question | Field |
|---|---|---|
| CQ-1 | "Did you get to try it: fully, partly, or not yet?" | `attempt_status` |
| CQ-2 | "Walk me through what you actually did." | `actions_taken` |
| CQ-3 | "What did you note down?" (the measure template) | `observations[]` |
| CQ-4 | "Actual time spent, roughly?" | `effort_minutes_actual` |
| CQ-5 | "Before you started you predicted: '<prediction.user>'. How did it compare?" | `prediction_comparison` |
| CQ-6 | "Anything surprise you?" | `surprises` |
| CQ-7 | *(if partly or not yet)* "What got in the way?" | `blockers[]` |
| CQ-8 | "Did anything go wrong or feel uncomfortable, at work, with anyone, or with data?" **(always asked)** | `harm_report` |
| CQ-9 | "What do you now think about <the hypothesis in plain words>?" | `belief_update` |
| CQ-10 | "Has this changed or confirmed anything you'll do or decide?" | `decision_change` |
| CQ-11 | "0–10: how useful was this?" | `usefulness_0_10` |
| CQ-12 | "0–10: how confident are you now that you're on track?" (compared with the baseline) | `goal_confidence_0_10` |

## 4. Evidence grades (E0–E3)
Each observation is graded. The record-level `evidence_grade` is the highest grade among the observations that bear directly on the hypothesis.

| Grade | Meaning | Example | What it can do in adaptation |
|---|---|---|---|
| **E3** | Measured at the time: a number, count or artifact comparison | "Normal way 95 min, assisted 40 min + 20 min edits" | Can **resolve** a `personal_empirical` item |
| **E2** | Specific qualitative observation: a concrete event | "Ops manager replied asking for the freight note every month" | Can **resolve** an item |
| **E1** | General impression | "Seemed quicker" | Can update `current_belief` (confidence ≤ medium). **Cannot resolve.** |
| **E0** | No information | — | No update |

All of this is **n=1 personal evidence**. It is valid for *this* user's plan. It never becomes a general claim (§8).

## 5. Blocker vocabulary
`time` · `forgot` · `access_or_tool` · `policy` · `skill` · `unclear_instructions` · `motivation_or_relevance` · `stakeholder_unavailable` · `circumstances_changed` · `other`

This is a controlled list so that blockers can be aggregated later (AR-11). A free-text note is always allowed as well.

## 6. Adaptation decision table
First, classify the result:
- `result_class` is `confirms`, `disconfirms`, `mixed` or `null_result`, judged against the experiment's `learning_criteria`;
- or `not_applicable` when nothing was attempted.

Then apply the first matching rule, in precedence order.

| Rule | Condition | Decision | What happens |
|---|---|---|---|
| **A1** | Harm reported, any severity above `none` | `escalate` | The operator reviews within 1 business day and stops that line. If the harm was minor and is resolved, the next move is `modify` with an added safeguard. |
| **A2** | A new acute situation appeared (the D0 signals) | `escalate` | Re-run the scope gate (MPR-02). |
| **A3** | The user opts out | `stop` | Record a reason only if the user offers one. |
| **A4** | An exit criterion is met | `stop` | Close the mission, or mark it "done for now" with watch triggers (MPR-19 and MPR-20). |
| **A5** | `not_attempted` or `no_response` for the **second time in a row** | `rediagnose` | Revisit the goal with the user and offer to stop. **Don't keep pushing.** |
| **A6** | `not_attempted`, blocker `time` or `forgot` | `simplify` | Halve the effort or split it into sessions. Allowed once. |
| **A7** | `no_response` (first time) | `simplify` | As A6. The operator also asks whether the timing was wrong. |
| **A8** | `not_attempted`, blocker `access_or_tool` or `policy` | `change_intervention` | Safe material or a different archetype (MPR-14). |
| **A9** | `not_attempted`, blocker `unclear_instructions` | `modify` | Rewrite the steps. This is the engine's fault and is **not counted against the user**. |
| **A10** | `not_attempted`, blocker `motivation_or_relevance` | `rediagnose` | The goal or focus may have been misdiagnosed. Re-run MPR-01 and MPR-09. |
| **A11** | `partly` with ≥ E2 data | *(the class of the data you do have)* | Apply A13–A16 to the partial data, then `modify` for the rest. |
| **A12** | `partly` without E2 data | `simplify` | |
| **A13** | Completed, `confirms`, ≥ E2 | `continue` | Resolve the target item and move to the next step in the sequence. The next experiment targets the next open high-impact item. |
| **A14** | Completed, `disconfirms`, ≥ E2 | `modify` | Update the ledger and the task map, then **re-run MPR-09**; the focus may change. Design a new experiment. |
| **A15** | Completed, `mixed` | `investigate_further` | Split the hypothesis and design a narrower follow-up. If the mixed result points to a world fact, add a research item. |
| **A16** | Completed, `null_result`, **or** only E1 evidence | `modify` | Fix the measurement (add an observable) or simplify. **Never treat this as confirmation.** |
| **A17** | *(runs alongside any rule above)* The feedback raised a new world-fact question | + `investigate_further` on that line | Add a research item. It doesn't block other lines. |
| **A18** | The experiment was **declined** at delivery (FM-22) | `continue` on the explain and research steps | The check-in uses CQ-9, CQ-10 and CQ-12. Offer one smaller experiment. This is an informed choice, **not** a non-attempt, so it doesn't count toward A5. |

**Rediagnose mini-protocol** *(FM-20, used by A5 and A10)*. This is a short conversation of ≤10 min, not a new intake. Three questions:
1. "Is this still the thing you want to change?"
2. "What makes it hard to start?"
3. "Would a different kind of step suit you better: smaller, different, or none for now?"

Then re-run MPR-01 (goal and archetype) and MPR-09 (focus). "None for now" closes the mission with a watch trigger, under the `user_opt_out` exit.

**Escalation** (A1, A2) follows the operator escalation playbook in `V0_PILOT_PREPARATION_v0.1.md` (FM-21).

**How the table relates to the pre-agreed branches.** The branch that matches the result is the default next move. The table *overrides* it only for rules A1 to A5: harm, scope, opt-out, exit, and repeated non-attempt. Any other deviation from the branch is allowed but must be recorded in the AdaptationDecision's `deviation_reason`.

## 7. What changes after a check-in
| Object | Update |
|---|---|
| **FeedbackRecord** `FB..` | Created from CQ-v0.1. |
| **Uncertainty Ledger** | The target items become `resolved` (≥ E2, with a `resolution`). An E1 result updates `current_belief` and the item stays `open`. New items are added from surprises (CQ-6) and new questions (A17). |
| **Task Map** | Audit results replace `time_share` values, with `source: observed`. Traits contradicted by what was observed are updated, with the old value kept in the trait's `note`. |
| **Experiment** | `status` and `status_history` are updated. |
| **AdaptationDecision** `AD..` | Created: the decision, the rules applied, the branch used, any deviation, and a list of the changes. |
| **Packet revision** | A new packet `r(n+1)` with `parent_packet_id` and `decision_ref` (INV-11). The previous packet becomes `superseded`. In a revision, `first_experiment` holds the *current* experiment; see the v0.2 note. |

The user receives a short summary covering what we learned, what changes, and what's next. That summary respects the ≤10-minute reading budget.

## 8. Keeping n=1 evidence personal
- Personal results change only **this user's** plan.
- Learning across users, such as "shadow tests on reporting tasks usually disconfirm for X", is a *hypothesis* for the Lane 08 Experiment Registry. It follows the Constitution's Evidence Rule: observation → hypothesis → experiment → decision. It never goes straight into planner rules.
- The fields that can be aggregated are the controlled-vocabulary ones: archetype, target trait profile, `attempt_status`, blockers, `result_class`, `evidence_grade`, `prediction_comparison`, effort. Free text is not aggregated. Aggregation needs pilot consent.

## 9. Meaningful Action capture
The pilot records everything needed to compute **both** definitions, so the owner can compare them with real data. This does not pre-empt decision MCP-4.

| Definition | An action counts when |
|---|---|
| **Current (DEC-005), literal reading** | `attempt_status ∈ {fully, partly}` **and** (`usefulness_0_10 ≥ 6` **or** `decision_change ∈ {changed, confirmed}`) |
| **Proposed (MCP-4)** | `attempt_status ∈ {fully, partly}` **and** `evidence_grade ∈ {E2, E3}` **and** `decision_change ∈ {changed, confirmed}` |
| Diagnostics (proposed) | Attention Cost = packet reading + `effort_minutes_actual` + `checkin_minutes` · harm reports · LLM-Baseline Preference (pilot only) |

The denominator is every delivered experiment, *including* `no_response`.

## 10. Failure modes this logic guards against
| Risk | Guard |
|---|---|
| Treating completion as success | The result is classified against the learning criteria. A null result goes to A16. |
| The user reports what the operator seems to want | Neutral-first ordering, a pre-registered prediction, and requests for records before ratings. |
| Pushing a user who has disengaged | A5 caps it at two non-attempts, then rediagnose or stop. |
| Engine errors counted as user failure | A9 separates unclear instructions. |
| Harm going unnoticed | CQ-8 is always asked, and A1 has top precedence. |
| One anecdote turning into a rule | §8. |

## v0.2 note
Rename `first_experiment` to `current_experiment` when the contract is next revised. It is left unchanged in v0.1 to keep the Lane 02 brief's terminology.

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. Implements AR-13, AR-15 (capture only) and AR-19. |
| 0.1-rev1 | 2026-09-29 | A18 declined (FM-22); rediagnose mini-protocol (FM-20); escalation playbook pointer (FM-21). |
