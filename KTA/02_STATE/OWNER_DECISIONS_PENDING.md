# OWNER DECISIONS

## Pending
**None.** Next owner actions (not decisions): provide the 3 human seed cases to the *isolated* case-generation session, and upload the KTA-REL-0.1 bundle to Drive. See `05_HANDOFFS/RELEASE_KTA-REL-0.1_HANDOFF.md`.

---

## Decided · Lane 02 acceptance checkpoint · 2026-09-29
Source: `03_CURRENT_WORK/KTA_LANE_02_ACCEPTANCE_PACKET_v0.1.md` §8. Registry rows: `04_REGISTRIES/KTA_REGISTRIES_v0.1.xlsx`.

| # | Ruling | Registry |
|---|---|---|
| D1 | **APPROVED, option B.** The Dual-Layer Source of Truth wording (packet §7.4) is adopted.<ul><li>Git is the canonical active development workspace.</li><li>Drive is the canonical governance/release mirror and the independent recovery layer.</li></ul>**Operational mode is manual release:** build and checksum each accepted-milestone bundle, commit and tag it in Git, and hand it to the owner to upload to Drive. Development is **not** blocked on Drive connectivity. Switching to option A (direct sync) later is operational only and does not change the rule. | KTA-004 (CORE) |
| D2 | **CORE principle APPROVED**, and P1 **revised** before promotion. KTA may use coarse, derived, non-confidential workflow quantities: approximate hours per week, frequency, approximate time share, rough counts, self-estimated proportions. KTA must not request any of these:<ul><li>confidential or proprietary organizational figures;</li><li>documents;</li><li>employer, client or customer names;</li><li>account identifiers;</li><li>sensitive internal metrics;</li><li>other protected work information.</li></ul>Prefer abstraction, redaction, ranges and approximate quantities. Anything volunteered that appears confidential is excluded or redacted before LLM drafting. The ruling applies to INV-16, intake guidance, the checker lint, operator guidance and pilot consent. | DEC-007 (CORE), DEC-009 (CURRENT), KTA-006 (CORE) |
| D3 | **APPROVED, option A.** The data-model delta (packet §7.1–7.2) is applied with the Lane 02 acceptance. | KTA-005 (CURRENT) |
| D4 | **APPROVED, option A, with an amendment to refinement #8.** Refined DUAR is the PROVISIONAL primary candidate under V0 evaluation. MAR is retained for comparison, and all supporting and guardrail metrics are retained. **Amendment:** a serious-harm event does *not* invalidate or erase the measured DUAR. DUAR is recorded normally. A qualifying serious-harm event independently triggers the **safety gate**, which may fail, pause or end the pilot or cohort regardless of DUAR. The metric and the safety gate are kept conceptually separate. | DEC-005 (amended, PROVISIONAL), KTA-007 |
| D5 | **APPROVED, option A.** Lane 02 v0.1 is ACCEPTED WITH SPECIFIED REPAIRS R1–R5. The full validation suite must be green before proceeding. | DEC-008 (CURRENT), DEC-010 (PROVISIONAL), KTA-008 |
| D6 | **APPROVED, option A.** The blind/adversarial evaluation design is authorized (EXP-V0-00):<ul><li>The owner provides 3 human-authored seed cases separately.</li><li>The remaining cases are generated in a separate AI session with **no access** to KTA specs, rules, checker, planner or drafting prompt.</li><li>The dev/sealed split is kept.</li><li>Sealed cases are never exposed to the builder before the drafting prompt is frozen.</li><li>Scoring is blind, by a separate evaluator session, with no source labels.</li></ul> | DEC-011 (CURRENT), EXP-V0-00 |

**ID changes from the packet:**
- The North Star amendment got its own change row, KTA-007, so the release moved to KTA-008.
- DEC-011 was added for the blind-evaluation design.
- PARK-004 (independent review) was absorbed into EXP-V0-00 and not registered.

## Earlier history
- Batch 1 (MCP-1..4), raised 2026-09-29, was superseded by D1–D4 above.
