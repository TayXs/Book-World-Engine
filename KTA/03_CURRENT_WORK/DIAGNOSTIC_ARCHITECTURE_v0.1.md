# DIAGNOSTIC QUESTION ARCHITECTURE v0.1
Lane 02: Mission & Diagnostic Engine · Build step 2 of 9

Status: **DRAFT**, authorized Lane 02 work.
Machine form: `diagnostic_question_registry_v0.1.json`. The checker verifies that every question feeds a Mission Packet field and that every required intake field has a question.
Upstream: `MISSION_GENERATION_OUTPUT_CONTRACT_v0.1.md`.

---

## 1. Principle: work backward from the packet
Each question exists only because a Mission Packet field needs it, *and* because different answers would change the packet. Every question card states its **change test**: the answer patterns that would change which focus areas are picked, which experiment is chosen, what the safety constraints are, or the scope decision.

Three consequences:
- If no answer to a question would change anything, the question is removed.
- If a fact can be *derived* (by the planner, or by an operator/engine inference that is flagged for confirmation), we do not ask for it.
- If the user can't answer something reliably, we don't ask harder. It becomes an uncertainty with route `experiment` (for example, a `time_audit`).

## 2. Budget
| Part | Limit |
|---|---|
| Core intake (D0–D5) | ≤ 12 question cards, target ≤ 15 minutes of user time |
| Adaptive follow-ups (D6) | ≤ 5 questions, ≤ 5 minutes |
| Total | ≤ 20 minutes. Anything past that must pay for itself in plan quality, or it is dropped. |

## 3. Stages

```
D0 Scope ─▶ D1 Goal & role ─▶ D2 Work reality ─▶ D3 AI contact & policy ─▶ D4 Concern* ─▶ D5 Constraints
                                                                                                  │
         draft ledger (planner) ◀─────────────────────────────────────────────────────────────────┘
                 │
                 └─▶ D6 Adaptive follow-ups (value-of-information gate) ─▶ packet draft
                                                                           * conditional
```

D0 comes first because a person in acute distress should not be walked through a task inventory. D2 comes before D3 and D4 so that the user describes their work *before* talking about AI fears. That keeps the task map from being colored by anxiety.

## 4. Question cards
The wording below is the canonical *intent*. In V0 the operator may rephrase a question but must not change what it asks or turn it into a leading question.

### D0: Scope and safety
**DQ-01 · What's prompting this now?** (always)
- *Text:* "What's made you want to look at how AI is changing your work, right now?"
- *Feeds:* `scope_check.result`, `scope_check.flags`, `goal.stated_goal`, `goal.archetype` (derived), `goal.baseline.main_concern`.
- *Change test:*
  - Acute signals (job just lost with money pressure, a dispute, distress) → DQ-02.
  - "My company just rolled out tool X" → likely *protect* or *leverage*.
  - "I want to move into…" → *transition*.
  - "Everyone says my job is going away; is that true?" → *clarify*, and an understanding gap is likely.
- *Est:* 90 s.

**DQ-02 · Now-situation check** (only if DQ-01 has acute signals)
- *Text:* "Is this mainly about something happening right now, like losing a job, a dispute at work, or feeling overwhelmed, or about planning ahead?"
- *Feeds:* `scope_check.result`, `scope_check.flags`, `scope_check.note`.
- *Change test:*
  - Acute → `out_of_scope`. The user is signposted and no packet is built.
  - Mixed → `in_scope_operator_attention`.
  - Planning → `in_scope`.
- *Est:* 30 s. Signpost wording needs owner approval before the pilot.

### D1: Goal and role
**DQ-03 · Role, briefly** (always)
- *Text:* "In a sentence: what's your role, roughly how senior, what kind of organization or sector, and are you employed, freelance or something else?"
- *Feeds:* `context.role.*`.
- *Change test:*
  - Employment type changes whose policy applies: employer or clients.
  - Seniority changes whether *visibility* or *delegation* experiments are plausible.
  - The role feeds context only. **It never drives the mission on its own**; tasks do.
- *Est:* 45 s. Do not ask for the employer's name.

**DQ-04 · Future picture** (always)
- *Text:* "Picture yourself [1–3 years] from now and this has gone well. What's different about your work? Roughly when would you want that?"
- *Feeds:* `goal.diagnosed_goal` (derived), `goal.success_signals`, `goal.horizon_months`, `goal.archetype`.
- *Change test:*
  - "Doing the same job with less grind" → leverage, with focus on high-time repeatable tasks.
  - "Moved into X" → transition, with focus on transferable tasks and market research questions.
  - "Not worried anymore" → clarify, with an explanation-first sequence.
- *Est:* 90 s. If the answer is a feeling ("secure"), ask once: "What would you *see* that tells you that?"

**DQ-05 · Baseline confidence** (always)
- *Text:* "From 0 to 10, how confident are you today that you're on track for that?"
- *Feeds:* `goal.baseline.goal_confidence_0_10`.
- *Change test:*
  - ≤3 → start with a clarifying explanation step and a smaller experiment.
  - ≥8 → test the confidence: favor an experiment that could disconfirm it.
- *Est:* 15 s.

### D2: Work reality (task inventory)
**DQ-06 · Last week's outputs** (always)
- *Text:* "Think about last week, or a typical recent week. What were the main things you produced, decided or handled? List 4 to 8 in your own words. It may help to glance at your calendar or sent items; you don't need to share them."
- *Feeds:* `task_map.tasks[].name`, `.description`, `.output`, `.frequency`.
- *Probe for vague items:* "What did you hand over at the end of that?" Use this when someone answers with a job-title word like "accounting" or "design".
- *Change test:* This question defines the whole candidate space for focus areas. Without tasks there is no mission.
- *Est:* 180 s.

**DQ-07 · Time split** (always)
- *Text:* "Roughly how does your time split across those? Big, medium or small chunk is fine, or rough percentages."
- *Feeds:* `task_map.tasks[].time_share`, `task_map.coverage_estimate`.
- *Change test:* Time share is the strongest input to focus selection (MPR-03). If the user says "no idea", that becomes uncertainty UQ(time) with route `experiment` (`time_audit`).
- *Est:* 60 s.

**DQ-08 · Three quick probes per major task** (always; only for big and medium tasks, max 4)
- *Text:*
  - (a) "Could you write instructions that would let a capable newcomer do this to your standard?"
  - (b) "If this went wrong, who would notice, and what would happen?"
  - (c) "Is this a part of the job you'd miss, or be glad to lose?"
- *Feeds:*
  - (a) → `predictability` and `judgment_intensity`. These are behavioral proxies, not self-ratings (AR-07).
  - (b) → `accountability` and `stakeholders`.
  - (c) → `identity_value` and `friction`.
- *Change test:*
  - "Yes, easily" plus big time share → leverage candidate (MPR-04).
  - "No, it depends on reading the client" → anchor-value candidate (MPR-05).
  - "I'd miss it" → the planner must not pick it for automation without the user's say (MPR-08).
- *Est:* 45 s × ≤4.

### D3: AI contact and policy
**DQ-09 · AI so far** (always)
- *Text:* "Have you used any AI tools for any of these tasks? What happened?"
- *Feeds:* `context.ai_experience`, `task_map.tasks[].ai_current_use`, `context.capabilities`, and candidate `personal_empirical` uncertainties.
- *Change test:*
  - Never tried → the first experiment may be a guided shadow test, if policy allows.
  - Tried and it disappointed → probe *why* once. The answer separates "the tool can't do this" (a world fact) from "I haven't learned to use it well" (personal).
  - Regular use → experiments move on to value, visibility or transition.
- *Est:* 60 s.

**DQ-10 · Rules and sensitivity** (always)
- *Text:* "Does your employer, or do your clients, have rules about using AI tools with work material? Which tools, if any, are approved? And which of your main tasks involve confidential client or company information?"
- *Feeds:* `context.employer_ai_policy.status`, `.approved_tools`, `task_map.tasks[].data_sensitivity`.
- *Change test:* This is the safety gate (INV-08).
  - Unknown policy → the experiment uses only public or synthetic material, and a `policy_check` step is added.
  - Approved tools → shadow tests on real material are allowed, using those tools only.
  - Prohibited → no AI experiment touches work material.
- *Est:* 45 s.

### D4: Concern (conditional)
**DQ-11 · The specific worry** (ask only if DQ-01 did not already name a specific concern)
- *Text:* "What concerns you most about AI and your work? As specifically as you can."
- *Feeds:* `goal.baseline.main_concern`, candidate `understanding_gap` items, and omission candidates.
- *Change test:*
  - A concern attached to a *small-time-share* task → omission plus reassurance explanation (MPR-10).
  - A concern about the *whole occupation* → a `world_fact` research question plus an explanation. It does not drive the experiment.
- *Est:* 60 s.

### D5: Constraints
**DQ-12 · Realistic time** (always)
- *Text:* "Over the next month, how much time could you realistically put into this each week?"
- *Feeds:* `context.time_budget_minutes_per_week`.
- *Change test:* This caps experiment effort and the whole plan (INV-07). Under 30 minutes a week → micro-experiments only.
- *Est:* 30 s.

**DQ-13 · Off-limits** (always)
- *Text:* "Is there anything that's off-limits or hard, such as things you can't do at work, money you can't spend, or parts of the job you don't want to change?"
- *Feeds:* `context.constraints[]`.
- *Change test:* Removes candidate experiments or focus areas directly.
- *Est:* 45 s.

**DQ-14 · Format** (optional; defaults to `text`)
- *Text:* "When we send your plan, would you rather read it, listen to it, or get a checklist?"
- *Feeds:* `context.preferences.format`, `delivery.format`.
- *Change test:* Affects delivery only. It may be asked when the plan is delivered instead of during intake.
- *Est:* 10 s.

**Core total:** 11 always-asked cards plus up to 3 conditional ones. The estimate is about 14 minutes with 4 major tasks.

## 5. D6: Adaptive follow-ups (value-of-information gate)
After D5, the engine or operator drafts the Uncertainty Ledger (see the Planner, MPR-11). A follow-up question **FQ** is asked only if **all** of these hold:

1. The item's kind is `user_context`, because the user can plausibly just know the answer.
2. Its impact is `high`, or `medium` when two candidate experiments are otherwise tied.
3. The follow-up card states what each plausible answer would change: the focus area, the experiment choice, or a safety constraint.
4. There is budget left: ≤5 follow-ups and ≤5 minutes.

If any condition fails, the item stays in the ledger:
- as route `experiment`, when observation beats recall;
- as `deferred`, when its impact is low;
- as `research`, when it is really a world fact.

Follow-ups are written for the user in front of us, so they are not fixed questions. They are logged in the packet's `operator_log` with the ledger item they resolved.

**Example (accountant):** "Is the monthly management pack built fresh each month, or is it a template you update?" The answer decides between the two top experiment candidates: template → drafting the variance commentary; fresh build → the data-assembly step.

## 6. Stop rules
Stop asking as soon as any one of these is true:
1. Every required packet field is filled or derivable, and no open `user_context` item is high-impact.
2. The budget is reached.
3. The user shows fatigue or irritation. Stop, and log the remaining unknowns in the ledger.
4. D0 has set the scope to `out_of_scope`.

## 7. Answer-quality rules
| Situation | Handling |
|---|---|
| The answer is a job title ("I do marketing") | Ask for outputs: "What did you hand over last Thursday?" |
| "I don't know" on time or frequency | Don't push. Record `UQ` with kind `personal_empirical` and route `experiment` (a `time_audit` candidate). |
| A self-rating of judgment ("it's all judgment") | Rely on the DQ-08(a) behavioral proxy. Record the inferred trait with source `operator_inferred` and confidence `low`. |
| An answer that reveals identifying data (names, clients) | Do not store it. Keep the function only ("a key client" instead of the name). |
| The user asks "will AI replace me?" during intake | Acknowledge it and park it: "We'll look at that with evidence, not guesses." Log it as a `world_fact` or `understanding_gap`. **Never state exposure claims during intake**, because that colors the answers that follow. |

## 8. Forbidden during intake
- Leading or fear-priming questions, such as "How likely is it that AI replaces you?"
- Asking for the employer, client or colleague names, salary, or performance ratings.
- Long rating grids. The user gives at most three quick probes per task; the rest is inferred and flagged.
- Recommending anything before the packet exists (Diagnose Before Prescribing).

## 9. Traceability matrix (packet field ← source)
| Packet field | Asked in | Derived by |
|---|---|---|
| `scope_check.*` | DQ-01, DQ-02 | |
| `goal.stated_goal` | DQ-01 | |
| `goal.diagnosed_goal`, `.divergence_note` | | Planner MPR-01, from DQ-01, DQ-04, DQ-11 |
| `goal.archetype` | | MPR-01, from DQ-01 and DQ-04 |
| `goal.horizon_months`, `.success_signals` | DQ-04 | |
| `goal.baseline.goal_confidence_0_10` | DQ-05 | |
| `goal.baseline.main_concern` | DQ-01 / DQ-11 | |
| `context.role.*` | DQ-03 | |
| `context.time_budget_minutes_per_week` | DQ-12 | |
| `context.employer_ai_policy.*` | DQ-10 | |
| `context.ai_experience` | DQ-09 | |
| `context.constraints` | DQ-13 | Also from DQ-10 (policy constraints) |
| `context.capabilities` | DQ-09 | Operator inference, flagged |
| `context.preferences` | DQ-14 (optional) | Default `text` |
| `task_map.tasks[]` name, description, output, frequency | DQ-06 | |
| `task_map.tasks[].time_share` | DQ-07 | |
| `task_map.tasks[].traits` (predictability, judgment, accountability, identity, friction) | DQ-08 | Other traits are inferred and flagged (Task Map spec) |
| `task_map.tasks[].data_sensitivity` | DQ-10 | |
| `task_map.tasks[].ai_current_use` | DQ-09 | |
| `uncertainty_ledger` | FQ (D6) resolves `user_context` items | Planner MPR-11 |
| `mission.*`, `first_experiment`, `feedback_plan`, `claims` | | Planner (steps 4–6) |

The checker verifies against the registry JSON that every question card feeds at least one of these fields, and that every always-required intake field has a card or a derivation rule.

## 10. V0 delivery mode
The operator runs the intake as a text or voice conversation, or as an async form followed by one operator follow-up. Answers are summarized directly into packet fields. **Verbatim transcripts are not retained after the packet is drafted.** Only the packet fields are kept (Privacy by Minimization). This retention default is part of the pilot consent terms, which need owner approval.

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. Implements AR-07, AR-12 and AR-18. |
