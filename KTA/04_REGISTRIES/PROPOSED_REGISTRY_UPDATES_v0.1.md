# PROPOSED REGISTRY UPDATES v0.1

Status: **PROPOSED, NOT APPROVED.** None of these rows has been written to `KTA_REGISTRIES_v0.1.xlsx`. Each row is added only after owner approval, and then the Markdown mirror is regenerated with `tools/render_registries.py`.
Sources: the architecture review (AR-nn), the failure-mode review (FM-nn), and the owner decision batch (`02_STATE/OWNER_DECISIONS_PENDING.md`).

## A. Change Registry (material; each needs owner approval)
| Proposed ID | Area | Observation / Trigger | Proposed Change | Proposed Status | Evidence / Reason | Affected Systems | Depends on |
|---|---|---|---|---|---|---|---|
| KTA-004 | Storage / Continuity | Work moved to Claude Code, which writes to git. The Drive originals aren't reachable from the session (AR-01). | Git repo `KTA/` becomes the canonical working source of truth, with Drive as a milestone mirror. Reword the Chat Independence rule so it covers any AI tool or session. | CORE (amends KTA-002 and KTA-003) | Two unsynchronized stores will drift. | Constitution, Source Manifest, Lanes 00 and 08 | MCP-1 |
| KTA-005 | Architecture | The Blueprint data model lacks TaskMap and other Lane 02 objects (AR-10, AR-04, AR-05). | Reconcile the Blueprint at the Lane 02 handoff: add TaskMap, UncertaintyItem, FeedbackRecord and AdaptationDecision; describe Personalization as a property, not a stage; record the Lane 02/05 interface. | CURRENT | The Propagation Rule | Blueprint; Lanes 02, 03, 04, 05, 06 | MCP-3 |

## B. Decision Registry
| Proposed ID | Decision Area | Decision | Proposed Status | Rationale | Affected Lanes | Validation State | Depends on |
|---|---|---|---|---|---|---|---|
| DEC-007 | Safety / Privacy | KTA never recommends putting confidential employer or client material into unapproved tools. Experiments default to public, synthetic or redacted material. Work-material rules are a required intake item. | CURRENT | AR-08; FM-09, FM-11, FM-19 | 02, 05, 06, 07 | Applied as a restrictive default in the Lane 02 drafts | MCP-2 |
| DEC-005 (amend) | North Star Metric | Operational MAR: attempted **and** evidence grade E2 or higher **and** a decision or behavior changed or confirmed. Add three diagnostics: Attention Cost, Harm/Regret, LLM-Baseline Preference. | PROVISIONAL | AR-15; FM-12 | 05, 07 | Both definitions are computed in the V0 pilot | MCP-4 |
| DEC-008 | Lane 02 Specification | Adopt Mission Generation Engine v0.1 (the Output Contract, Diagnostic Architecture, Task Map, Planner Rules, ActionExperiment, Feedback & Adaptation, at 0.1-rev1) as the Lane 02 specification for the V0 pilot. | PROVISIONAL | Built and stress-tested in steps 1–8; the simulation passed. | 02, 03, 04, 05, 07 | Simulation only; needs V0 evidence | Owner acceptance of the Lane 02 handoff |

## C. Experiment Registry (non-authoritative; activated only when the pilot launches)
| Proposed ID | Hypothesis | Audience / Cohort | Method | Primary Metric | Status |
|---|---|---|---|---|---|
| EXP-V0-01 | After one loop, users value a KTA packet (selection, omissions, a pre-registered experiment) more than a longer generic LLM answer to the same goal. | V0 cohort, 6–8 people | A randomized-order comparison against 2 verbatim LLM baselines at the check-in (Pilot §6) | LLM-Baseline Preference | NOT STARTED |
| EXP-V0-02 | Attempt rate differs by experiment archetype and by baseline confidence. Audit-first designs may feel like homework (FM-14). | V0 cohort | Descriptive comparison | Attempt rate | NOT STARTED |
| EXP-V0-03 | Self-reported time shares (DQ-07) are accurate to within one band for most tasks. | V0 participants who run an audit | Compare DQ-07 estimates with audit results | Band agreement | NOT STARTED |

## D. Parking Lot (non-authoritative)
| Proposed ID | Idea | Why It May Matter | Affected Lanes | Return Condition |
|---|---|---|---|---|
| PARK-001 | Reuse Truthcast's claim extraction, research and "bar" filter (this repo) as a prototype for the Lane 03 Evidence Engine (AR-25) | It already implements a strict evidence filter and plain-language output. | 03, 06 | When Lane 03 specification starts |
| PARK-002 | Reconsider the public mission name "Stay Valuable…" and its threat framing (AR-23) | Users may be leverage-, transition- or clarify-minded. | 01, 04, 07 | After V0 archetype frequencies are known |
| PARK-003 | Soften the Core Promise wording "will determine what matters" (AR-24) | It overclaims certainty compared with the explicit-uncertainty principle. | 01, 07 | Before any public copy |
| PARK-004 | An independent adversarial review of the Lane 02 specs by a separate agent or person (FM-17) | Reduces author bias. | 02, 08 | Before the pilot, if the owner wants it |
| PARK-005 | v0.2 field renames: `first_experiment` → `current_experiment`; `employer_ai_policy` → `work_material_rules` | Clearer semantics (Feedback v0.2 note; FM-10) | 02, 06 | Next contract revision |
