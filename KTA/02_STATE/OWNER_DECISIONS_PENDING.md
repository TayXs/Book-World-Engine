# OWNER DECISIONS PENDING

Batch 1 · raised 2026-09-29 · source: `03_CURRENT_WORK/KTA_ARCHITECTURE_REFINEMENT_REVIEW_v0.1.md`
None of these block Lane 02. Work continues under the current rules until you reply.

**Reply format:** `1A 2A 3A 4A` (the recommended defaults are A)

---

### 1 · Source of truth (AR-01) · changes CORE KTA-GOV-003
- **Change:** Make the git repo folder `KTA/` the canonical project store, with Drive as a milestone mirror. Reword the Chat Independence rule so it covers any AI tool, not only ChatGPT.
- **Why:** Claude Code writes to git. This session can't reach the Drive originals, so the two stores will drift apart.
- **Accept risk:** Drive becomes stale between mirrors.
- **Reject risk:** Two diverging "truths", plus a manual upload every session.
- **A** Repo canonical, Drive mirror (recommended) · **B** Drive stays canonical; you sync the repo to Drive after each checkpoint · **C** Defer

### 2 · Employer and client data safety rule (AR-08) · new CURRENT decision
- **Change:** KTA never recommends putting confidential employer or client data into tools the employer hasn't approved. Experiments default to public, synthetic or redacted material. Employer AI policy becomes a required intake item.
- **Why:** "Try AI on your real task" is the most natural experiment, and it can breach employment, contract or regulatory rules.
- **Accept risk:** Some experiments become a bit less realistic.
- **Reject risk:** Real user harm and a pilot trust incident.
- **A** Adopt as CURRENT (recommended; the drafts already follow it) · **B** Adopt as PROVISIONAL · **C** Reject

### 3 · Blueprint reconciliation at the Lane 02 handoff (AR-10, AR-04, AR-05)
- **Change:** Add these data objects to the Blueprint: TaskMap, UncertaintyItem (covers research questions), FeedbackRecord, AdaptationDecision. Describe personalization as a property of planning, not a separate stage. Record that Lane 02 owns the first experiment and check-in interface and Lane 05 owns ongoing adaptation.
- **Why:** The Blueprint doesn't list a Task Map at all. Its data model lags its own build priority.
- **Accept risk:** Low; it formalizes the Lane 02 drafts.
- **Reject risk:** The authority docs contradict the engine spec.
- **A** Approve now; apply once, at the Lane 02 handoff (recommended) · **B** Review the diff first · **C** Reject

### 4 · Operational North Star definition (AR-15) · changes PROVISIONAL DEC-005
- **Change:** An action counts toward Meaningful Action Rate only if it was attempted, a *specific observation* was recorded (evidence grade E2 or higher), and the user names a decision or behavior it changed or confirmed. Add three pilot diagnostics: Attention Cost (minutes per cycle), Harm/Regret reports, and LLM-Baseline Preference.
- **Why:** The current wording is satisfied by "felt useful". That is easy to inflate and doesn't separate KTA from a chatbot.
- **Accept risk:** Lower headline numbers.
- **Reject risk:** A pilot "success" that proves nothing.
- **A** Adopt for V0 pilot (recommended) · **B** Adopt only the diagnostics · **C** Keep current wording

---
_Decisions answered: none yet._
