# FAILURE-MODE REVIEW & REVISION v0.1
Lane 02: Mission & Diagnostic Engine · Build step 8 of 9

Status: **DRAFT**. The fixes below have been applied to the Lane 02 drafts, whose revision logs are now at `0.1-rev1`.
Inputs: the findings in `THREE_USER_SIMULATION_v0.1.md` §6, plus five stress traces (§2) written to probe rule edges the friendly simulation didn't reach.
Verification after the fixes: `kta_check.py` gives 0 errors and 0 warnings; `test_kta_check.py` passes 27 tests.

---

## 1. Summary
| Outcome | Count | IDs |
|---|---|---|
| Fixed in the specs, checker or schemas | 15 | FM-01, 03, 04, 05, 06, 07, 08, 09, 10, 11, 13, 18, 19, 20, 22 |
| Routed to pilot prep, Lane 03 or Lane 04 | 5 | FM-12, 15, 16, 17, 21 |
| Needs pilot evidence | 1 | FM-14 |
| Merged | 1 | FM-02 (into FM-01) |
| **Material changes triggered** | **0** | None of these fixes changes a CORE or CURRENT rule, the market, the mission, a metric or the scope. |

## 2. Stress traces
Each trace runs a hostile or messy input through the rules, on paper. There are no fixtures for these yet; they would be good additions to the regression tests.

### ST-1 · Messy intake
- **Input:** "I do marketing: campaigns, content, reporting, meetings." "No idea" on time split. 15 min a week. Policy unknown.
- **Trace:**
  - The DQ-06 probe ("What did you hand over last Thursday?") yields 2 concrete tasks.
  - DQ-07 gives nothing, so coverage is `low`.
  - MPR-11 adds a `personal_empirical` coverage item.
  - The budget is under 30, so micro mode applies.
- **Break found:** The Task Map schema required ≥3 tasks, so **no valid packet could be formed**. The user would just have been sent back into intake.
- **Fix (FM-18):**
  - Accept 1–2 tasks with `map_confidence: low`.
  - The first experiment must then be map-building: a `time_audit` of 3 days × 5 min, which fits 15 min/week.
  - New invariant **INV-15**, and a mutation test.

### ST-2 · Prohibitive policy plus a discouraging manager
- **Input:** An accountant variant: `employer_ai_policy = prohibits`. The manager says "we don't do AI here". The goal archetype is `leverage`.
- **Trace:** INV-08 blocks work material. But the rules said nothing about whether *any* AI practice is acceptable, or whether a prohibition should change the diagnosis.
- **Fix (FM-19, MPR-14):**
  - AI-tool experiments are allowed only as off-work practice on public or synthetic material, never producing work deliverables.
  - Non-tool archetypes are preferred.
  - A prohibition is itself decision-relevant: for `leverage` goals, re-check the archetype, because `protect` (making anchor value visible) or `transition` may fit better.
  - Stakeholder-facing experiments with a discouraging manager rely on the existing harm branch (B6) and honest framing.

### ST-3 · Two non-attempts in a row
- **Input:** The designer fails AX02 as well.
- **Trace:** A5 → `rediagnose`, which is covered by a mutation test. But **"rediagnose" was never defined**. An operator could re-run the entire intake and cost the user 20 minutes.
- **Fix (FM-20):** A rediagnose mini-protocol: 3 questions and ≤10 minutes, then re-run MPR-01 and MPR-09. "None for now" is an allowed answer, which closes the mission with a watch trigger.

### ST-4 · The experiment backfires
- **Input:** The accountant pastes real figures into a tool before the data scope is confirmed. CQ-8 reports this.
- **Trace:** A1 → `escalate`, and the operator reviews within one business day. But **what the operator does was undefined**, and there was a risk of improvised legal advice.
- **Fix (FM-21):** An operator escalation playbook in `V0_PILOT_PREPARATION_v0.1.md`:
  - acknowledge without blame;
  - establish the facts (what data, which tool, which rules);
  - point to the employer's or client's own process;
  - **give no legal advice**;
  - stop that line;
  - log the incident;
  - run a spec post-mortem.

### ST-5 · A user who refuses experiments
- **Input:** "I just want to know whether to worry. I'm not doing homework." Archetype `clarify`.
- **Trace:** The contract required one experiment. The user declines, the status can't be recorded, and A5 would eventually count the refusal as failure and push `rediagnose`.
- **Fix (FM-22):**
  - An experiment status of `declined`, and a check-in rule A18: continue with the explain and research steps.
  - A smaller experiment is offered **once**.
  - A decline doesn't count toward A5, and it's exempt from INV-14.
  - This follows the Blueprint wording "Action Over Information … **when action is useful**" and does not change it.

## 3. Findings register
| ID | Failure mode | Severity | Resolution | Where |
|---|---|---|---|---|
| FM-01 | A revision broke links from resolved ledger items to the replaced experiment | Med | INV-02 history exception | Contract INV-02, checker |
| FM-03 | A transition focus wasn't accepted as a leverage destination | Med | MPR-04 widened | Planner, checker |
| FM-04 | Light-touch focused on the largest task, which was identity-valued site work | Med | MPR-20 now picks the most predictable non-protected medium+ task | Planner |
| FM-05 | Clarify's explain-first step came before research, risking unverified claims | **High** (evidence) | Explain-first uses user-local facts only; evidence comes at check-in | Planner MPR-07 |
| FM-06 | The generic lint flagged descriptive uses of "AI tools" | Low | Pattern narrowed to advice verbs | Checker |
| FM-07 | A time constraint collided with task timing (close week) | Med | 9th filter "timing-feasible" with a retrospective variant | Planner MPR-13 |
| FM-08 | `data_class` was ambiguous when no tool is used | Low | Defined as the most sensitive material put into a tool or shared | AX schema doc |
| FM-09 | "Tool approved, but for which data?" wasn't representable | **High** (safety) | Treat as `unknown` until the scope is confirmed | Contract §5.4, MPR-14 |
| FM-10 | The freelancer's rules come from clients, not an employer | Low | Wording now; rename to `work_material_rules` in v0.2 | Contract §5.4 |
| FM-11 | The engine missed a policy conflict in the user's current habit | **High** (safety) | MPR-14 current-habit cross-check, and a checklist item | Planner |
| FM-12 | "Less looks like less": the naive answer has more bullet points | **High** (value/trust) | Delivered packets must show the omissions. Lane 04 must present selection as value. The pilot measures LLM-Baseline Preference (MCP-4). | Contract §5.13 → Lane 04, pilot |
| FM-13 | The operator caught an engine miss in every packet | Med | A checklist item that every user-raised item gets placed. The pilot attributes changes via `operator_log`. | Planner §5, pilot |
| FM-14 | Audit-first experiments may feel like homework | Med | **Evidence needed.** Pilot tracks attempt rate by archetype and confidence baseline. | Pilot |
| FM-15 | Every packet queues 1–2 research items: operator load | Med | Research reuse across users (a shared cache of answered world facts) and a capacity plan | Pilot, Lane 03 |
| FM-16 | The swap test has no contrast set outside the simulation | Low | Use SIM-ACC, DES, SAL and LOW as the pilot contrast profiles | Pilot |
| FM-17 | Author bias: the same agent wrote the rules and the users | **High** (validity) | Stress traces (this file). Pilot with real users. Optional independent adversarial review (owner's choice). | Pilot, handoff |
| FM-18 | Thin task map: no valid packet possible | **High** (coverage) | 1–2 tasks allowed with a map-building experiment; INV-15 | Task Map, contract, checker |
| FM-19 | A prohibitive policy was unhandled beyond data | Med | MPR-14 rule | Planner |
| FM-20 | "Rediagnose" was undefined | Med | Mini-protocol | Feedback logic |
| FM-21 | Escalation was undefined | **High** (harm) | Operator playbook | Pilot prep |
| FM-22 | A decline couldn't be recorded, and refusals would be counted as failures | Med | `declined` status, A18, INV-14 exemption | AX schema, feedback, checker |

## 4. What remains uncertain (evidence needed, not fixable on paper)
1. Whether real users find pre-registered, bounded experiments **more** valuable than a longer generic answer (FM-12, FM-14). This is the central V0 question.
2. Whether self-reported task maps are accurate enough without an audit (AR-07). The pilot compares DQ-07 estimates with any `retro_audit` results.
3. How much of each delivered packet's quality comes from the operator rather than the engine (FM-13). Measured with `operator_log`.
4. Whether the E2/E3 evidence requirement is achievable in practice, or whether most check-ins produce E1 (AR-19).
5. Check-in response rates and non-response handling (A7, A5).

## 5. Proposed registry updates arising here
None of these needs a new material decision. They are candidate Experiment Registry entries for V0, drafted in `04_REGISTRIES/PROPOSED_REGISTRY_UPDATES_v0.1.md`:
- **EXP-V0-01:** pre-registered experiment vs generic-answer value (FM-12)
- **EXP-V0-02:** attempt rate by archetype and baseline confidence (FM-14)
- **EXP-V0-03:** accuracy of self-reported time shares (AR-07)

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First review: 22 findings, 5 stress traces; fixes applied as `0.1-rev1` across the Lane 02 drafts. |
