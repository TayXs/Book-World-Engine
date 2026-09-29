# MISSION PLANNER DECISION RULES v0.1
Lane 02: Mission & Diagnostic Engine · Build step 4 of 9

Status: **DRAFT**, authorized Lane 02 work.
Upstream: the Output Contract, the Diagnostic Architecture and the Task Map Schema.
Downstream: the ActionExperiment Schema (step 5) and the Feedback Logic (step 6).

---

## 1. The planner's question
> What does this person need to understand, investigate or test next, and what can they safely leave aside for now?

The planner turns `goal + context + task_map + ledger` into `mission + first_experiment + claims`.

Personalization happens here, as four acts. Every rule is tagged with the act it performs:
- **[SEL]** selection;
- **[SEQ]** sequencing;
- **[OMI]** omission;
- **[ADA]** adaptation (groundwork for step 6).

Rewording the same content for a different person is *not* personalization and is not a planner output (AR-04).

## 2. Precedence
When rules conflict, the one higher in this list wins:

1. **MPR-14 Safety**
2. **MPR-02 Scope**
3. **MPR-12 Evidence gate**
4. **MPR-08 Identity protection**
5. **MPR-17 Attention budget**
6. All other rules

## 3. Execution order
```
MPR-02 scope ─▶ MPR-01 goal ─▶ MPR-11 ledger ─▶ (D6 follow-ups) ─▶ MPR-03..07 candidates
   ─▶ MPR-08/14 filters ─▶ MPR-10 fear–size ─▶ MPR-09 rank & select ─▶ MPR-15 omissions
   ─▶ MPR-12 evidence gate ─▶ MPR-13 experiment ─▶ MPR-16 sequence ─▶ MPR-17 budget
   ─▶ MPR-19 exit ─▶ MPR-18 anti-convergence check ─▶ (MPR-20 light-touch if nothing qualifies)
```
In V0 the operator runs these rules as a checklist, with or without LLM drafting. Any deviation from a rule goes in `operator_log` with the reason.

## 4. Rules

### MPR-01 · Goal diagnosis and archetype [SEL]
- **Means become ends.** A stated goal that is a *means*, such as "learn AI tools" or "take a course", is traced to the *end* it serves. If the intake doesn't reveal the end, one follow-up asks: "What would that let you do?"
- **`diagnosed_goal` template:** "Change *<observable aspect of work>* within *<horizon>* so that *<success signal>*." If it differs materially from `stated_goal`, fill `divergence_note`.
- **Archetype**, from the answers to DQ-01, DQ-04 and DQ-11:

  | Archetype | Pattern |
  |---|---|
  | `transition` | The future picture names a different role, field or employment type. |
  | `leverage` | Same role, with more impact, advancement or less grind. The worry is *falling behind*. |
  | `protect` | The worry is *displacement or devaluation* of the current work. The future is about keeping and strengthening the position. |
  | `clarify` | The main need is to know *whether and how much* to worry. The future picture is vague, or amounts to "not worried". |

- **Ties** get one follow-up: "Keep your current role and make it stronger, or use this to move into something different?"

### MPR-02 · Scope gate
- `out_of_scope` → build the scope-only packet with the approved signpost and stop.
- `in_scope_operator_attention` → proceed, with these limits:
  - the operator reviews every section;
  - experiment effort is capped at half the budget;
  - no stakeholder-facing experiments;
  - the check-in comes earlier (≤5 days).

### MPR-03 · Focus candidates: time share comes first [SEL]
- Candidates are tasks, or clusters of tasks that share an output or stakeholder.
- **Eligible as a primary focus:** `time_share ∈ {large, medium}`. Two exceptions:
  - an `accountability = 3` task (small time, high stakes);
  - a task named in a `transition` target.
- **Why time share first:** it is a *user fact* that is available right away. A focus built on it doesn't have to wait for Lane 03 evidence (MPR-12).
- Each candidate is typed by MPR-04 to MPR-07. A task can fit more than one type.

### MPR-04 · Leverage candidate [SEL]
- **Pattern:** the Task Map *leverage view*: large or medium share, predictability ≥ 2, judgment ≤ 2, autonomy ≥ 2.
- **Question it opens:** under this user's constraints, can assistance or redesign reclaim time or improve quality on this task? *And what would the reclaimed time be used for?*
- **Pairing rule.** A leverage focus is valid only with a **destination** for the reclaimed time. The destination is an anchor focus (MPR-05), a transition focus (MPR-06), or a goal-linked use the user has stated. *(The transition option was added in step 7 after the sales simulation; see FM-03.)* If there is no destination, add a `user_context` uncertainty: "What would you do with the time?" (route ask; impact high). Efficiency with no destination can speed up a user's own devaluation.

### MPR-05 · Anchor-value candidate [SEL]
- **Pattern:** the *anchor view*: large or medium share, judgment ≥ 2, and relationship ≥ 2 or accountability ≥ 2.
- **Question it opens:** do the people who rely on this work, or pay for it, see and value the judgment in it, and how could that value be strengthened or made visible?
- **Typical experiments:** `value_probe`, `visibility_move`.

### MPR-06 · Transition candidate [SEL]
- **Pattern:** archetype `transition`.
- Candidates are the current tasks whose skills plausibly carry over to the target role. That link is an operator hypothesis, labeled as one.
- A `world_fact` research question about entry into the target role is **always** added: demand, entry routes, and what is actually required.
- **Typical experiments:** `market_probe`, `skill_probe`.

### MPR-07 · Clarify candidate [SEL][SEQ]
- **Pattern:** archetype `clarify`.
- An **explain** step (understanding gap) comes *before* the experiment. The specific world fact behind the worry gets a research question.
- *(FM-05)* The explain-first step uses **user-local facts only**, such as "55% of your week is on-site work". Research isn't back yet, so the evidence-based part of the explanation is delivered at check-in (MPR-12).
- The first experiment is small and **diagnostic**, on the task the worry attaches to, usually a `shadow_test` or `retro_audit`. The user gets personal evidence rather than headlines.

### MPR-08 · Identity protection [SEL][OMI]
- A task with `identity_value = 3` is **never** the target of an automation or delegation experiment unless the user opts in.
- Such a task can still be an anchor focus.
- If the goal plausibly requires change in that task, the planner adds a `decide` step that puts the trade-off to the user. The planner does not make that choice for them.

### MPR-09 · Rank and select at most 3 focus areas [SEL]
Ranking is **lexicographic, not a numeric score**, to avoid false precision.

| Order | Criterion | Levels |
|---|---|---|
| 1 | Goal alignment | direct > indirect. "None" is not eligible. |
| 2 | Stake | large > medium > small. `accountability = 3` counts as medium. |
| 3 | Decision-relevant uncertainty attached | open high-impact item > none |
| 4 | Actionability | autonomy ≥ 2 and a safe experiment exists > otherwise |
| 5 | Tie-break | leverage: higher `friction` first · anchor: higher `identity_value` first |

- Keep at most 3. The rest become omissions with revisit conditions (MPR-15).
- For archetypes `protect` and `leverage`, the selected set **must include an anchor focus**, or the packet must state why no anchor exists. This follows from the pairing rule in MPR-04.

### MPR-10 · Fear–size mismatch [OMI][SEQ]
If the main concern attaches to a task with `time_share = small`, or to the occupation in general:
- it does **not** become a focus;
- add an **omission** in the form "set X aside for now, because it's a small part of your week", with a revisit condition someone can observe;
- add an `understanding_gap` item (route explain), plus a `world_fact` item if the worry rests on a claim about the world.

Omissions are honest: they say *for now*, never *never*.

### MPR-11 · Building the Uncertainty Ledger [ADA]
**Where candidate items come from:**

| Trigger | Kind → route |
|---|---|
| A decisive trait was inferred with low confidence (Task Map §5 rule 2) | user_context → ask |
| Task map coverage is `low`, or the time shares are guesses | personal_empirical → experiment (`time_audit` / `retro_audit`) |
| An `exposure_hypothesis` or a `future_value` that affects the plan | world_fact → research |
| `employer_ai_policy = unknown` | user_context → ask. If the user can't find out quickly, a `policy_check` step. |
| A leverage focus with no destination (MPR-04) | user_context → ask |
| What stakeholders actually value (MPR-05) | personal_empirical → experiment (`value_probe`) |
| The user's concern (MPR-10) | understanding_gap → explain, and/or world_fact → research |
| AI performance **on this user's task under their constraints** | personal_empirical → experiment (`shadow_test`) |
| AI capability **in general** for the task type | world_fact → research |

- **Two separate questions.** The last two rows are different questions and must stay separate:
  - The personal question drives the experiment.
  - The general question informs the explanation.

  The experiment's rationale must not depend on the answer to the general question (MPR-12).
- **Impact:**
  - high: the answer could change the focus selection or the first experiment;
  - medium: it could change the sequence or the explanation;
  - low: neither. Set status `deferred`, with a reason.
- **Blocking** is true when some delivered element would be wrong if `current_belief` turns out false.
- **Size:** at most 10 items. Merge near-duplicates.

### MPR-12 · Evidence gate
1. Every statement about the world that will be *shown* to the user gets a `claims` entry.
2. A `world_fact` that is not `verified` is shown as a **hypothesis** ("we think…, and we're checking"), or it is left out.
3. A focus rationale may rest on user facts (time share, accountability, stated goal) and verified claims. It may **not** rest on an unverified world fact alone.
4. The first experiment's `depends_on` list contains no open `world_fact` (INV-06).
5. A blocking `world_fact` gets a `research` step before any `decide` step that depends on it.

### MPR-13 · Selecting the first experiment [SEL]
**Generate candidates.** Take the open high-impact `personal_empirical` items on the priority-1 focus area (then priority 2, if needed). Map each one to experiment archetypes:

| Uncertainty pattern | Archetype(s) |
|---|---|
| "Can assistance help *me* with task T under my constraints?" | `shadow_test` |
| "Where does my time actually go?" | `retro_audit` (from calendar or records, one sitting) · `time_audit` (live, ≤5 min/day) |
| "What do the people who rely on my work value?" | `value_probe` |
| "Is target role X realistic for me?" | `market_probe` · `conversation_probe` |
| "Could I do skill S?" | `skill_probe` |
| "Is my judgment work visible to those who assess me?" | `visibility_move` |
| "Would handing T to someone or something free me for Y?" | `delegation_test` |

**Filters.** A candidate must pass all of these:

| Filter | Test |
|---|---|
| Safe | Passes MPR-14. |
| Cheap | Effort ≤ min(90 min, weekly budget × window weeks). Window ≤ 14 days. |
| Personal | Operates on the user's own task, or a faithful public or synthetic stand-in for it. |
| Observable | At least one measure that can be recorded within the window and is not "felt useful". |
| Meaningful | At least 2 distinct next moves depending on the result. The branch table shows them. |
| Not generic | Not a course, and not "read about X". |
| Evidence-independent | Its rationale does not need an unverified world fact (MPR-12). |
| Respectful | Honors MPR-08 and the `constraints`. |
| Timing-feasible *(FM-07)* | The window doesn't collide with a time constraint. If the task only happens inside a blocked window (for example, close week), use a **retrospective variant** on the last instance of the task. |

**Choose** among the survivors in this order:
1. The one that targets the highest-impact uncertainty.
2. Then the lowest effort.
3. Then the more reversible one, with no stakeholder exposure.

Two overrides based on the baseline:
- confidence ≥ 8 → prefer the candidate most able to *disconfirm* the user's current belief;
- confidence ≤ 3 → prefer the smallest effort.

**`policy_check` is never the first experiment on its own.** It is an ask step that runs before or alongside the experiment. When the policy is unknown, the experiment uses public or synthetic material instead.

### MPR-14 · Safety (the restrictive default from AR-08; ratification is pending as MCP-2)
- **Material rules (INV-08):**
  - confidential, regulated or internal material goes only into tools the employer has approved;
  - if the policy is unknown, only public, synthetic, redacted or no material is used.
- **Honest framing.** No experiment involves deceiving stakeholders. A `value_probe` question is asked openly.
- **No material exposure:** nothing that risks employment terms, legal exposure or financial loss. Every experiment is reversible or low-stakes and has stop conditions.
- **No paid tools in V0** unless the user states a budget for them. Prefer tools the user already has or that are approved.
- **Operator-attention users:** no stakeholder-facing experiments (MPR-02).
- **Policy `prohibits` *(FM-19)*:** AI-tool experiments are allowed only as off-work practice on public or synthetic material, and must never produce work deliverables. Non-tool archetypes are preferred (`retro_audit`, `value_probe`, `visibility_move`, `market_probe`). A prohibition also matters for the decision itself: for a `leverage` goal, re-check the archetype with MPR-01.
- **Approved tool, unconfirmed data scope *(FM-09)*:** treat the policy as `unknown` until the scope is confirmed.
- **Current-habit cross-check *(FM-11)*:** compare current AI use (DQ-09) with the stated rules (DQ-10). If a current habit appears to breach the user's *own* described rules, add a user-local `engine_judgment` claim and an explain step. Keep it matter-of-fact: no blame, and no suggestion of any reporting duty.

### MPR-15 · Omissions [OMI]
- **Minimum:** 1. **Sources:** candidates that were not selected, fear–size mismatches, and things *this user* raised or is clearly considering (such as "should I learn to code?").
- Every omission is grounded in this user through its `relevance`. **Generic filler omissions are forbidden.** Don't add "don't learn to code" for someone who never considered it.
- Each omission carries `why_omitted` and an *observable* `revisit_condition`.

### MPR-16 · Sequencing [SEQ]
The default pattern has 2 to 6 steps and spans 2 to 4 weeks in V0:
1. **Unblock.** Only the ask or `policy_check` steps the experiment actually depends on.
2. **Experiment.** Starts within 3 days of delivery.
3. **Research**, in parallel. The operator or Lane 03 answers the high-impact world facts, returning by check-in.
4. **Explain**, just in time. An understanding gap is scheduled for the point where it informs a decision, not all at intake.
5. **Decide**, at check-in. The next move comes from the branch table (step 6).

The `clarify` archetype reverses steps 2 and 4: explain first.

### MPR-17 · Attention budget
- Count the user's planned minutes:
  - reading the packet (≤10);
  - the experiment;
  - the check-in (≤10);
  - any user-owned ask or explain steps.
- The total must be ≤ `time_budget_minutes_per_week × plan_weeks`. If it is over, drop the lowest-priority steps into omissions.
- **Micro mode**, when the budget is under 30 min/week: one focus area, an experiment of ≤ 30 min, and one explain step at most.

### MPR-18 · Anti-convergence self-check
Before the operator reviews the packet:
- **Swap test (AT-1).** Would the priority-1 focus and the experiment fit a contrast profile just as well? In the simulation, the contrast profiles are the other simulated users. In the pilot, a fixed set of 3 contrast profiles is used.
- **Generic lint (AT-2).** Check the titles for generic advice patterns.

On failure, re-ground the packet in the user's specific tasks and uncertainties. If that isn't possible, flag it to the operator and don't ship the packet.

### MPR-19 · Exit criteria [ADA]
- Every packet includes `user_opt_out` and `risk_detected`.
- Add `goal_met`, tied to a specific success signal.
- Add `no_decision_relevant_uncertainty`: the mission is "done for now" when no open item would change a decision.

### MPR-20 · Light-touch mission [SEL][OMI]
Use this when no candidate passes MPR-09 criteria 1–2, or when the user's own evidence shows little near-term pressure. The packet then has:
- one focus area: the medium-or-larger task with the **highest predictability that isn't identity-protected**, because that is where near-term change is most plausible and cheapest to test. Fall back to the largest task if none qualifies. *(Changed from "the largest task" by FM-04. For the electrician, the largest task is identity-valued, low-predictability site work.)*
- an explain step;
- a minimal diagnostic experiment of ≤ 30 min;
- an omission that works as a **watch trigger**, for example "revisit if your team adopts tool X or your review criteria change".

It is correct and useful for KTA to say "not much to do right now, and here's how you'll know if that changes". That respects Minimum Necessary Attention.

## 5. Planner output checklist (the operator ticks it before `operator_reviewed`)
- [ ] INV-01 to INV-15 pass (`kta_check.py`)
- [ ] Every focus area, step and omission can be traced to a named task or user fact
- [ ] A leverage focus has a destination (MPR-04)
- [ ] The experiment passes all 9 filters (MPR-13), including timing feasibility
- [ ] No unverified world fact is shown as fact (MPR-12)
- [ ] The swap test and the lint pass (MPR-18)
- [ ] Reading time ≤ 10 min · planned minutes within budget (MPR-17)
- [ ] Every tool, course, plan or worry the user raised appears as a focus, step, omission or claim *(FM-13)*
- [ ] Current AI habits are cross-checked against the stated rules (MPR-14, FM-11)
- [ ] `operator_log` explains every deviation from these rules

## 6. Known limits of v0.1 (tested in steps 7–8)
- Lexicographic ranking may be too coarse when two tasks are tied on every criterion. The tie-breaks are untested.
- The "destination" pairing rule assumes that reclaimed time is under the user's control. That assumption fails in heavily managed roles.
- Contrast profiles for the swap test outside the simulation are not defined yet (pilot prep).

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. MPR-01 to MPR-20. |
| 0.1-rev1 | 2026-09-29 | Step 7–8 fixes: MPR-04 destination (FM-03); MPR-07 user-local explain (FM-05); MPR-13 timing filter (FM-07); MPR-14 prohibits, data scope and habit cross-check (FM-19, 09, 11); MPR-20 focus choice (FM-04); checklist (FM-13). |
