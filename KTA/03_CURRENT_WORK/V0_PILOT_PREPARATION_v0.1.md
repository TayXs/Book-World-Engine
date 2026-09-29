# V0 HUMAN-ASSISTED PILOT: PREPARATION v0.1
Lane 02 build step 9 of 9 · Hands over to **Lane 07 (Pilots)** and **Lane 05 (Feedback)**

Status: **DRAFT FOR OWNER REVIEW. Nothing here has been launched.** Recruiting participants, contacting anyone, publishing consent terms or collecting real personal data are external actions that need explicit owner approval (`CLAUDE.md`). The items that need a decision are marked **[OWNER]**.

---

## 1. What V0 must answer
The Blueprint defines V0 as one human-assisted, end-to-end mission for working adults adapting to AI-driven work change.

| # | Pilot question | Why it matters | Measured by |
|---|---|---|---|
| Q1 | Do people **attempt** a bounded, pre-registered experiment on their own work? | The loop only works if people take action. | Attempt rate, by archetype and baseline confidence (EXP-V0-02) |
| Q2 | Does the experiment produce a **specific observation** that **changes or confirms a decision**? | This is the core outcome claim. | Both MAR definitions (§6) |
| Q3 | Do users value the KTA packet **more than a generic LLM answer** to the same goal, after the loop? | Differentiation (DEC-004; FM-12) | LLM-Baseline Preference at intake and after check-in (EXP-V0-01) |
| Q4 | Does the engine, or the operator, produce the value? | Needed before building any software | `operator_log`: the rate and type of changes the operator makes to engine drafts |
| Q5 | Is the intake burden acceptable, and are task maps accurate? | Minimum Necessary Attention; AR-07 | Intake minutes; DQ-07 estimates compared with audits (EXP-V0-03) |
| Q6 | Is it safe? | Harm is never acceptable, whatever the other results. | Harm reports, escalations, policy near-misses |

## 2. Cohort **[OWNER]**
| Item | Proposal | Rationale |
|---|---|---|
| Size | 6–8 participants | Enough to see patterns in Q1 to Q4 while one operator can still do the research. It is **not** enough for statistical claims, and results will be reported as such. |
| Mix | At least 2 each from reporting- or analysis-heavy, creative/production-heavy, and relationship-heavy work. At least 1 freelancer. | Mirrors the simulation, so the results can be compared with it. |
| Include | Working adults (18+), currently working, with some concern or curiosity about AI and their work, able to give about 20 min a week for 3 weeks | V0 scope (DEC-002) |
| Exclude | Anyone meeting the D0 out-of-scope flags; the operator's own direct reports; anyone whose participation their employer forbids | Safety and bias |
| Recruitment channel | **[OWNER]** Options: A) the owner's personal network; B) THE OTHER VARIABLE audience (DEC-006); C) both. Recommended: **A first**, because it is lower-risk and allows faster iteration. | Distribution is Lane 07. |
| Incentive | **[OWNER]** None, or a small thank-you. | Paid incentives can inflate attempt rates. |

## 3. Roles
| Role | Who | Does |
|---|---|---|
| Operator | **[OWNER]** The owner, or someone they appoint | Runs intake, reviews and edits packets, sends nudges and check-ins, handles escalation, answers research questions |
| Engine | An LLM following the Lane 02 specs, or the operator by hand | Drafts packets. Its output is saved **before** operator edits, for Q4. |
| Checker | `tools/kta_check.py` | Must pass before any packet reaches `operator_reviewed` |

## 4. Operator runbook (per participant)
| Day | Step | Artifact | Spec |
|---|---|---|---|
| 0 | Consent (§7). Intake D0–D5 (≤15 min), then D6 follow-ups (≤5 min). | Intake notes, deleted after drafting | DIAGNOSTIC_ARCHITECTURE |
| 0 | Capture the **LLM baseline**: paste the participant's own one-line goal into 2 general assistants and save both answers verbatim. Don't show them yet. | `baseline_llm_*.md` | §6 |
| 1 | The engine drafts packet r1. Save it as `packet_r1.engine.json`. | Engine draft | Planner rules |
| 1 | The operator reviews it with the MPR §5 checklist, logs every change, and runs `kta_check.py` until it shows 0 errors. | `packet_r1.json` | Contract, INV-01..15 |
| 1–2 | Deliver the packet: ≤10 min to read, omissions shown. The participant writes their prediction, and the experiment becomes `accepted` or `declined`. | Delivered packet | Contract §5.13 |
| 2–12 | Operator research on the queued `world_fact` items. **Reuse** earlier answers where the question is the same (FM-15). | Research notes → claims | MPR-12 |
| mid | Nudge (one line). | — | Feedback §2 |
| ~9–12 | Check-in with CQ-v0.1 (≤10 min). Apply the decision table. Write the decision record and packet r2. | `feedback_FB01`, `decision_AD01`, `packet_r2` | Feedback §3–7 |
| ~12 | **Comparison moment:** show both LLM baselines next to the packet and ask the preference question (§6). | Preference record | EXP-V0-01 |
| ~21 | Second check-in on r2, then a close-out interview (10 min). | `feedback_FB02`, close-out notes | — |

## 5. Escalation playbook (FM-21)
Triggered by a harm report (A1), a new acute situation (A2), or any operator concern.
1. **Within 1 business day**, acknowledge without blame: "Thanks for telling me; let's sort out next steps."
2. **Establish the facts only:** what happened, what data, which tool, and whose rules apply.
3. **Point to their own process:** the employer's or client's IT, data-protection or HR channel, or the tool's deletion controls. **Give no legal, HR or clinical advice.**
4. For acute situations (A2), use the approved signpost wording (§7) and pause the mission.
5. **Stop that experiment line.** Record `harm_report` and the decision.
6. **Log the incident** in the pilot incident log, with no identifying details.
7. **Post-mortem the spec:** which rule should have prevented it? File a finding (FM-nn) before the next participant starts.
8. **Tell the owner** within 1 business day of any `serious` incident.

## 6. Metrics and comparison
**North Star.** Both definitions are computed until the owner decides MCP-4 (see Feedback logic §9).
- *Current (DEC-005) literal reading:* attempted **and** (usefulness ≥ 6 **or** decision changed or confirmed).
- *Proposed (MCP-4):* attempted **and** evidence grade E2 or higher **and** decision changed or confirmed.

**Diagnostics:**
- attempt rate;
- Attention Cost (minutes per cycle);
- harm and near-miss count;
- operator change rate (Q4);
- time-share estimate error, where an audit exists (EXP-V0-03);
- check-in response rate.

**LLM baseline protocol (AT-3, EXP-V0-01):**
1. Record both baseline answers **verbatim** at intake. Don't show them to the participant yet.
2. At the comparison moment, show the two baselines and the packet, with their order randomized. Ask:
   - "Which would you rather have had at the start?"
   - "Which one actually changed something you did?"
   - "What did each one miss?"
3. Report the answers descriptively. With n = 6–8, this is *signal*, not proof.

**Contrast profiles for the swap test (FM-16):** SIM-ACC, SIM-DES, SIM-SAL and SIM-LOW.

## 7. Consent and data handling: DRAFT **[OWNER approval required before use]**
This is a draft of commitments, not final wording.
- **What we collect:** the packet fields only (task descriptions, time shares, goals, experiment results). **No employer, client or colleague names. No work material.**
- **What we don't keep:** intake notes and transcripts are deleted once the packet is drafted (Diagnostic §10).
- **Where it's stored:** **[OWNER]** Proposed: a private location only the operator can access, using pseudonymous IDs. It is **not** the public git repository. Real participant data must never be committed to this repo.
- **Retention:** **[OWNER]** Proposed: deleted 90 days after the pilot ends. Only anonymized, controlled-vocabulary fields are kept for learning across users (Feedback §8), and only with a separate opt-in.
- **Rights:** a participant can stop at any time and have their data deleted on request.
- **Safety:** KTA never asks anyone to put confidential work material into unapproved tools (MCP-2).
- **Limits:** KTA is not career, legal, financial or mental-health advice. The signpost wording for out-of-scope situations is **[OWNER]**, and should point to local employment support and appropriate support lines.

## 8. Readiness checklist (all must be ✅ before the first participant)
- [ ] Owner decisions MCP-1 to MCP-4 answered (`02_STATE/OWNER_DECISIONS_PENDING.md`)
- [ ] Pilot decisions answered: cohort channel, incentive, operator, storage, retention, signpost wording (batch 2)
- [ ] Consent text finalized and approved
- [ ] One **dry run** with a friendly volunteer, or with the owner playing the participant. Record the intake minutes and packet time.
- [ ] Private data location set up. The `.gitignore` guard is confirmed.
- [ ] Research reuse notes started (FM-15)
- [ ] Engine prompt or template written from the Lane 02 specs, since the engine currently exists only as specs *(this is the next build item; see the handoff)*

## 9. Go / no-go after the pilot (proposed; decided by the owner)
| Signal | Continue toward Lane 06 software | Revise Lane 02 first | Rethink (material) |
|---|---|---|---|
| Attempt rate | ≥ 60% | 30–60% | < 30% |
| MAR (proposed definition) | ≥ 40% of delivered | 20–40% | < 20% |
| LLM-Baseline Preference after the loop | Packet preferred by the majority | Split | Baseline preferred by the majority |
| Operator change rate | Mostly minor edits | Frequent substantive fixes | The operator is effectively writing the packets |
| Harm | 0 serious | — | Any serious incident → pause |

These thresholds are **starting proposals** and are not evidence-based. With n = 6–8, they are guides for judgment, not statistical tests.

## 10. Owner decisions for the pilot: batch 2 (asked after batch 1)
1. Recruitment channel: **A** personal network (recommended) · **B** TOV audience · **C** both
2. Operator: **A** the owner · **B** someone appointed
3. Storage for real data: **A** a private Drive folder (recommended) · **B** another private store
4. Retention: **A** 90 days, plus opt-in anonymized learning (recommended) · **B** delete everything at the end
5. Incentive: **A** none (recommended) · **B** a small thank-you

## Revision log
| Version | Date | Change |
|---|---|---|
| 0.1-draft | 2026-09-29 | First draft. Includes the FM-21 escalation playbook and the FM-15/16 pilot items. |
