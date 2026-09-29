# KTA CURRENT STATE
## Recovery Snapshot

### Version
KTA v0.1, release **KTA-REL-0.1** (2026-09-29)

### Stage
Pre-V0. Lane 02 Mission Generation Engine v0.1 was accepted with specified repairs on 2026-09-29. Repairs R1–R5 are complete, the validation suite is green, and the release is KTA-REL-0.1.

### Current Objective
V0 readiness, in this order: blind/adversarial evaluation case preparation → engine drafting/compiler prompt → freeze → blind evaluation → repairs → small human-assisted pilot → decision gate.

### Current Market
Working adults adapting to AI-driven changes in their profession.

### First Mission
Stay Valuable as AI Changes My Work.

### Current Core Loop
Goal → Diagnosis → Mission → Evidence → Explanation → Action → Feedback → Adaptation.

### Current Build Area
Blind evaluation case preparation (EXP-V0-00, owner plus an isolated session), then the engine drafting/compiler prompt.

### Approved Governance
- KTA-GOV-001: Structured Project Governance.
- KTA-GOV-002: Session Independence & Continuity (amended, KTA-004).
- KTA-GOV-003: Dual-Layer Source of Truth, with the Git workspace plus a Drive governance/release mirror (amended, KTA-004). The operational mode is manual release.
- DEC-007: Confidential Information Boundary (CORE).

### Current North Star
Decision-Useful Action Rate is the PROVISIONAL primary candidate under V0 evaluation. Meaningful Action Rate is retained for comparison. It is not locked. The safety gate is separate from all metrics.

### Active Experiment
EXP-V0-00 blind/adversarial evaluation: PLANNED (protocol `03_CURRENT_WORK/BLIND_EVAL_PROTOCOL_v0.1.md`).

### Known Blockers
None blocking development. The Drive mirror of KTA-REL-0.1 is pending the owner's manual upload (D1 option B).

### Next Work
1. Owner: upload the release bundle to Drive.
2. Owner: write the 3 seed cases and run the isolated case-generation session; hand the dev set to the builder.
3. Builder: drafting/compiler prompt, after owner go-ahead.

### Pending Material Proposals
None.

### Recovery Instruction
When a new AI session replaces an old one, read this Current State document first, then the Master Blueprint, then the latest relevant lane handoff and Registry entries. In the Git workspace, also read 02_STATE/PROJECT_STATE.json, PROGRESS.md and NEXT_ACTION.md. If the Git workspace and the latest Drive release disagree, apply the sync rule in the Constitution.
