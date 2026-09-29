# KTA PROJECT CONSTITUTION v0.1
## Governance and Continuity Rules

### Purpose
Protect the Knowledge → Action project from fragmented decisions, lost context, silent rule changes, and chat-dependent memory.

### Authority Hierarchy
1. Core Constitution — highest authority.
2. Current Master Blueprint — defines what is currently true.
3. Approved Change and Decision Registry — records why current rules exist.
4. Lane Specifications — detailed implementation by area.
5. Active Experiments — may inform future rules but do not override current rules.
6. Brainstorming and Exploration — non-authoritative until promoted.
7. Archive — historical evidence only.

### Idea Status System
- CORE — fundamental principle or governance rule.
- CURRENT — currently implemented approach.
- PROVISIONAL — plausible but not sufficiently proven.
- EXPERIMENT — actively being tested.
- PARKED — potentially useful but not relevant now.
- DEPRECATED — previously used and superseded.
- REJECTED — deliberately not adopted.
- ARCHIVED — historical context only.

### Change Control Rule
No material idea becomes part of the product merely because it was discussed. Material ideas must be classified, linked to affected components, and either promoted, tested, parked, rejected, deprecated, or archived.

### Propagation Rule
Every approved change must identify all affected lanes, specifications, data structures, metrics, interfaces, and public promises. A change is incomplete until affected authoritative artifacts are reconciled.

### Evidence Rule
Observations are not automatically rules. Where evidence is needed, an observation becomes a hypothesis, then an experiment, then a decision. Single anecdotes or isolated tool behavior must not silently change CORE or CURRENT rules.

### Pivot Rule
Major pivots must record: previous belief, new evidence or reasoning, what remains valid, what is invalidated, affected systems, and what is archived.

### Chat Independence Rule
No material project knowledge may depend on a single ChatGPT conversation. When a working chat ends or reaches a limit, a replacement chat resumes from authoritative project artifacts rather than reconstructing the project from memory.

### External Source of Truth Rule
Google Drive is the durable external repository for authoritative Knowledge → Action project state. ChatGPT memory and conversation history assist development but do not independently establish product authority.

### Recovery Protocol
A replacement chat should read, in order: KTA CURRENT STATE, KTA MASTER BLUEPRINT, the latest relevant lane handoff, and applicable Registry entries. It should then continue from the recorded next task.

### Archive Rule
Superseded, rejected, parked, and historical material should be preserved without competing with current rules. The Archive explains what was tried and why it changed; it does not define current behavior.

### Governing Decisions
- KTA-GOV-001 — Structured Project Governance. Status: CORE.
- KTA-GOV-002 — Chat Independence & Continuity. Status: CORE.
- KTA-GOV-003 — External Source of Truth using Google Drive. Status: CORE.

### Project Principle
Nothing important should be lost, nothing provisional should masquerade as settled, and no approved change should remain isolated from the rest of the system.
