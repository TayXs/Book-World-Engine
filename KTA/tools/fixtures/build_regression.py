"""Builds the stress-trace regression fixtures (repair R5) in 03_CURRENT_WORK/regression/.

Each folder encodes the *correct* handling of one stress trace from FAILURE_MODE_REVIEW_v0.1 §2
and must pass kta_check.py. tools/test_regression.py then breaks each one to show the
checker catches the wrong handling. ST-2..ST-5 are derived from the simulation fixtures,
so run the sim_*.py builders first (build_all.py does this).
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REG, STD_TRIGGERS, inf, load, meta, progress, rel, tr, trust, ts, write  # noqa: E402


def w(folder, name, doc):
    write(folder, name, doc, root=REG)


# ---------------------------------------------------------------- ST-1 thin task map (FM-18, INV-15)
U = "SIM-ST1"
st1 = {
    "meta": meta(U, 1, "delivered", "2026-10-02"),
    "scope_check": {"result": "in_scope"},
    "goal": {"stated_goal": "Which AI tool should I learn so I don't get left behind?",
             "diagnosed_goal": "Within 12 months, know which parts of this person's actual week are changing, before choosing anything to learn.",
             "divergence_note": "The stated goal is a means (learn a tool); the end is unclear because the person couldn't describe their week in detail.",
             "archetype": "clarify", "horizon_months": 12,
             "success_signals": ["Can name the 2-3 tasks that take most of the week, from a real log"],
             "baseline": {"goal_confidence_0_10": 4, "main_concern": "Vague sense of being left behind.", "captured_at": "2026-10-01"}},
    "context": {"role": {"function": "Marketing coordinator", "seniority_band": "early", "sector_band": "Consumer services", "employment_type": "employee"},
                "time_budget_minutes_per_week": 15, "employer_ai_policy": {"status": "unknown"}, "ai_experience": "tried",
                "preferences": {"format": "checklist"}},
    "task_map": {"tasks": [
        {"id": "T01", "name": "Campaign social posts", "description": "Write and schedule posts for current campaigns.", "output": "Scheduled posts",
         "frequency": "weekly", "time_share": ts("medium", conf="low"),
         "traits": {"predictability": tr(2, conf="low"), "judgment_intensity": tr(2, conf="low"), "friction": tr(1, conf="low")},
         "data_sensitivity": "internal", "ai_current_use": {"level": "tried"}, "confirmed_by_user": True},
        {"id": "T02", "name": "Weekly campaign report", "description": "Pull numbers from the ad platforms into the weekly report.", "output": "Weekly report",
         "frequency": "weekly", "time_share": ts("medium", conf="low"),
         "traits": {"predictability": inf(3, conf="low"), "information_retrieval": inf(3, conf="low"), "friction": tr(3, conf="low")},
         "data_sensitivity": "confidential", "ai_current_use": {"level": "none"}, "confirmed_by_user": True}],
        "coverage_estimate": {"band": "low", "source": "user_stated"}, "map_confidence": "low",
        "unlisted_work_note": "The user said 'meetings and lots of small things' but couldn't list them."},
    "uncertainty_ledger": [
        {"id": "UQ01", "statement": "Where does this person's working week actually go?", "kind": "personal_empirical", "route": "experiment",
         "impact": "high", "blocking": True, "decision_links": ["F1", "AX01"], "task_links": ["T01", "T02"], "status": "open",
         "relevance": rel("You couldn't list most of your week, so any advice now would be a guess.", "T01", "T02")},
        {"id": "UQ02", "statement": "Which tools, if any, may be used with campaign data at this employer?", "kind": "user_context", "route": "ask",
         "impact": "medium", "blocking": False, "decision_links": ["S2"], "task_links": ["T02"], "status": "open",
         "relevance": rel("The weekly report uses confidential campaign numbers.", "T02", "context.employer_ai_policy")},
        {"id": "UQ03", "statement": "Which marketing-coordinator tasks are AI tools changing most, per current evidence?", "kind": "world_fact", "route": "research",
         "impact": "medium", "blocking": False, "decision_links": ["S3"], "task_links": ["T01", "T02"], "status": "open",
         "research": {"question": "What do recent studies or practitioner surveys (last 12 months) report about AI changing entry-level marketing coordination tasks?",
                      "required_strength": "moderate", "freshness": "≤12 months", "preferred_source_types": ["primary_study", "practitioner_report"],
                      "answer_changes": [{"if": "Content drafting changes most", "then": "Look at T01 after the audit"},
                                         {"if": "Reporting changes most", "then": "Look at T02 after the audit"}], "status": "queued"},
         "relevance": rel("Answers the 'left behind' worry with evidence once we know your week.", "goal.baseline")}],
    "mission": {
        "focus_areas": [{"id": "F1", "title": "Map where your week actually goes", "candidate_type": "clarify", "task_ids": ["T01", "T02"], "uncertainty_ids": ["UQ01"],
                         "rationale": "Thin task map (INV-15): only 2 tasks with low coverage, so map-building comes first.", "planner_rule_refs": ["MPR-07", "MPR-11", "MPR-17"], "priority": 1,
                         "relevance": rel("You could only name two tasks, and 'lots of small things'.", "T01", "T02")}],
        "sequence": [
            {"id": "S1", "step_type": "experiment", "description": "Run AX01: log your time for 3 working days.", "targets": ["AX01", "UQ01"], "depends_on": [], "timebox_days": 14, "owner": "user",
             "relevance": rel("A few minutes a day replaces guesses with your own numbers.", "T01", "T02")},
            {"id": "S2", "step_type": "ask", "description": "Find out which tools, if any, are allowed with campaign data.", "targets": ["UQ02"], "depends_on": [], "timebox_days": 14, "owner": "user",
             "relevance": rel("Needed before any test on the report.", "T02")},
            {"id": "S3", "step_type": "research", "description": "Operator checks UQ03.", "targets": ["UQ03"], "depends_on": [], "timebox_days": 14, "owner": "operator",
             "relevance": rel("Evidence for the 'left behind' worry.", "goal.baseline")},
            {"id": "S4", "step_type": "decide", "description": "At check-in, re-run focus selection on the logged week.", "targets": ["AX01"], "depends_on": ["S1"], "timebox_days": 16, "owner": "user",
             "relevance": rel("Your next step is chosen from your real week.", "goal")}],
        "omissions": [{"id": "O1", "what": "Choosing an AI tool to learn", "why_omitted": "We don't yet know which of your tasks matter most.",
                       "revisit_condition": "After the time log shows your biggest tasks.", "relevance": rel("You asked which tool to learn; this is why it waits.", "goal.stated_goal")}],
        "exit_criteria": [{"type": "no_decision_relevant_uncertainty", "statement": "Nothing open would change your next step."},
                          {"type": "user_opt_out", "statement": "You ask to stop."}, {"type": "risk_detected", "statement": "Any risk appears."}],
        "attention_budget": {"user_minutes_planned_total": 30, "plan_weeks": 2}},
    "first_experiment": {
        "id": "AX01", "archetype": "time_audit", "title": "Log your week in 5-minute daily tallies",
        "hypothesis": {"statement": "Campaign posts and the weekly report together take at least half of the working week.",
                       "would_be_wrong_if": "They take under half, or large unlisted work shows up."},
        "targets": {"uncertainty_ids": ["UQ01"], "task_ids": ["T01", "T02"]}, "depends_on": [],
        "relevance": rel("Your map is too thin to plan from; this builds it in 15 minutes total.", "T01", "T02", "context.time_budget_minutes_per_week"),
        "steps": [{"n": 1, "instruction": "At the end of 3 working days, tally roughly how many minutes went to posts, the report, meetings and 'other'.", "minutes": 15}],
        "materials": {"data_class": "none", "description": "Your own tallies; no tool, no work content."},
        "effort": {"minutes_total": 15, "sessions": 3, "window_days": 14},
        "prediction": {"user": "Meetings probably eat more than I think.", "engine": "Expect a large 'meetings and other' share, which means the map needs new tasks."},
        "measures": [{"id": "M1", "what": "Minutes per bucket per day", "how_recorded": "Tally template", "type": "time_minutes"},
                     {"id": "M2", "what": "Work that fits no bucket", "how_recorded": "One line per day", "type": "text_observation"}],
        "learning_criteria": {"confirms_if": "Posts plus report are at least half of the logged time", "disconfirms_if": "They are under half, or unlisted work is large"},
        "branches": [
            {"id": "B1", "condition_type": "confirms", "condition": "Posts plus report dominate", "next_move": "continue", "next_description": "Pick the larger one as focus."},
            {"id": "B2", "condition_type": "disconfirms", "condition": "Unlisted work dominates", "next_move": "rediagnose", "next_description": "Rebuild the task map from the log."},
            {"id": "B3", "condition_type": "null_result", "condition": "Time spread evenly, no dominant task", "next_move": "modify", "next_description": "Group tasks by output and re-run focus selection."},
            {"id": "B4", "condition_type": "inconclusive", "condition": "Fewer than 2 days logged", "next_move": "simplify", "next_description": "One day's tally only."},
            {"id": "B5", "condition_type": "not_attempted", "condition": "Didn't log", "next_move": "simplify", "next_description": "One day's tally only."},
            {"id": "B6", "condition_type": "harm", "condition": "Anything felt wrong", "next_move": "escalate", "next_description": "Operator reviews."}],
        "safety": {"stakeholder_exposure": "none", "reversibility": "reversible", "stop_conditions": ["Record minutes only, never work content."]},
        "alternatives_considered": [{"archetype": "shadow_test", "why_not": "INV-15: no reliable map yet, and the policy is unknown."}],
        "status": "accepted", "status_history": [{"status": "accepted", "at": "2026-10-02"}]},
    "feedback_plan": {"checkin_at_days": 16, "channel": "operator_message", "question_set": "CQ-v0.1", "mission_triggers": STD_TRIGGERS},
    "claims": [], "operator_log": [{"at": "2026-10-02", "path": "meta.status", "change": "approved", "reason": "ST-1 regression: thin-map path (INV-15, micro mode)."}],
    "delivery": {"format": "checklist", "estimated_user_minutes": 5}}
w("ST-1-thin-map", "packet_r1.json", st1)

# ---------------------------------------------------------------- ST-2 prohibitive policy (FM-19)
p = load("SIM-ACC", "packet_r1.json")
p["meta"].update({"packet_id": "MP-SIM-ST2-r1", "user_ref": "SIM-ST2", "status": "active"})
p["context"]["employer_ai_policy"] = {"status": "prohibits", "approved_tools": [], "notes": "Employer policy prohibits AI tools for work; manager discourages AI use."}
ax = p["first_experiment"]
ax["title"] = "Variance commentary: your way vs an AI assistant, off-work, on made-up numbers"
ax["steps"][2]["instruction"] = "Off-work, on a personal device, give an AI assistant the invented table and cause notes; edit until you'd send it. Time it. Never reuse the output at work."
ax["materials"] = {"data_class": "synthetic", "description": "Invented table and notes; off-work practice only; output never used at work.",
                   "tool": {"name": "Personal AI assistant (off-work practice only)", "employer_approved": "no"}}
ax["safety"]["notes"] = "Prohibitive policy (MPR-14, FM-19): off-work practice on synthetic material only; never produce or reuse work deliverables."
L = {u["id"]: u for u in p["uncertainty_ledger"]}
L["UQ01"]["statement"] = "Does the prohibition also cover personal, off-work practice on made-up material?"
p["mission"]["sequence"][0]["description"] = "Ask HR or IT, in a normal channel, whether the policy covers personal off-work practice on made-up material; also ask what 'close should get faster' means."
p["operator_log"] = [{"at": "2026-10-02", "path": "first_experiment.materials", "change": "edited", "reason": "ST-2 regression: prohibitive policy handled as off-work synthetic practice (MPR-14, FM-19)."}]
w("ST-2-prohibits-policy", "packet_r1.json", p)

# ---------------------------------------------------------------- ST-3 two non-attempts in a row (A5)
for name in ("packet_r1.json", "feedback_FB01.json", "decision_AD01.json", "packet_r2.json"):
    w("ST-3-repeat-non-attempt", name, load("SIM-DES", name))
fb2 = copy.deepcopy(load("SIM-DES", "feedback_FB01.json"))
fb2.update({"id": "FB02", "packet_id": "MP-SIM-DES-r2", "experiment_id": "AX02", "collected_at": "2026-10-20",
            "actions_taken": "Didn't get to either sitting.", "blocker_note": "Another busy week.", "checkin_minutes": 3,
            "trust": trust(5), "mission_progress": progress()})
w("ST-3-repeat-non-attempt", "feedback_FB02.json", fb2)
w("ST-3-repeat-non-attempt", "decision_AD02.json", {
    "id": "AD02", "packet_id": "MP-SIM-DES-r2", "feedback_id": "FB02", "decided_at": "2026-10-20", "decided_by": "operator",
    "decision": "rediagnose", "table_rules": ["A5"], "branch_id": "B5",
    "ledger_updates": [], "task_map_updates": [],
    "next": {"summary": "Second non-attempt in a row: run the rediagnose mini-protocol (3 questions, ≤10 min) and offer to stop. Don't push a third audit."},
    "user_informed": True})

# ---------------------------------------------------------------- ST-4 harm (A1)
p = load("SIM-ACC", "packet_r1.json")
p["meta"]["status"] = "active"
w("ST-4-harm", "packet_r1.json", p)
fb = copy.deepcopy(load("SIM-ACC", "feedback_FB01.json"))
fb["harm_report"] = {"occurred": True, "severity": "minor",
                     "description": "Pasted two real figures from last month's pack into the tool before IT had confirmed the data scope; noticed straight away."}
fb["surprises"] = "How easy it was to paste real numbers by habit."
w("ST-4-harm", "feedback_FB01.json", fb)
w("ST-4-harm", "decision_AD01.json", {
    "id": "AD01", "packet_id": "MP-SIM-ACC-r1", "feedback_id": "FB01", "decided_at": "2026-10-14", "decided_by": "operator",
    "decision": "escalate", "table_rules": ["A1"], "branch_id": "B6",
    "ledger_updates": [], "task_map_updates": [],
    "next": {"summary": "Escalation playbook: acknowledge without blame; establish facts; point to the employer's IT or data process; no legal advice; stop this line; log the incident; spec post-mortem."},
    "user_informed": True})

# ---------------------------------------------------------------- ST-5 declined experiment (A18)
p = load("SIM-LOW", "packet_r1.json")
ax = p["first_experiment"]
ax["status"] = "declined"
ax["prediction"]["user"] = None
ax["status_history"] = [{"status": "proposed", "at": "2026-10-02"}, {"status": "declined", "at": "2026-10-02"}]
p["operator_log"].append({"at": "2026-10-02", "path": "first_experiment.status", "change": "edited", "reason": "ST-5 regression: user declined ('not doing homework'); explain and research steps continue (A18)."})
w("ST-5-declined", "packet_r1.json", p)
w("ST-5-declined", "feedback_FB01.json", {
    "id": "FB01", "packet_id": "MP-SIM-LOW-r1", "experiment_id": "AX01", "collected_at": "2026-10-11", "channel": "operator_message",
    "attempt_status": "declined", "actions_taken": "Read the half-page explanation; chose not to try the test.",
    "observations": [], "effort_minutes_actual": 5, "prediction_comparison": "no_prediction", "surprises": "", "blockers": [],
    "harm_report": {"occurred": False, "severity": "none"},
    "belief_update": {"direction": "more_confident", "note": "Seeing my week by task helped more than the headlines."},
    "decision_change": {"status": "not_yet"}, "usefulness_0_10": None, "goal_confidence_0_10": 6,
    "evidence_grade": "E0", "result_class": "not_applicable", "checkin_minutes": 5,
    "trust": trust(7), "mission_progress": progress()})
w("ST-5-declined", "decision_AD01.json", {
    "id": "AD01", "packet_id": "MP-SIM-LOW-r1", "feedback_id": "FB01", "decided_at": "2026-10-11", "decided_by": "operator",
    "decision": "continue", "table_rules": ["A18"], "branch_id": None,
    "ledger_updates": [], "task_map_updates": [],
    "next": {"summary": "Continue with explain and research; offer a smaller 10-minute voice-only version once; do not count this as a non-attempt."},
    "user_informed": True})
print("regression written")
