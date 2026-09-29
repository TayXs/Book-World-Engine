"""KTA Lane 02 checker: validates Mission Packets and related records.

It checks:
  * JSON Schema structure (03_CURRENT_WORK/schemas/*.schema.json)
  * the cross-field invariants INV-01..INV-14 from MISSION_GENERATION_OUTPUT_CONTRACT_v0.1
  * planner-rule warnings (MPR-*) that need human judgment
  * feedback / adaptation-decision consistency (FEEDBACK_ADAPTATION_LOGIC_v0.1)
  * diagnostic-registry traceability (DIAGNOSTIC_ARCHITECTURE_v0.1)
  * generic-convergence lint (AT-2) and a swap-test aid (AT-1)

Usage (from the repo root or from KTA/):
    pip install jsonschema
    python KTA/tools/kta_check.py                 # registry + every simulation folder
    python KTA/tools/kta_check.py path/to/packet_r1.json [...]
    python KTA/tools/kta_check.py --registry
    python KTA/tools/kta_check.py --swap KTA/03_CURRENT_WORK/simulation

File naming decides the record type: packet_*.json, feedback_*.json, decision_*.json.
Exit code 1 if any ERROR was found. WARN lines need human review and do not fail.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

KTA = Path(__file__).resolve().parent.parent
WORK = KTA / "03_CURRENT_WORK"
SCHEMAS = WORK / "schemas"
SIMULATION = WORK / "simulation"
REGISTRY_FILE = WORK / "diagnostic_question_registry_v0.1.json"

KIND_ROUTES = {
    "user_context": {"ask", "defer"},
    "personal_empirical": {"experiment", "ask", "defer"},
    "world_fact": {"research", "defer"},
    "understanding_gap": {"explain", "defer"},
}
SAFE_DATA = {"none", "public", "synthetic", "redacted_nonconfidential"}
WORK_DATA = {"internal", "confidential", "regulated"}
PAST_ACCEPTED = {"scheduled", "in_progress", "completed", "partial", "not_attempted", "abandoned"}
OVERRIDE_RULES = {"A1", "A2", "A3", "A4", "A5"}  # may override the pre-agreed branch

FORBIDDEN_KEY = re.compile(
    r"automation_risk|risk_score|replace(ment)?_prob|automatable|employer_name|client_name|colleague_name|salary",
    re.I,
)
FORBIDDEN_VALUE = [
    re.compile(r"\b\d{1,3}\s?%\s*(automat|replac|exposure|risk|chance)", re.I),
    re.compile(r"(automat\w*|replac\w*)\s+(risk|probability|likelihood|chance)\s*(of|is|:)?\s*\d", re.I),
]
GENERIC_PATTERNS = [
    r"\blearn(ing)? (about )?ai\b", r"\b(learn|use|adopt|master|try|explore) (new |more |the latest |some )?ai tools?\b", r"\bimprove (your )?communication\b",
    r"\bcommunication skills\b", r"\bhuman skills\b", r"\bsoft skills\b", r"\btake an? .*course\b",
    r"\bonline course\b", r"\bupskill", r"\bembrace ai\b", r"\bstay curious\b", r"\bkeep learning\b",
    r"\bstay up[- ]to[- ]date\b", r"\bnetwork more\b", r"\bpersonal brand\b", r"\bprompt engineering\b",
    r"\bfuture[- ]proof\b",
]
STOPWORDS = set("""a an the and or of to in on for with your you my i is are be this that it as at by from
into how what which who whether can could would does do did vs versus than more less one two per each own
its their them they we our not no yes if then when test probe check""".split())


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def err(self, where, msg):
        self.errors += 1
        print(f"  ERROR [{where}] {msg}")

    def warn(self, where, msg):
        self.warnings += 1
        print(f"  WARN  [{where}] {msg}")


# ---------------------------------------------------------------- schemas
def load_schemas():
    schemas, resources = {}, []
    for f in sorted(SCHEMAS.glob("*.schema.json")):
        s = json.loads(f.read_text())
        schemas[f.name] = s
        resources.append((s["$id"], Resource.from_contents(s)))
    return schemas, Registry().with_resources(resources)


SCHEMA_BY_PREFIX = {
    "packet": "mission_packet.schema.json",
    "feedback": "feedback_record.schema.json",
    "decision": "adaptation_decision.schema.json",
}


def schema_validate(doc, schema_name, schemas, registry, rep, where):
    v = Draft202012Validator(schemas[schema_name], registry=registry)
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in e.absolute_path) or "(root)"
        rep.err(where, f"schema {path}: {e.message[:200]}")


# ---------------------------------------------------------------- helpers
def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else k)
            yield ("key", f"{path}.{k}" if path else k, k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield ("str", path, obj)


def packet_ids(p):
    ids = {}
    def add(i, kind):
        ids.setdefault(i, []).append(kind)
    for t in (p.get("task_map") or {}).get("tasks", []):
        add(t["id"], "task")
    for u in p.get("uncertainty_ledger", []) or []:
        add(u["id"], "uncertainty")
    m = p.get("mission") or {}
    for f in m.get("focus_areas", []):
        add(f["id"], "focus")
    for s in m.get("sequence", []):
        add(s["id"], "step")
    for o in m.get("omissions", []):
        add(o["id"], "omission")
    if p.get("first_experiment"):
        add(p["first_experiment"]["id"], "experiment")
    for c in p.get("claims", []):
        add(c["id"], "claim")
    ctx = p.get("context") or {}
    for c in ctx.get("constraints", []):
        add(c["id"], "constraint")
    for c in ctx.get("capabilities", []):
        add(c["id"], "capability")
    return ids


def ref_ok(ref, ids, p):
    if ref in ids:
        return True
    if ref == "goal" or (ref.startswith("goal.") and ref[5:] in (p.get("goal") or {})):
        return True
    if ref.startswith("context.") and ref[8:] in (p.get("context") or {}):
        return True
    return False


def generic_hits(text):
    return [pat for pat in GENERIC_PATTERNS if re.search(pat, text, re.I)]


# ---------------------------------------------------------------- packet invariants
def check_packet(p, rep, where):
    scope = p["scope_check"]["result"]
    body = ["task_map", "mission", "first_experiment"]
    required_in_scope = body + ["goal", "context", "uncertainty_ledger", "feedback_plan"]

    # INV-01 scope
    if scope == "out_of_scope":
        for k in body:
            if k in p:
                rep.err(where, f"INV-01 out_of_scope packet must not contain '{k}'")
        if not p["scope_check"].get("note"):
            rep.err(where, "INV-01 out_of_scope packet needs a signpost note")
        return
    missing = [k for k in required_in_scope if k not in p]
    if missing:
        rep.err(where, f"INV-01 in-scope packet missing {missing}")
        return

    ids = packet_ids(p)
    # INV-02 uniqueness
    for i, kinds in ids.items():
        if len(kinds) > 1:
            rep.err(where, f"INV-02 duplicate id {i} ({kinds})")

    tasks = {t["id"]: t for t in p["task_map"]["tasks"]}
    ledger = {u["id"]: u for u in p["uncertainty_ledger"]}
    m, ax, ctx = p["mission"], p["first_experiment"], p["context"]

    def need(ref, kind_hint, ctx_where):
        if not ref_ok(ref, ids, p):
            rep.err(where, f"INV-02 {ctx_where} references unknown {kind_hint} '{ref}'")

    # INV-02/03 references + grounding
    relevance_holders = (
        [("focus " + f["id"], f) for f in m["focus_areas"]]
        + [("step " + s["id"], s) for s in m["sequence"]]
        + [("omission " + o["id"], o) for o in m["omissions"]]
        + [("uncertainty " + u["id"], u) for u in p["uncertainty_ledger"]]
        + [("experiment " + ax["id"], ax)]
    )
    for label, el in relevance_holders:
        for r in el["relevance"]["grounded_in"]:
            need(r, "grounding", f"{label}.relevance")
        if generic_hits(el["relevance"]["why_for_this_user"]):
            rep.warn(where, f"AT-2 generic language in {label}.relevance: {el['relevance']['why_for_this_user'][:80]!r}")
    for f in m["focus_areas"]:
        for t in f["task_ids"]:
            need(t, "task", f"focus {f['id']}")
        for u in f.get("uncertainty_ids", []):
            need(u, "uncertainty", f"focus {f['id']}")
    for s in m["sequence"]:
        for t in s["targets"]:
            need(t, "target", f"step {s['id']}")
        for d in s.get("depends_on", []):
            need(d, "step", f"step {s['id']}")
    for u in p["uncertainty_ledger"]:
        # Resolved/dropped items keep links to elements of earlier revisions as history (FM-01).
        if u["status"] in {"resolved", "dropped"}:
            continue
        for d in u["decision_links"]:
            need(d, "element", f"uncertainty {u['id']}.decision_links")
        for t in u.get("task_links", []):
            need(t, "task", f"uncertainty {u['id']}.task_links")
    for t in tasks.values():
        for key in ("exposure_hypothesis", "future_value"):
            uid = (t.get(key) or {}).get("uncertainty_id")
            if uid:
                need(uid, "uncertainty", f"task {t['id']}.{key}")
                if uid in ledger and ledger[uid]["kind"] != "world_fact":
                    rep.err(where, f"INV-02 task {t['id']}.{key} must link a world_fact item, {uid} is {ledger[uid]['kind']}")
        for uid in t.get("evidence_flags", []):
            need(uid, "uncertainty", f"task {t['id']}.evidence_flags")
    for c in p["claims"]:
        if c.get("uncertainty_id"):
            need(c["uncertainty_id"], "uncertainty", f"claim {c['id']}")
    for x in ax["targets"]["uncertainty_ids"] + ax["targets"]["task_ids"] + ax.get("depends_on", []):
        need(x, "target", f"experiment {ax['id']}")

    # INV-04 omissions (schema enforces >=1; kept explicit)
    if not m["omissions"]:
        rep.err(where, "INV-04 at least one omission required")

    # INV-05 targeting
    exp_targets = [ledger[u] for u in ax["targets"]["uncertainty_ids"] if u in ledger]
    if not any(u["status"] == "open" and u["route"] == "experiment" for u in exp_targets):
        rep.err(where, "INV-05 experiment must target >=1 open uncertainty with route=experiment")
    if all(ms["type"] == "rating_0_10" for ms in ax["measures"]):
        rep.err(where, "INV-05 experiment needs >=1 measure that is not rating_0_10")

    # INV-06 evidence gate
    for u in ax.get("depends_on", []):
        if u in ledger and ledger[u]["kind"] == "world_fact" and ledger[u]["status"] == "open":
            rep.err(where, f"INV-06 experiment depends on open world_fact {u}")
    for c in p["claims"]:
        if c["claim_type"] == "world_fact" and c["evidence_status"] != "verified" and c["shown_as"] != "hypothesis":
            rep.err(where, f"INV-06 claim {c['id']} is an unverified world_fact but shown_as={c['shown_as']}")
        if c["evidence_status"] == "verified" and not c.get("evidence_ref"):
            rep.err(where, f"INV-06 claim {c['id']} marked verified without evidence_ref")
        if c["claim_type"] == "personal_evidence" and c["evidence_status"] != "user_local":
            rep.warn(where, f"claim {c['id']} personal_evidence should be evidence_status=user_local")

    # INV-07 budget
    budget = ctx["time_budget_minutes_per_week"]
    weeks = math.ceil(ax["effort"]["window_days"] / 7)
    if ax["effort"]["minutes_total"] > budget * weeks:
        rep.err(where, f"INV-07 experiment {ax['effort']['minutes_total']} min > budget {budget}/wk x {weeks} wk")
    ab = m["attention_budget"]
    if ab["user_minutes_planned_total"] > budget * ab["plan_weeks"]:
        rep.err(where, f"INV-07 planned attention {ab['user_minutes_planned_total']} > {budget} x {ab['plan_weeks']}")
    step_sum = sum(s["minutes"] for s in ax["steps"])
    if abs(step_sum - ax["effort"]["minutes_total"]) > max(5, 0.1 * ax["effort"]["minutes_total"]):
        rep.err(where, f"INV-07 step minutes sum {step_sum} != minutes_total {ax['effort']['minutes_total']} (±10%)")
    if ab["user_minutes_planned_total"] < ax["effort"]["minutes_total"]:
        rep.err(where, "INV-07 planned attention is smaller than the experiment effort alone")

    # INV-08 safety
    pol = ctx["employer_ai_policy"]
    mat = ax["materials"]
    if mat["data_class"] in WORK_DATA:
        tool = mat.get("tool") or {}
        ok = (
            pol["status"] == "allows_listed_tools"
            and tool.get("employer_approved") == "yes"
            and tool.get("name") in pol.get("approved_tools", [])
        )
        if not ok:
            rep.err(where, f"INV-08 {mat['data_class']} material requires an employer-approved listed tool (policy={pol['status']})")
    elif mat["data_class"] not in SAFE_DATA:
        rep.err(where, f"INV-08 unknown data_class {mat['data_class']}")
    if scope == "in_scope_operator_attention" and ax["safety"]["stakeholder_exposure"] != "none":
        rep.err(where, "INV-08/MPR-02 operator-attention users get no stakeholder-facing experiments")
    for t in ax["targets"]["task_ids"]:
        if t in tasks and tasks[t]["data_sensitivity"] in {"confidential", "regulated"} and mat["data_class"] in WORK_DATA and pol["status"] != "allows_listed_tools":
            rep.err(where, f"INV-08 task {t} is {tasks[t]['data_sensitivity']}; experiment would use work material")

    # INV-09 ledger hygiene
    targeted = set(ax["targets"]["uncertainty_ids"])
    for s in m["sequence"]:
        targeted.update(s["targets"])
    for u in p["uncertainty_ledger"]:
        if u["route"] not in KIND_ROUTES[u["kind"]]:
            rep.err(where, f"INV-09 {u['id']} kind={u['kind']} cannot take route={u['route']}")
        if u["status"] == "open" and u["impact"] == "high" and u["id"] not in targeted:
            rep.err(where, f"INV-09 open high-impact {u['id']} is not targeted by a step or the experiment (or deferred)")
        if u["status"] == "open" and u["route"] == "defer":
            rep.err(where, f"INV-09 {u['id']} route=defer must have status=deferred")
    if not any(s["step_type"] == "experiment" and ax["id"] in s["targets"] for s in m["sequence"]):
        rep.err(where, f"INV-09 no sequence step of type experiment targets {ax['id']}")

    # INV-10 forbidden content (whole packet)
    for kind, path, val in walk(p):
        if kind == "key" and FORBIDDEN_KEY.search(val):
            rep.err(where, f"INV-10 forbidden field '{path}'")
        if kind == "str":
            for rx in FORBIDDEN_VALUE:
                if rx.search(val):
                    rep.err(where, f"INV-10 risk-percentage language at {path}: {val[:80]!r}")

    # INV-11 revision chain
    meta = p["meta"]
    if meta["revision"] > 1 and not (meta.get("parent_packet_id") and meta.get("decision_ref")):
        rep.err(where, "INV-11 revision > 1 needs parent_packet_id and decision_ref")
    if not meta["packet_id"].endswith(f"-r{meta['revision']}"):
        rep.err(where, "INV-11 packet_id suffix must match revision")

    # INV-12 branch coverage
    types = {b["condition_type"] for b in ax["branches"]}
    for needed in ("not_attempted", "null_result"):
        if needed not in types:
            rep.err(where, f"INV-12 experiment branches missing '{needed}'")
    for recommended in ("confirms", "disconfirms", "harm"):
        if recommended not in types:
            rep.warn(where, f"experiment branches lack recommended '{recommended}'")

    # INV-13 check-in timing and triggers
    fp = p["feedback_plan"]
    if fp["checkin_at_days"] > ax["effort"]["window_days"] + 3:
        rep.err(where, "INV-13 check-in later than experiment window + 3 days")
    decisions = {t["decision"] for t in fp["mission_triggers"]}
    for needed in ("escalate", "rediagnose"):
        if needed not in decisions:
            rep.err(where, f"INV-13 mission_triggers missing '{needed}'")

    # INV-14 pre-registration
    if (ax["status"] != "proposed" or meta["status"] in {"active"}) and not (ax["prediction"].get("user") or "").strip():
        rep.err(where, f"INV-14 experiment status={ax['status']} requires prediction.user")

    # ---------------- planner warnings (human judgment)
    archetype = p["goal"]["archetype"]
    ctypes = {f.get("candidate_type") for f in m["focus_areas"]}
    if archetype in {"protect", "leverage"} and "anchor" not in ctypes and "light_touch" not in ctypes:
        rep.warn(where, "MPR-09 protect/leverage mission has no anchor focus; packet should say why")
    for f in m["focus_areas"]:
        if not f.get("candidate_type"):
            rep.warn(where, f"focus {f['id']} has no candidate_type")
        if f["priority"] == 1:
            t0 = [tasks[t] for t in f["task_ids"] if t in tasks]
            if t0 and all(t["time_share"]["band"] == "small" for t in t0) and not any(
                t["traits"].get("accountability", {}).get("value") == 3 for t in t0
            ) and archetype != "transition":
                rep.warn(where, f"MPR-03 priority-1 focus {f['id']} rests only on small-share tasks")
        if f.get("candidate_type") == "leverage" and not any(
            x.get("candidate_type") in {"anchor", "transition"} for x in m["focus_areas"]
        ):
            if not any("destination" in (u["statement"] + json.dumps(u.get("current_belief", ""))).lower() for u in p["uncertainty_ledger"]):
                rep.warn(where, f"MPR-04 leverage focus {f['id']} has no anchor/transition focus and no destination item")
    if ax["archetype"] in {"shadow_test", "delegation_test"}:
        for t in ax["targets"]["task_ids"]:
            if tasks.get(t, {}).get("traits", {}).get("identity_value", {}).get("value") == 3:
                rep.warn(where, f"MPR-08 {ax['archetype']} targets identity-protected task {t}; needs explicit user opt-in")
    if ax["effort"]["minutes_total"] > 90:
        rep.warn(where, f"MPR-13 experiment effort {ax['effort']['minutes_total']} min > 90")
    if budget < 30 and (len(m["focus_areas"]) > 1 or ax["effort"]["minutes_total"] > 30):
        rep.warn(where, "MPR-17 micro mode (<30 min/wk) expects 1 focus and <=30 min experiment")
    if len(p["uncertainty_ledger"]) > 10:
        rep.warn(where, "MPR-11 ledger has more than 10 items")
    if (p.get("delivery") or {}).get("estimated_user_minutes", 0) > 10:
        rep.err(where, "AT-4 delivered reading time > 10 minutes")
    lint_targets = [("focus " + f["id"], f["title"]) for f in m["focus_areas"]]
    lint_targets += [("step " + s["id"], s["description"]) for s in m["sequence"]]
    lint_targets += [("experiment title", ax["title"]), ("experiment hypothesis", ax["hypothesis"]["statement"])]
    for label, text in lint_targets:
        hits = generic_hits(text)
        if hits:
            rep.warn(where, f"AT-2 generic pattern in {label}: {text[:90]!r}")
    for t in tasks.values():
        infl = [k for k, v in t["traits"].items() if v["source"] in {"operator_inferred", "engine_inferred"} and v["confidence"] == "high"]
        if infl:
            rep.err(where, f"Task Map §5: task {t['id']} inferred traits cannot have confidence=high: {infl}")


# ---------------------------------------------------------------- feedback / decision
def check_feedback(fb, packet, rep, where):
    ax = packet.get("first_experiment") or {}
    if fb["packet_id"] != packet["meta"]["packet_id"]:
        rep.err(where, f"feedback packet_id {fb['packet_id']} != {packet['meta']['packet_id']}")
    if fb["experiment_id"] != ax.get("id"):
        rep.err(where, f"feedback experiment_id {fb['experiment_id']} not in packet")
    mids = {mm["id"] for mm in ax.get("measures", [])}
    for o in fb["observations"]:
        if o["measure_id"] not in mids:
            rep.err(where, f"observation for unknown measure {o['measure_id']}")
    grades = [o["grade"] for o in fb["observations"]] or ["E0"]
    if fb["evidence_grade"] != max(grades):
        rep.warn(where, f"record evidence_grade {fb['evidence_grade']} != max observation grade {max(grades)}")
    if fb["attempt_status"] in {"not_attempted", "no_response"}:
        if fb["result_class"] != "not_applicable":
            rep.err(where, "not attempted -> result_class must be not_applicable")
        if fb["attempt_status"] == "not_attempted" and not fb.get("blockers"):
            rep.err(where, "not_attempted requires blockers (CQ-7)")
    if fb["harm_report"]["occurred"] != (fb["harm_report"]["severity"] != "none"):
        rep.err(where, "harm_report.occurred inconsistent with severity")


def expected_rules(fb, prior_non_attempt):
    """Return the decision-table rule that should fire first (FEEDBACK_ADAPTATION_LOGIC §6)."""
    if fb["harm_report"]["occurred"]:
        return "A1", "escalate"
    status, blockers = fb["attempt_status"], set(fb.get("blockers", []))
    if status in {"not_attempted", "no_response"} and prior_non_attempt:
        return "A5", "rediagnose"
    if status == "no_response":
        return "A7", "simplify"
    if status == "not_attempted":
        if blockers & {"access_or_tool", "policy"}:
            return "A8", "change_intervention"
        if "unclear_instructions" in blockers:
            return "A9", "modify"
        if "motivation_or_relevance" in blockers:
            return "A10", "rediagnose"
        if blockers & {"time", "forgot"}:
            return "A6", "simplify"
        return None, None
    strong = fb["evidence_grade"] in {"E2", "E3"}
    if status == "partly" and not strong:
        return "A12", "simplify"
    rc = fb["result_class"]
    if not strong or rc == "null_result":
        return "A16", "modify"
    return {"confirms": ("A13", "continue"), "disconfirms": ("A14", "modify"), "mixed": ("A15", "investigate_further")}.get(rc, (None, None))


def check_decision(ad, fb, packet, rep, where, prior_non_attempt=False):
    ax = packet.get("first_experiment") or {}
    if ad["feedback_id"] != fb["id"]:
        rep.err(where, f"decision feedback_id {ad['feedback_id']} != {fb['id']}")
    rule, move = expected_rules(fb, prior_non_attempt)
    if rule and rule not in ad["table_rules"]:
        rep.err(where, f"decision table expects {rule} ({move}); decision lists {ad['table_rules']}")
    if move and ad["decision"] != move and not (fb["attempt_status"] == "partly" and rule not in {"A12"}):
        rep.err(where, f"decision table expects '{move}', decision is '{ad['decision']}'")
    branches = {b["id"]: b for b in ax.get("branches", [])}
    bid = ad.get("branch_id")
    if bid:
        if bid not in branches:
            rep.err(where, f"branch {bid} not in experiment")
        elif branches[bid]["next_move"] != ad["decision"] and not (set(ad["table_rules"]) & OVERRIDE_RULES) and not ad.get("deviation_reason"):
            rep.err(where, f"decision deviates from branch {bid} ({branches[bid]['next_move']}) without deviation_reason")
    ledger = {u["id"] for u in packet.get("uncertainty_ledger", [])}
    for lu in ad["ledger_updates"]:
        if lu["new_status"] != "added" and lu["uncertainty_id"] not in ledger:
            rep.err(where, f"ledger update for unknown {lu['uncertainty_id']}")
        if lu["new_status"] == "resolved" and fb["evidence_grade"] not in {"E2", "E3"}:
            rep.err(where, f"{lu['uncertainty_id']} resolved on {fb['evidence_grade']} evidence (needs E2+)")


def check_revision(r2, r1, ad, rep, where):
    if r2["meta"].get("parent_packet_id") != r1["meta"]["packet_id"]:
        rep.err(where, "revision parent_packet_id does not match previous packet")
    if r2["meta"].get("decision_ref") != ad["id"]:
        rep.err(where, "revision decision_ref does not match decision id")
    if r2["meta"]["revision"] != r1["meta"]["revision"] + 1:
        rep.err(where, "revision number must increment by 1")
    old = {u["id"]: u for u in r1.get("uncertainty_ledger", [])}
    new = {u["id"]: u for u in r2.get("uncertainty_ledger", [])}
    for lu in ad["ledger_updates"]:
        u = new.get(lu["uncertainty_id"])
        if u is None:
            rep.err(where, f"decision updates {lu['uncertainty_id']} but revision lacks it")
        elif lu["new_status"] != "added" and u["status"] != lu["new_status"]:
            rep.err(where, f"{u['id']} status in revision is {u['status']}, decision says {lu['new_status']}")
    for uid in old:
        if uid not in new:
            rep.err(where, f"revision dropped ledger item {uid} (use status=dropped instead)")


# ---------------------------------------------------------------- folders
def check_folder(folder, schemas, registry, rep):
    print(f"\n== {folder.relative_to(KTA.parent) if folder.is_relative_to(KTA.parent) else folder}")
    docs = {}
    for f in sorted(folder.glob("*.json")):
        prefix = f.name.split("_")[0]
        if prefix not in SCHEMA_BY_PREFIX:
            continue
        doc = json.loads(f.read_text())
        docs[f.name] = doc
        schema_validate(doc, SCHEMA_BY_PREFIX[prefix], schemas, registry, rep, f.name)
    packets = sorted((n for n in docs if n.startswith("packet_")), key=lambda n: docs[n]["meta"]["revision"])
    for n in packets:
        try:
            check_packet(docs[n], rep, n)
        except (KeyError, TypeError) as e:
            rep.err(n, f"invariant check aborted (structure): {e!r}")
    by_id = {docs[n]["meta"]["packet_id"]: docs[n] for n in packets}
    non_attempts = 0
    for n in sorted(x for x in docs if x.startswith("feedback_")):
        fb = docs[n]
        pk = by_id.get(fb["packet_id"])
        if not pk:
            rep.err(n, f"no packet {fb['packet_id']} in folder")
            continue
        check_feedback(fb, pk, rep, n)
        dn = [x for x in docs if x.startswith("decision_") and docs[x]["feedback_id"] == fb["id"]]
        if not dn:
            rep.err(n, "feedback has no decision record")
            continue
        ad = docs[dn[0]]
        check_decision(ad, fb, pk, rep, dn[0], prior_non_attempt=non_attempts > 0)
        non_attempts = non_attempts + 1 if fb["attempt_status"] in {"not_attempted", "no_response"} else 0
        nxt = [by_id[k] for k in by_id if by_id[k]["meta"].get("decision_ref") == ad["id"]]
        if nxt:
            check_revision(nxt[0], pk, ad, rep, f"{dn[0]} -> {nxt[0]['meta']['packet_id']}")
    return docs


# ---------------------------------------------------------------- registry
def schema_path_exists(path, schemas):
    node = schemas["mission_packet.schema.json"]
    base = "mission_packet.schema.json"
    for part in path.split("."):
        is_list = part.endswith("[]")
        key = part[:-2] if is_list else part
        node, base = deref(node, base, schemas)
        props = node.get("properties", {})
        if key not in props:
            return False
        node = props[key]
        node, base = deref(node, base, schemas)
        if is_list:
            node = node.get("items", {})
    return True


def deref(node, base, schemas):
    while "$ref" in node:
        ref = node["$ref"]
        file, _, frag = ref.partition("#")
        if file:
            base = file
        target = schemas[base]
        if frag:
            for seg in frag.strip("/").split("/"):
                target = target[seg]
        node = target
    return node, base


def check_registry(schemas, rep):
    print("\n== diagnostic question registry")
    reg = json.loads(REGISTRY_FILE.read_text())
    fed = set()
    always = [q for q in reg["questions"] if q["ask"].startswith("always")]
    for q in reg["questions"]:
        if not q["feeds"]:
            rep.err(q["id"], "question feeds no packet field (remove it)")
        if not q.get("change_test"):
            rep.err(q["id"], "question has no change test")
        for f in q["feeds"]:
            if not schema_path_exists(f, schemas):
                rep.err(q["id"], f"feeds unknown packet path '{f}'")
            fed.add(f)
    for f in reg["required_intake_fields"]:
        if f not in fed:
            rep.err("registry", f"required intake field '{f}' has no question")
        if not schema_path_exists(f, schemas):
            rep.err("registry", f"required intake field '{f}' not in packet schema")
    if len(always) > reg["budget"]["core_max_cards"]:
        rep.err("registry", f"{len(always)} always-asked cards > budget {reg['budget']['core_max_cards']}")
    secs = sum(q["est_seconds"] for q in always)
    if secs > reg["budget"]["core_target_seconds"] * 1.1:
        rep.warn("registry", f"core intake est {secs}s > target {reg['budget']['core_target_seconds']}s")
    print(f"  {len(reg['questions'])} cards ({len(always)} always-asked, est {secs // 60} min {secs % 60} s core)")


# ---------------------------------------------------------------- swap-test aid
def words(text):
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOPWORDS}


def swap_aid(folders, rep):
    print("\n== AT-1 swap-test aid (textual overlap of priority-1 focus + experiment; judgment still required)")
    firsts = {}
    for folder in folders:
        pk = [json.loads(f.read_text()) for f in folder.glob("packet_*.json")]
        pk = [p for p in pk if p["meta"]["revision"] == 1 and p["scope_check"]["result"] != "out_of_scope"]
        if pk:
            firsts[folder.name] = pk[0]
    for (a, pa), (b, pb) in itertools.combinations(sorted(firsts.items()), 2):
        fa = next(f for f in pa["mission"]["focus_areas"] if f["priority"] == 1)
        fb = next(f for f in pb["mission"]["focus_areas"] if f["priority"] == 1)
        ta = words(fa["title"] + " " + pa["first_experiment"]["title"] + " " + pa["first_experiment"]["hypothesis"]["statement"])
        tb = words(fb["title"] + " " + pb["first_experiment"]["title"] + " " + pb["first_experiment"]["hypothesis"]["statement"])
        jac = len(ta & tb) / max(1, len(ta | tb))
        same_arch = pa["first_experiment"]["archetype"] == pb["first_experiment"]["archetype"]
        flag = "  <-- review" if jac >= 0.35 or (same_arch and jac >= 0.2) else ""
        print(f"  {a:>18} vs {b:<18} overlap={jac:.2f} archetypes={pa['first_experiment']['archetype']}/{pb['first_experiment']['archetype']}{flag}")
        if flag:
            rep.warn("AT-1", f"{a} vs {b} may converge")
    archs = [p["first_experiment"]["archetype"] for p in firsts.values()]
    print(f"  distinct first-experiment archetypes: {len(set(archs))}/{len(archs)}")


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--registry", action="store_true", help="check the diagnostic question registry only")
    ap.add_argument("--swap", type=Path, help="run swap-test aid over a folder of user folders")
    a = ap.parse_args(argv)
    schemas, registry = load_schemas()
    rep = Report()
    if a.registry:
        check_registry(schemas, rep)
    elif a.swap:
        swap_aid(sorted(d for d in a.swap.iterdir() if d.is_dir()), rep)
    elif a.paths:
        for p in a.paths:
            if p.is_dir():
                check_folder(p, schemas, registry, rep)
            else:
                prefix = p.name.split("_")[0]
                doc = json.loads(p.read_text())
                print(f"\n== {p}")
                schema_validate(doc, SCHEMA_BY_PREFIX.get(prefix, "mission_packet.schema.json"), schemas, registry, rep, p.name)
                if prefix == "packet":
                    check_packet(doc, rep, p.name)
    else:
        check_registry(schemas, rep)
        folders = sorted(d for d in SIMULATION.iterdir() if d.is_dir()) if SIMULATION.exists() else []
        for d in folders:
            check_folder(d, schemas, registry, rep)
        if folders:
            swap_aid(folders, rep)
    print(f"\nRESULT: {rep.errors} error(s), {rep.warnings} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
