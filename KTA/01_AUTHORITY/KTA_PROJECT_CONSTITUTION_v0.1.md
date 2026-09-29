# KTA PROJECT CONSTITUTION v0.1
## Governance and Continuity Rules

Revision: v0.1-r1, 2026-09-29 (release KTA-REL-0.1). This revision applies owner-approved change KTA-004: session independence and the dual-layer source of truth.

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

### Session Independence Rule
No material project knowledge may depend on a single AI conversation or session, in any tool. When a working session ends or reaches a limit, a replacement session resumes from authoritative project artifacts rather than reconstructing the project from memory.

### Dual-Layer Source of Truth Rule
1. The Git repository (TayXs/Book-World-Engine, folder KTA/) is the canonical active development workspace for code, schemas, tests, specifications, working artifacts and operational state files.
2. Google Drive is the canonical governance and release mirror and the independent recovery layer. It holds, for every accepted milestone, the approved Master Blueprint, Current State, Registries, accepted handoff and a portable release bundle.
3. A release is an owner-accepted milestone with a release ID (KTA-REL-x.y). It exists as a Git tag and as a Drive release folder containing the same bundle, verified by a SHA-256 manifest.
4. Synchronization: at every accepted milestone, update the approved governance files in Git, build the release bundle, tag it, publish the bundle and the governance files to Drive, verify the hashes, and record the release in the Change Registry.
5. Conflict resolution:
   a. Working artifacts (code, schemas, tests, drafts): Git wins. Drive copies are snapshots.
   b. Governance files (Constitution, Blueprint, Current State, Registries): the latest Drive release is authoritative for approved state. A Git difference is valid only if it is backed by a registered, owner-approved change not yet released; otherwise it is moved to a proposal and Git is restored to the release.
   c. An owner edit made directly in Drive is an owner-authored change. It must be imported into Git and registered at the start of the next session, before other work.
   d. If the same governance file changed in both places since the last release, stop; present both versions to the owner; do not merge automatically.
   e. AI memory and conversation history never establish product authority.
6. Recovery: rebuild Git from the latest Drive release bundle plus the Git remote; rebuild Drive from the latest release tag.

### Recovery Protocol
A replacement session should read, in order: KTA CURRENT STATE, KTA MASTER BLUEPRINT, the latest relevant lane handoff, and applicable Registry entries — and, in the Git workspace, the operational state files — then check Git against the latest Drive release per the Dual-Layer rule, and continue from the recorded next task.

### Archive Rule
Superseded, rejected, parked, and historical material should be preserved without competing with current rules. The Archive explains what was tried and why it changed; it does not define current behavior.

### Governing Decisions
- KTA-GOV-001 — Structured Project Governance. Status: CORE.
- KTA-GOV-002 — Session Independence & Continuity. Status: CORE (amended by KTA-004).
- KTA-GOV-003 — Dual-Layer Source of Truth (Git workspace + Drive governance/release mirror). Status: CORE (amended by KTA-004).

### Project Principle
Nothing important should be lost, nothing provisional should masquerade as settled, and no approved change should remain isolated from the rest of the system.
