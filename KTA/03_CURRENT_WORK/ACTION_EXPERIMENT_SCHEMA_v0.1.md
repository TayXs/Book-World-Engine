# ACTIONEXPERIMENT SCHEMA v0.1
Lane 02: Mission & Diagnostic Engine · Build step 5 of 9 · **Lane 02 draft; Lane 05 steward** (AR-05)

Status: **DRAFT**, authorized Lane 02 work.
Machine form: `schemas/action_experiment.schema.json`, embedded in the packet as `first_experiment`.
Upstream: Planner rules MPR-13 and MPR-14.

---

## 1. What an ActionExperiment is
It is the smallest useful real-world action that **reduces an important uncertainty about this user's own situation**, cheaply, safely and in a way someone can observe.

It is **not**:
- advice;
- a course;
- a reading list;
- a habit plan.

It is designed so that *any* result teaches something. A disconfirmed hypothesis is a success when it changes the next step.

Why this matters for defensibility (AR-11): a general LLM can suggest an experiment. KTA **pre-registers** it, meaning it records the user's prediction before the action, then **observes** the result and **adapts** the plan to it. Across users, the structured results become intervention intelligence (Lane 05).

## 2. Fields
| Field | Req | Notes |
|---|---|---|
| `id` | R | `AX01`… |
| `archetype` | R | One of the library entries in §4. |
| `title` | R | User-facing, ≤ 12 words, names the user's actual task. |
| `hypothesis` | R | `{statement, would_be_wrong_if}`. Must be falsifiable by the measures. |
| `targets` | R | `{uncertainty_ids ≥1, task_ids ≥1}`. At least one target uncertainty must be open with route `experiment` (INV-05). |
| `depends_on` | — | The ledger items this experiment *assumes*. None of them may be an open `world_fact` (INV-06). |
| `relevance` | R | Why *this* experiment for *this* user, grounded in the user's facts. |
| `steps` | R | 1–5 × `{n, instruction, minutes}`. Concrete enough to do without asking. |
| `materials` | R | `{data_class, description, tool?}`. `data_class` is one of `none`, `public`, `synthetic`, `redacted_nonconfidential`, `internal`, `confidential` or `regulated`. It means **the most sensitive material that will be put into any tool or shared beyond the user's own control**. When the user only reviews their own records locally and no tool is involved, it is `none` (FM-08). `tool` is `{name, employer_approved: yes\|no\|not_applicable}`. |
| `effort` | R | `{minutes_total, sessions, window_days ≤ 14}`. The sum of step minutes must equal `minutes_total` ± 10%. |
| `prediction` | R | `{user, engine}`. `user` is the user's own prediction, written **before** starting. It may be `null` only while the status is `proposed` (INV-14). `engine` is the expected observation and why. |
| `measures` | R | ≥1 × `{id, what, how_recorded, type}`. `type` is one of `time_minutes`, `count`, `yes_no`, `rating_0_10`, `text_observation` or `artifact_comparison`. **At least one measure must be something other than `rating_0_10`.** |
| `learning_criteria` | R | `{confirms_if, disconfirms_if, informative_note}` |
| `branches` | R | ≥3 × `{id, condition_type, condition, next_move, next_description}`. See §3. |
| `safety` | R | `{stakeholder_exposure, reversibility, stop_conditions ≥1, notes}`. `stakeholder_exposure` is one of `none`, `informed_stakeholder` or `public`. `reversibility` is `reversible` or `low_stakes`. |
| `alternatives_considered` | R | ≥1 × `{archetype, why_not}`: the evidence that MPR-13 selection actually ran. |
| `status` | R | `proposed` → `accepted` → `scheduled` → `in_progress` → `completed` \| `partial` \| `not_attempted` \| `abandoned`. The status can also be `superseded`, or `declined` when the user chooses not to do it (FM-22). |
| `status_history` | — | `[{status, at}]` |

## 3. Branches: the pre-agreed next moves
Each branch has a `condition_type`:
- `confirms`
- `disconfirms`
- `mixed`
- `null_result`: done, but no signal either way
- `partial`
- `not_attempted`
- `harm`: something went wrong

**Required:** `not_attempted` and `null_result` (INV-12). **Strongly expected:** `confirms`, `disconfirms` and `harm`.

`next_move` uses the adaptation vocabulary from step 6:
- `continue`
- `modify`
- `investigate_further`
- `simplify`
- `change_intervention`
- `stop`
- `escalate`
- `rediagnose`

Branches are written *before* the experiment runs. That makes the check-in decision mostly mechanical, and it is auditable. Deviating from a branch at check-in is allowed but must be logged with a reason (step 6).

## 4. Archetype library v0.1
This library is the seed of Lane 05's intervention intelligence. Each entry gives the default design, and the planner adapts it to the user.

### 4.1 `shadow_test`
- **Resolves:** "Can assistance help *me* with task T under my constraints?"
- **Design:** Do one real instance of T the normal way and one assisted way, on **safe material**. If the policy doesn't cover real material, use a faithful public or synthetic stand-in (INV-08).
- **Effort:** 45–90 min · 1–2 sessions.
- **Measures:**
  - minutes each way;
  - the number of substantive corrections;
  - "Would you send this with ≤ N minutes of edits?" (yes/no);
  - the step where the assisted draft failed (text).
- **Typical branches:**
  - Confirms: time saved *and* acceptable → `continue`. Plan the destination for the saved time, and check policy for real material.
  - Quality poor → `investigate_further`. Is it the tool, the input, or the user's skill?
  - `null_result` → `simplify`. Try a narrower sub-step.
  - `not_attempted` → `change_intervention` if the blocker was access or policy; `simplify` if it was time.
- **Safety:** No confidential material without an approved tool. The output is never sent to stakeholders during the test.

### 4.2 `retro_audit`
- **Resolves:** "Where does my time actually go?", when the task-map shares are guesses.
- **Design:** One sitting. Rebuild the last 2–4 weeks from the calendar, sent items or records into the task-map buckets. **Only the bucket totals leave the user's device.**
- **Effort:** 30–45 min.
- **Measures:** hours per task bucket; the difference from the DQ-07 estimate; any unlisted work found.
- **Branches:**
  - Estimates hold → `continue`.
  - A major shift → `rediagnose` the focus (re-run MPR-09).
  - Records don't exist → `change_intervention` to `time_audit`.

### 4.3 `time_audit`
- **Resolves:** the same as `retro_audit`, when no records exist.
- **Design:** 5 working days, ≤ 5 min a day, tallying time into buckets.
- **Effort:** ≤ 25 min over 5 days.
- **Measures:** daily bucket minutes.
- **Branches:** the same as `retro_audit`. For `not_attempted`, `simplify` to 2 days.

### 4.4 `value_probe`
- **Resolves:** "What do the people who rely on my work actually value?"
- **Design:** Ask 1–3 people who use your output one specific, **openly framed** question. Example: "Of the last three packs, which part did you actually use to make a decision?" No deception.
- **Effort:** 20–40 min.
- **Measures:** the responses, categorized; mentions of judgment content compared with production content; any request for more of X.
- **Branches:**
  - Judgment is valued → `continue` and consider a `visibility_move`.
  - Only production is valued → `modify` the mission toward a leverage + destination rethink.
  - Nobody answers → `simplify` to one person in a normal meeting.
- **Safety:** `stakeholder_exposure = informed_stakeholder`. **Excluded** for operator-attention users (MPR-02).

### 4.5 `market_probe`
- **Resolves:** "What does my target role actually require, where I'd look for it?"
- **Design:** Review 5–8 current postings, or profiles, for the target role in the user's own market. Tally the requirements against the user's task map and capabilities.
- **Effort:** 45–60 min.
- **Measures:** requirements met, partial and missing (counts); recurring requirements (text).
- **Evidence note:** Postings are *indicative* evidence about the user's local market. They are graded E2 personal evidence, not a verified world fact.
- **Branches:**
  - Mostly met → `continue` to a `conversation_probe`.
  - Large gaps → `modify` (a skill_probe on the top gap).
  - Target unclear → `rediagnose`.

### 4.6 `conversation_probe`
- **Resolves:** "What is it actually like, or what does it take, to do X?"
- **Design:** One 20-minute conversation with someone in the target role or an adjacent team, using three prepared questions.
- **Effort:** 40–60 min, including preparation.
- **Measures:** answers to the three questions; one surprise.
- **Safety:** `informed_stakeholder`. The user frames it honestly.

### 4.7 `skill_probe`
- **Resolves:** "Could I do S, and how far am I from it?"
- **Design:** Attempt one bounded, representative task for S (≤ 60 min) and note where you got stuck.
- **Measures:** completion (yes / partial / no); the sticking points (text); a self-rating compared with the prediction.
- **Branches:**
  - Easy → `continue`, since the skill is not the bottleneck.
  - Stuck early → `modify` to a narrower learning step, *tied to that sticking point*.

### 4.8 `visibility_move`
- **Resolves:** "Is my judgment work visible to the people who assess me?"
- **Design:** In the next routine deliverable, add a short, explicit note on the key judgment ("Why I flagged X"). Observe the response.
- **Effort:** 15–30 min.
- **Measures:** any follow-up, question or comment (count and text); whether the note was used.
- **Safety:** It uses normal work channels and the normal level of disclosure. `informed_stakeholder`.

### 4.9 `delegation_test`
- **Resolves:** "Would handing sub-task T to a template, a tool or a colleague free me for Y?"
- **Design:** Define the sub-task, hand it off once, and measure the time freed and the rework.
- **Measures:** minutes freed; rework minutes; quality issue count.
- **Safety:** Only within the user's authority to delegate. The same material rules apply for tools.

## 5. What the user sees (minimum fields for Lane 04)
1. **Title**: the user's task, in their own words.
2. **Why this, for you**: one sentence taken from `relevance`.
3. **What to do**: the steps, with minutes for each.
4. **Before you start, write down**: your prediction.
5. **What to note**: the measures, as a tiny template.
6. **Keep it safe**: the material rule and the stop conditions.
7. **What happens next**: a plain-language summary of the branches.

Everything else stays internal.

## 6. Anti-patterns (these fail review)
| Anti-pattern | Why it fails |
|---|---|
| "Try ChatGPT for a week" | Not bounded, no measure, no hypothesis. |
| "Take an intro AI course" | Not personal, not observable, and the result doesn't change a decision. |
| "Use AI on your client files" | Breaks INV-08. |
| "Ask your boss if your job is safe" | Unsafe framing and exposure. It resolves nothing. |
| An experiment whose only measure is "was it useful?" | Fails the observable-measure rule. |
| Branches written after the result | Invalidates the pre-registration. |

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft, with a 9-archetype library. |
| 0.1-rev1 | 2026-09-29 | `data_class` meaning (FM-08); `declined` status (FM-22); retrospective variant for blocked windows (FM-07, see MPR-13). |
