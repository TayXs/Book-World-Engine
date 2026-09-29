# KTA LANE 02 — MISSION GENERATION ENGINE v0.1
## External-AI Continuation Brief

### Authorized Work
Continue the locked Knowledge → Action project by designing **Mission Generation Engine v0.1**.

Do not restart product ideation from zero. Do not replace the locked product thesis merely because another design is possible. You may identify risks or propose improvements, but material changes must be classified under the Constitution rather than silently adopted.

### Why This Is First
The product should not begin with app code or a generic onboarding questionnaire. First define the contract for turning a messy human goal plus minimum necessary context into a structured, evidence-aware mission.

### Build Order
1. Mission Generation Output Contract
2. Diagnostic Question Architecture
3. Task Map Schema
4. Mission Planner Decision Rules
5. ActionExperiment Schema
6. Feedback & Adaptation Logic
7. Three-user simulation
8. Revision based on failure modes
9. Prepare V0 human-assisted pilot

### Mission Generation Output Contract
A successful mission packet should be capable of containing:
1. Goal Definition — what the person is actually trying to change or achieve.
2. Context & Constraints — relevant experience, time, existing capabilities, limitations and preferences.
3. Task Map — what the person actually does, not merely their job title.
4. Known Unknowns / Uncertainties — missing context that materially affects the mission.
5. Knowledge Gaps — what the person must understand to make a better decision.
6. Research Questions — factual questions that must be independently investigated rather than assumed.
7. Mission Architecture — what should be learned or explored, sequence, and what should be deliberately excluded.
8. Personal Relevance Map — why each mission element matters to this user.
9. First ActionExperiment — smallest useful real-world action that reduces uncertainty or creates progress.
10. Feedback Criteria — what result, obstacle or observation determines the next step.

### Required Design Principle
Work backward from outputs to minimum necessary diagnostic inputs. Every intake question must have a clear downstream use. Do not create a long questionnaire merely because more context is available.

### Diagnostic Architecture
Privilege actual tasks and workflows over occupational labels. Questions should be adaptive and only ask follow-ups when the answer can change mission construction.

Candidate prompts include:
- What are the main things you actually do during a typical work week?
- Which tasks take the most time?
- Which require judgment rather than following a repeatable process?
- Which are repetitive?
- Which outcomes are you personally accountable for?
- What concerns you most about AI changing your work?
- What outcome do you want in the next 1–3 years?
- How much time can you realistically invest in adapting?

### Task Map
Do not assign fabricated automation-risk percentages. Lane 02 describes the user's work; Lane 03 evaluates relevant claims against evidence.

Candidate dimensions:
- task name / description
- frequency
- time burden
- predictability / repetition
- information retrieval burden
- analysis intensity
- judgment intensity
- communication / relationship intensity
- accountability
- creativity / synthesis
- tool/system dependency
- perceived pain/friction
- future-value relevance
- evidence-required flags

### Mission Planner
Answer: What does this person need to understand, investigate or test next — and what can be safely omitted for now?

Personalization means selection, sequencing, omission and adaptation, not cosmetic rewriting.

### First ActionExperiment
Do not default to advice lists or courses. Ask: What important uncertainty can be reduced cheaply, safely and meaningfully?

Recommended structure:
- hypothesis
- user-specific reason
- action
- effort/time
- expected observation
- success/learning criteria
- branch conditions for next step
- safety/privacy constraints
- status

### Feedback & Adaptation Logic
Capture more than completion:
- attempted?
- completed / partial / not attempted?
- what happened?
- what surprised the user?
- what blocked them?
- what changed our understanding?
- does the mission continue, modify, investigate further, simplify, change intervention, or stop?

### Three-User Simulation
Before serious software, simulate:
- Accountant — reconciliation/reporting heavy
- Graphic designer — creative production/client interaction heavy
- Sales professional — relationship heavy with research/admin overhead

Pass condition: materially different missions and experiments based on actual context.

Failure condition: generic convergence such as “learn AI, improve communication, use AI tools, focus on human skills.”

### V0 Boundary
Do not build social network, gamification, course marketplace, broad multi-domain expansion, enterprise suite, creator suite, or fully automated app. The first proof is a human-assisted end-to-end mission.

### Expected Deliverables
1. MISSION_GENERATION_OUTPUT_CONTRACT_v0.1
2. DIAGNOSTIC_ARCHITECTURE_v0.1
3. TASK_MAP_SCHEMA_v0.1
4. MISSION_PLANNER_RULES_v0.1
5. ACTION_EXPERIMENT_SCHEMA_v0.1
6. FEEDBACK_ADAPTATION_LOGIC_v0.1
7. THREE_USER_SIMULATION_v0.1
8. LANE_02_HANDOFF_v0.1
9. Proposed Registry updates, clearly labeled and not silently treated as approved unless owner authorization is given.
