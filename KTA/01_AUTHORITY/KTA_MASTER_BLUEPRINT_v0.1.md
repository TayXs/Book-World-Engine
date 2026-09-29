# KNOWLEDGE → ACTION — MASTER BLUEPRINT v0.1
## Current Product Definition

Revision: v0.1-r1, 2026-09-29 (release KTA-REL-0.1). This revision applies owner-approved changes KTA-005 (data model and architecture), KTA-006 (the Confidential Information Boundary), KTA-007 (the North Star candidate) and KTA-008 (Lane 02 acceptance).

### Product Thesis
Knowledge → Action helps a person move from uncertainty to a useful real-world outcome by diagnosing their situation, determining what matters, grounding important conclusions in evidence, recommending a small action, observing the result, and adapting what happens next.

### Core Promise
Tell us what you are trying to change. The system will determine what matters, explain it clearly, show the basis for important conclusions, and help you take the next useful action.

### Initial Market
Working adults adapting to AI-driven changes in their profession.

### First Mission
Stay Valuable as AI Changes My Work.

### Primary User Problem
The user does not primarily lack information. The user lacks prioritization, trustworthy interpretation, personal relevance, and a clear next action.

### Product Outcome
The product is successful when the user makes a better decision, changes a useful behavior, completes a meaningful experiment, or achieves another observable improvement. Consumption alone is not success.

### Core Loop
Goal → Diagnosis → Mission → Evidence → Explanation → Action → Feedback → Adaptation.

### Product Differentiation
A general LLM primarily answers the question the user asks. Knowledge → Action is designed to diagnose the underlying goal, map the user’s context, determine what must be learned, verify important claims, prioritize what applies, recommend a small intervention, observe the result, and adapt the next step. The consumer should not need advanced prompt-engineering skills.

### System Architecture
Goal Intake (with scope triage) → Context and Task Mapper → Mission Planner (routes each uncertainty to ask / experiment / research / explain) → Research Engine → Evidence Engine → Explanation Engine → Action Engine → User Experiment → Feedback Engine → Mission Adaptation.
Personalization (selection, sequencing, omission, adaptation) is a property of the Mission Planner and Mission Adaptation, not a separate stage. In V0 these are logical functions performed by an operator with LLM assistance, not separate services. Lane 02 owns the first ActionExperiment and check-in interface; Lane 05 owns ongoing adaptation and cross-user intervention intelligence.

### Core Product Principles
- Consumer Outcome First. Optimize for useful real-world progress rather than engagement.
- Diagnose Before Prescribing. Understand the person’s situation before recommending an intervention.
- Evidence Before Recommendation. Important factual conclusions should be investigated before they become advice.
- Action Over Information. Understanding should lead toward an appropriate next action when action is useful.
- Feedback Before Next Prescription. Where possible, observe the result before deciding the next intervention.
- Minimum Necessary Attention. Use the least amount of the user’s attention needed to create understanding and progress.
- No Prompt-Engineering Burden. The product handles decomposition, research, follow-up logic, and prioritization for the consumer.
- Model Independence. The product should improve as underlying models improve and should not depend permanently on one provider.
- Privacy by Minimization. Collect only context materially necessary to improve the user’s outcome.
- Confidential Information Boundary (CORE). KTA must never require, request or encourage a person to enter confidential employer, client, customer or other organizational information into an AI environment its owner has not approved — including KTA itself. KTA works from abstraction, redaction and the minimum necessary context.

### Current Data Objects
UserProfile (within the mission context). Goal. Mission (versioned Mission Packet). TaskMap. UncertaintyItem (incl. ResearchQuestion). EvidenceClaim. ActionExperiment. FeedbackRecord. AdaptationDecision. Outcome (aggregate, derived from FeedbackRecords, AdaptationDecisions and mission exits).
Definitions: Lane 02 specifications in `03_CURRENT_WORK/` and schemas in `03_CURRENT_WORK/schemas/`.

### Trust Layer
Important claims should carry source provenance, evidence strength, freshness, uncertainty, limitations, and relevance to the user. The system should explain why a conclusion deserves trust rather than asking the user to trust the AI.

### Personalization
Personalization means selection, sequencing, omission, and adaptation based on the user’s context and observed outcomes. It is not cosmetic rewriting.

### Experience
Audio is a major interface but not the product itself. The product may use audio, text, diagrams, checklists, or other formats according to whichever medium produces understanding with the least unnecessary attention.

### Current North Star
PROVISIONAL, under V0 evaluation — not locked. Primary candidate: Decision-Useful Action Rate (DUAR) — of all recommended ActionExperiments (including declined and unanswered ones), the share that the user attempted AND that produced interpretable evidence (graded E2 or higher, not inconclusive; null results count) or an observed change in one of the user's success signals (E2 or higher) AND that the next AdaptationDecision used under a result-driven rule. Reported with a per-user companion and always alongside Real-World Decision Rate.
Meaningful Action Rate is retained as a comparison metric until the V0 decision gate.
Supporting metrics: attempt, completion, decline, evidence quality, usefulness, trust, mission progress, real-world decision change, attention cost, high-impact targeting.
Safety gate (separate from all metrics): a qualifying serious-harm event independently triggers the safety gate and may fail, pause or terminate a pilot or cohort regardless of DUAR. DUAR is still recorded normally.

### Current Development Stage
Pre-V0. Lane 02 Mission Generation Engine v0.1 accepted with specified repairs (2026-09-29); repairs R1–R5 completed; released as KTA-REL-0.1.

### V0 Scope
Build and test one human-assisted end-to-end mission for working adults adapting to AI-driven work change. The initial system must support intake, diagnostic reasoning, task mapping, mission planning, evidence-backed explanation, one ActionExperiment, check-in, and adaptation.

### Excluded from V0
Social network, gamification, large course marketplace, broad multi-domain expansion, enterprise tooling, creator tooling, and a fully automated self-service app.

### Distribution Relationship
THE OTHER VARIABLE may serve as a public discovery and acquisition layer. Public content introduces important problems; Knowledge → Action provides individual diagnosis, mission guidance, action, feedback, and adaptation.

### Current Build Priority
V0 readiness: blind/adversarial evaluation case preparation (isolated session) → engine drafting prompt → freeze → blind/adversarial evaluation on unseen cases → repairs → small human-assisted pilot → decision gate before application development.
