# THREE-USER SIMULATION v0.1
Lane 02: Mission & Diagnostic Engine · Build step 7 of 9

Status: **DRAFT**, simulation evidence. The users are fictional. Nothing here is pilot evidence.
Machine-checked fixtures: `simulation/SIM-ACC`, `SIM-DES`, `SIM-SAL`, plus the edge cases `SIM-LOW` and `SIM-OOS`.
To reproduce: `python KTA/tools/kta_check.py` gives 0 errors and 0 warnings. `python -m unittest KTA/tools/test_kta_check.py` runs 24 mutation tests, all passing.

---

## 1. Verdict

| Test (Lane 02 brief and Output Contract) | Result |
|---|---|
| **Pass condition:** materially different missions and experiments, based on actual context | **PASS.** 3 archetypes, 3 different first-experiment archetypes, different data classes, different omissions and different check-in paths (§3). |
| **Failure condition:** generic convergence ("learn AI, improve communication, use AI tools, focus on human skills") | **Not observed.** The generic lint has 0 hits after one false-positive fix (FM-06). |
| AT-1 swap test (judgment) | **PASS** for all 6 pairs (§4). |
| AT-3 naive-LLM contrast | **PASS** (≥3 absent elements per user), with an important caveat (§5). |
| AT-4 attention | **PASS.** Delivered reading time is 4–8 minutes. |
| Invariants INV-01 to INV-14 | **PASS** on all 7 packets, 3 feedback records and 3 decisions. |

**Main caveat.** The same agent wrote the rules and the users, which invites confirmation bias. The intake answers are cleaner than real ones will be. Step 8 adds stress traces aimed at the rule edges. Only the pilot can test real value.

## 2. The three users

### 2.1 SIM-ACC: management accountant (reconciliation- and reporting-heavy)
**Intake summary:**
- Mid-level, manufacturing, employee.
- Copilot licences arrived and the manager said "close should get faster".
- Future picture: "the person ops managers come to."
- Tasks: variance pack **30%**, reconciliations 20%, ad-hoc ops analysis 15% ("best part of the job"), reforecast 10%, journals and queries.
- Copilot is approved, but the user doesn't know whether ledger data is allowed with it.
- 60 min a week. Close week is off-limits.

**Planner trace (key rules):**

| Rule | Application |
|---|---|
| MPR-01 | The stated goal is a worry, but the future picture is leverage with a destination. `divergence_note` is recorded. |
| MPR-04/05 | T01 is a leverage candidate. T03 is an anchor and identity-protected (MPR-08), so it's the *destination*. |
| MPR-09 | F1 = T01 (large, direct, testable). F2 = T03 (anchor). T02 goes to omissions: autonomy 1, the ERP decides. |
| MPR-11/12 | Two questions are kept separate: the personal "can *I* draft faster?" (UQ02, experiment) and the general "how reliable are assistants at this?" (UQ03, research). The role-content worry goes to UQ05 (explain) and UQ06 (research). |
| MPR-13/14 | Shadow test on **synthetic** data, because the data scope is unknown (INV-08). Policy clarification is a separate ask step (S1), never the experiment itself. |

**Packet (r1):**
- **Focus:** F1 "Shrink the drafting part of the month-end variance pack"; F2 "Grow the ops analysis that managers come to you for".
- **Experiment:** AX01 "Variance commentary: your way vs Copilot, on made-up numbers". 70 min; the user predicted "maybe 10 min saved, heavy rewriting".
- **Omissions:** reconciliations, the IT Copilot webinar the user mentioned, reforecast.
- **Research queued:** AI drafting error types, and role-content vs headcount evidence.
- **Held back:** the engine drafted an unverified "task mix, not headcount" claim. The operator removed it (MPR-12).

**Check-in → adaptation:**
- Results: 22 vs 38 minutes (E3), sendable, 2 corrections (an invented cause and a sign flip). The user's view changed: "checking is the real work."
- IT confirmed that internal financial data is allowed within the company Copilot tenant. The manager wants the close shortened to free analysis time.
- Decision: **A13 continue** via branch B1.
- **r2:** AX02 re-drafts *last month's real* section after close, now in policy. It uses `confidential` material with the approved tool, so INV-08 passes.

### 2.2 SIM-DES: freelance graphic designer (creative production- and client-interaction-heavy)
**Intake summary:**
- Senior freelancer working with small food and drink brands.
- Clients arrive with AI mockups and question prices.
- Future picture: "fewer, better-paid projects bought for the thinking."
- Tasks: production and variations about 35% (*a guess*), revisions about 25% (*a guess*), concept 20% ("why I do this"), winning work, admin.
- Some client contracts restrict generative AI.
- A D6 follow-up found that every project is priced as **one fee** (UQ03 resolved at intake).
- Constraint: nothing that signals corner-cutting to clients.

**Planner trace:**

| Rule | Application |
|---|---|
| MPR-01 | Archetype `protect`. Diagnosis: a single fee hides which part of the work clients value. |
| MPR-05/08 | Concept (T01) is the anchor and identity-protected, so no automation experiments there. Production (T02) is leverage, with concept work as its destination. |
| MPR-11 | The time shares are guesses, so the top uncertainty is *where the hours and money actually go*. That's personal and empirical, not a question about tools. |
| MPR-13 | A `retro_audit` of 6 past projects was chosen over a `value_probe` (client-facing, uncomfortable under C01, and hard to frame without numbers) and over a `shadow_test` (the question is economics, not capability). |

**Packet (r1):**
- **Focus:** F1 "Make your concept thinking visible and separately priced"; F2 "Cut production hours where your client contracts allow".
- **Experiment:** a 60-minute audit. Only totals and ratios are recorded, and no tool is used.
- **Omissions:** the website rebuild ("human-made design") that the user had planned, which the operator added after the engine missed it; image generators for concept work; revision-process redesign.
- **Research:** rate pressure by work type, and tool licensing and contract clauses.

**Check-in → adaptation:**
- **Not attempted.** Blocker: `time` (a rush job).
- Decision: **A6 simplify** via branch B5.
- **r2:** AX02 covers 3 projects in two 15-minute sittings.
- If this fails again, **A5 rediagnose** applies. The mutation tests cover that path.

### 2.3 SIM-SAL: account executive (relationship-heavy, with research and admin overhead)
**Intake summary:**
- Mid-market B2B software.
- The company is piloting AI SDR tools, and the manager says "reps using AI replace reps who don't."
- Future picture: **enterprise AE**.
- Tasks: discovery and demos 30% ("I'd miss it"), prospect research 20% (disliked), CRM admin 15%, proposals and emails 15% (sometimes polished in a *personal* chatbot), closing 10%.
- Policy: two approved tools, and no customer data in personal tools.
- 45 min a week. Nothing that touches live deals. Listens to audio while driving.

**Planner trace:**

| Rule | Application |
|---|---|
| MPR-01 | The future picture names a different role, so the archetype is `transition`. |
| MPR-06 | F1 is the transition focus (T02, T05), with the manager's criteria (ask) and the market requirements (experiment) as its questions. |
| MPR-04 | Prep (T01) is leverage, and the transition focus is its destination. This case **exposed FM-03**: the original pairing rule allowed only an anchor as a destination. |
| MPR-10 | The AI SDR worry attaches to outbound work, which this AE doesn't do. It becomes omission O1, plus an explanation and research. |
| MPR-13 | A `market_probe` on public postings. A skill probe on live deals was rejected because it would break C01. |
| MPR-14 | The operator caught that the user's personal-chatbot email polishing conflicts with the stated policy. A non-judgmental claim CL03 and an explain step were added. **The engine missed this (FM-11).** |

**Check-in → adaptation:**
- Results: of 9 recurring requirements, 5 were met, 2 partly and 2 missing (E2). The gaps are multi-threading and exec-level business cases; deal size, the user's prediction, barely mattered.
- The manager's route is internal: co-run a mentor-led enterprise deal.
- Surprise: 4 of 7 postings asked for "AI-assisted prospecting".
- Decision: **A15 investigate_further** via branch B3, plus **A17**, which adds a research item.
- Next: a conversation with an enterprise AE at the user's own company.

### 2.4 Edge cases
| ID | Case | Outcome | Rules exercised |
|---|---|---|---|
| SIM-LOW | Commercial electrician whose kid says "AI takes all jobs". 55% of the week is on-site work. 20 min a week. | **Light-touch mission**: one focus (certificate paperwork), a 20-minute voice-notes test on a made-up job, and an omission that works as a watch trigger for hands-on work. | MPR-07 clarify, MPR-17 micro mode, MPR-20. **Exposed FM-04 and FM-05.** |
| SIM-OOS | Laid off last week, rent due, not sleeping. | **Out of scope.** Signpost only, with no task map or mission. The signpost wording is a placeholder pending owner approval. | D0/DQ-02, MPR-02, INV-01 |

## 3. Differentiation matrix

| | SIM-ACC | SIM-DES | SIM-SAL | SIM-LOW |
|---|---|---|---|---|
| Archetype | leverage | protect | transition | clarify |
| Policy state | tool approved, data scope unknown | client contracts restrict | 2 tools approved | none known |
| Priority-1 focus | variance pack drafting (T01, 30%) | concept pricing (T01, anchor) | gap to enterprise AE (T02+T05) | paperwork (T03, light-touch) |
| First experiment | `shadow_test`, synthetic data | `retro_audit`, no tool | `market_probe`, public data | `shadow_test`, synthetic job |
| User's own omission | IT Copilot webinar | website rebuild | "AI for Sales" certification | hands-on replacement worry |
| Fear handling | role worry → research + explain | price worry → research | AI SDR worry → omission + explain | headline → omission + research |
| Check-in path | confirms → continue → real data | not attempted → simplify | mixed → investigate + new research | (not simulated) |
| Engine miss caught by operator | close-week timing; unverified claim | user-raised website plan | policy conflict in current habit | — |

## 4. AT-1 swap test (judgment)
The question for each pair: would user X's priority-1 focus and first experiment be a sound choice for user Y?

| From → to | Fits? | Why not |
|---|---|---|
| ACC → DES/SAL | No | Neither user has a variance pack or reporting commentary. |
| DES → ACC/SAL | No | Both are salaried with no per-project fees, and the accountant's time split is already high-confidence, so MPR-13 would never pick an audit. |
| SAL → ACC/DES | No | Neither user's goal is a transition. The designer has no target role. |
| ACC ↔ LOW | Same archetype, different content | Both are `shadow_test` on synthetic data. The shared **structure** comes from the archetype library, which is by design. The task, tool, policy state and next branches all differ. |

The textual-overlap aid in `kta_check.py --swap` shows ≤0.08 overlap on every pair. It is a weak proxy; the judgment above is the actual test.

## 5. AT-3 naive-LLM contrast, with an honest caveat
**Method limitation.** The "naive answers" below are characterizations of a typical one-shot general-assistant reply to "How do I stay valuable as AI changes my work as a <role>?". They were written by this same agent. They are **not** captured model outputs. The pilot must capture real, verbatim baseline outputs (see pilot prep).

| User | Typical naive answer | Elements in the KTA packet that a naive answer lacks |
|---|---|---|
| ACC | Learn Copilot and ChatGPT · build data skills (Power BI, Python) · move toward business partnering · strengthen communication and storytelling · get certifications · stay current | ① a bounded, *pre-registered* test on the user's own biggest task ② a data-scope safety gate that uses synthetic data until the policy is confirmed ③ explicit omissions of the webinar, recs and reforecast ④ the role-shrink claim held back until researched ⑤ branch rules that led to a real-data rehearsal |
| DES | Use Firefly and Midjourney to speed up · focus on brand strategy · value-based pricing · build a niche and personal brand · upskill into motion or 3D | ① the finding that a single fee hides the value split ② an audit of the user's *own* projects before any pricing change ③ concept work protected from automation ④ the website rebuild parked until clients are asked ⑤ a simplify path when the user didn't do it |
| SAL | Use AI for prospecting and email · build emotional intelligence · consultative selling · go for enterprise deals · mentor · LinkedIn brand | ① the AI SDR fear shown to attach to work the user doesn't do ② the policy conflict in a current habit, caught ③ an experiment that never touches live deals ④ the internal promotion route separated from the market route ⑤ a new research question raised by what the user observed |

**The caveat that matters.** The naive answers often point in *roughly the right direction*: business partnering, value-based pricing, going for enterprise deals. KTA's difference is mostly **procedural and grounding**:
- selection and omission;
- routing each unknown to the right resolver;
- safety gating;
- pre-registered observation;
- adaptation.

It is not mostly in having a smarter headline. That has two consequences:
1. On first read, **"less can look like less."** The naive answer has more bullet points. See FM-12 in step 8.
2. KTA's value will only show *over the loop*. The pilot has to measure outcomes after check-in, not first impressions.

## 6. What the simulation found (inputs to step 8)
| ID | Finding | Status |
|---|---|---|
| FM-01 | A resolved ledger item's links to a replaced experiment broke reference integrity. | **Fixed in step 7** (INV-02 history exception) |
| FM-02 | Same root cause as FM-01, seen in r2. | Merged into FM-01 |
| FM-03 | The leverage pairing rule didn't accept a transition focus as a destination. | **Fixed in step 7** (MPR-04) |
| FM-04 | MPR-20 "largest task" is wrong for a low-exposure user, whose largest task is identity-valued, hands-on work. | Fix in step 8 |
| FM-05 | "Explain first" for the clarify archetype conflicts with the evidence gate, because the research isn't back yet. | Fix in step 8 |
| FM-06 | The generic lint flagged "AI tools" used descriptively. | **Fixed in step 7** |
| FM-07 | A constraint collided with task timing: the close week is off-limits, but the real pack is built during it. | Fix in step 8 |
| FM-08 | `materials.data_class` was ambiguous for experiments that use no tool. | Fix in step 8 |
| FM-09 | "The tool is approved, but for which data?" isn't representable. | Fix in step 8 |
| FM-10 | For freelancers, the "employer" policy is really client-contract rules. | Fix in step 8 (wording); rename in v0.2 |
| FM-11 | The engine missed a policy conflict in the user's current behavior. | Fix in step 8 (MPR-14) |
| FM-12 | "Less looks like less": perceived-value risk compared with a naive LLM. | Step 8 → Lane 04 and pilot |
| FM-13 | The operator caught an engine miss in every packet. | Step 8 (checklist) and pilot attribution |
| FM-14 | An audit-first experiment may feel like homework to a low-confidence user. | Evidence needed (pilot) |
| FM-15 | Research load: every packet queues 1–2 research items for the operator. | Pilot capacity and Lane 03 reuse |
| FM-16 | The swap-test aid is only a textual proxy, and contrast profiles are undefined outside the simulation. | Pilot prep |
| FM-17 | Author bias: the same agent wrote the rules and the users. | Step 8 stress traces + pilot |

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First simulation: 3 users, 2 edge cases, 7 packets, 3 check-ins. |
| 0.1-rev2 | 2026-09-29 | Fixtures regenerated from `tools/fixtures/` after repairs. Changes: `inconclusive` branches added, with DES and SAL B4 relabelled from null to inconclusive (R1); `meta.privacy_check` added (R2); CQ-13 trust and CQ-14 progress added to check-ins (R3); a SAL promotion criterion abstracted from an internal figure to "consistently above quota" (INV-16). Metrics (R4): DUAR 2/3, MAR 2/3, safety gate clear. |
