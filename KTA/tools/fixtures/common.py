"""Shared helpers for the KTA simulation and regression fixture builders.

The fixtures under 03_CURRENT_WORK/simulation and 03_CURRENT_WORK/regression are generated
by these scripts. Edit the scripts, then run `python KTA/tools/fixtures/build_all.py`.
"""
import json, copy
from pathlib import Path
KTA = Path(__file__).resolve().parents[2]
OUT = KTA / "03_CURRENT_WORK" / "simulation"
REG = KTA / "03_CURRENT_WORK" / "regression"

def rel(why, *grounded):
    return {"why_for_this_user": why, "grounded_in": list(grounded)}

def tr(v, src="user_stated", conf="medium", note=None):
    d = {"value": v, "source": src, "confidence": conf}
    if note: d["note"] = note
    return d

def inf(v, conf="medium", note=None):
    return tr(v, "operator_inferred", conf, note)

def ts(band, pct=None, src="user_stated", conf="medium"):
    d = {"band": band, "source": src, "confidence": conf}
    if pct is not None: d["pct_estimate"] = pct
    return d

def meta(user, rev, status, created, parent=None, decision=None):
    m = {"contract_version": "0.1", "packet_id": f"MP-{user}-r{rev}", "user_ref": user,
         "mission_type": "stay_valuable_ai_work", "revision": rev, "status": status,
         "created_at": created, "generated_by": {"method": "llm", "engine_version": "lane02-spec-v0.1-sim"},
         "simulated": True,
         "privacy_check": {"performed": True, "stage": "before_llm_drafting", "items_redacted": 0, "method": "operator_and_lint"}}
    if parent: m["parent_packet_id"] = parent
    if decision: m["decision_ref"] = decision
    return m

STD_TRIGGERS = [
    {"condition": "Any harm or discomfort reported (CQ-8)", "decision": "escalate"},
    {"condition": "Experiment not attempted or no response at two consecutive check-ins", "decision": "rediagnose"},
    {"condition": "User asks to stop", "decision": "stop"},
]

def trust(rating=None, error=False, note=None):
    t = {"rating_0_10": rating, "fact_error_reported": error}
    if note: t["note"] = note
    return t

def progress(signals=(), grade="E0", note=None):
    p = {"success_signals_observed": list(signals), "evidence_grade": grade}
    if note: p["note"] = note
    return p

def load(folder, name, root=None):
    return json.loads(((root or OUT) / folder / name).read_text())

def write(folder, name, doc, root=None):
    d = (root or OUT) / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
