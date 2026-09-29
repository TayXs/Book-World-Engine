"""KTA metrics (repair R4): DUAR, MAR, supporting metrics, and the separate safety gate.

Definitions: FEEDBACK_ADAPTATION_LOGIC_v0.1.md §9 and DEC-005 as amended (owner decision D4).
  * DUAR (PROVISIONAL primary candidate): among recommended experiments that have a check-in
    (including declined and no-response), the share that were attempted, produced interpretable
    evidence (E2+, not inconclusive) or an observed success signal (E2+), and were cited by the
    next AdaptationDecision under a result-driven rule.
  * MAR (comparison): the literal DEC-005 v0.1 reading.
  * Safety gate: a serious harm report triggers the gate. It is reported separately and never
    changes DUAR.

Usage (repo root):
    python KTA/tools/kta_metrics.py                         # simulation folders
    python KTA/tools/kta_metrics.py path/to/user_folder ... [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

KTA = Path(__file__).resolve().parent.parent
SIMULATION = KTA / "03_CURRENT_WORK" / "simulation"

ATTEMPTED = {"fully", "partly"}
INTERPRETABLE = {"confirms", "disconfirms", "mixed", "null_result"}
STRONG = {"E2", "E3"}
RESULT_DRIVEN_RULES = {"A11", "A13", "A14", "A15", "A16a"}
DELIVERED_PACKET = {"delivered", "active", "superseded", "closed"}


def _load(folder: Path, prefix: str):
    return [json.loads(f.read_text()) for f in sorted(folder.glob(f"{prefix}_*.json"))]


def cycles(folder: Path):
    """Yield one record per recommended experiment in a user folder."""
    packets = sorted(_load(folder, "packet"), key=lambda p: p["meta"]["revision"])
    feedback = {f["experiment_id"] + "@" + f["packet_id"]: f for f in _load(folder, "feedback")}
    decisions = {d["feedback_id"]: d for d in _load(folder, "decision")}
    for p in packets:
        ax = p.get("first_experiment")
        if not ax or p["meta"]["status"] not in DELIVERED_PACKET or ax["status"] == "proposed":
            continue
        fb = feedback.get(ax["id"] + "@" + p["meta"]["packet_id"])
        ad = decisions.get(fb["id"]) if fb else None
        ledger = {u["id"]: u for u in p.get("uncertainty_ledger", [])}
        yield {"user": folder.name, "packet": p, "experiment": ax, "feedback": fb, "decision": ad,
               "high_impact": any(ledger.get(u, {}).get("impact") == "high" for u in ax["targets"]["uncertainty_ids"])}


def classify(c):
    fb, ad = c["feedback"], c["decision"]
    if fb is None:
        return {"pending": True}
    attempted = fb["attempt_status"] in ATTEMPTED
    interpretable = fb["evidence_grade"] in STRONG and fb["result_class"] in INTERPRETABLE
    mp = fb.get("mission_progress") or {}
    progress = bool(mp.get("success_signals_observed")) and mp.get("evidence_grade") in STRONG
    used = bool(ad) and bool(set(ad["table_rules"]) & RESULT_DRIVEN_RULES)
    dc = fb.get("decision_change") or {}
    real_world = dc.get("status") in {"changed", "confirmed"} and bool((dc.get("description") or "").strip())
    usefulness = fb.get("usefulness_0_10")
    return {
        "pending": False,
        "attempted": attempted,
        "completed": fb["attempt_status"] == "fully",
        "declined": fb["attempt_status"] == "declined",
        "no_response": fb["attempt_status"] == "no_response",
        "decision_useful": attempted and (interpretable or progress) and used,
        "mar": attempted and ((usefulness is not None and usefulness >= 6) or dc.get("status") in {"changed", "confirmed"}),
        "real_world_decision": real_world,
        "grade": fb["evidence_grade"],
        "usefulness": usefulness,
        "trust": (fb.get("trust") or {}).get("rating_0_10"),
        "fact_error": (fb.get("trust") or {}).get("fact_error_reported", False),
        "signals_observed": len(mp.get("success_signals_observed", [])),
        "confidence_delta": (fb.get("goal_confidence_0_10") - c["packet"]["goal"]["baseline"]["goal_confidence_0_10"])
        if fb.get("goal_confidence_0_10") is not None and c["packet"].get("goal") else None,
        "attention_minutes": (c["packet"].get("delivery") or {}).get("estimated_user_minutes", 0)
        + (fb.get("effort_minutes_actual") or 0) + (fb.get("checkin_minutes") or 0),
        "harm": fb["harm_report"]["severity"],
    }


def _rate(n, d):
    return {"n": n, "d": d, "rate": round(n / d, 3) if d else None}


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def compute(folders):
    cs = [c for f in folders for c in cycles(f)]
    rows = [(c, classify(c)) for c in cs]
    done = [(c, r) for c, r in rows if not r["pending"]]
    d = len(done)
    users_with_checkin = {c["user"] for c, _ in done}
    users_useful = {c["user"] for c, r in done if r["decision_useful"]}
    harm = Counter(r["harm"] for _, r in done)
    return {
        "recommended_experiments": len(rows),
        "pending_checkin": len(rows) - d,
        "DUAR": _rate(sum(r["decision_useful"] for _, r in done), d),
        "DUAR_per_user": _rate(len(users_useful), len(users_with_checkin)),
        "MAR_comparison": _rate(sum(r["mar"] for _, r in done), d),
        "real_world_decision_rate": _rate(sum(r["real_world_decision"] for _, r in done), d),
        "supporting": {
            "attempt_rate": _rate(sum(r["attempted"] for _, r in done), d),
            "completion_rate": _rate(sum(r["completed"] for _, r in done), d),
            "decline_rate": _rate(sum(r["declined"] for _, r in done), d),
            "no_response_rate": _rate(sum(r["no_response"] for _, r in done), d),
            "evidence_grade_mix": dict(Counter(r["grade"] for _, r in done)),
            "usefulness_mean": _mean(r["usefulness"] for _, r in done),
            "trust_mean": _mean(r["trust"] for _, r in done),
            "fact_error_reports": sum(bool(r["fact_error"]) for _, r in done),
            "success_signals_observed": sum(r["signals_observed"] for _, r in done),
            "goal_confidence_delta_mean": _mean(r["confidence_delta"] for _, r in done),
            "attention_minutes_mean": _mean(r["attention_minutes"] for _, r in done),
            "high_impact_targeting": _rate(sum(c["high_impact"] for c, _ in rows), len(rows)),
        },
        "safety_gate": {
            "serious_harm_events": harm.get("serious", 0),
            "minor_harm_events": harm.get("minor", 0),
            "status": "TRIGGERED" if harm.get("serious", 0) else "clear",
            "note": "Independent of DUAR (owner decision D4): a trigger may fail, pause or end the cohort; DUAR is still reported.",
        },
    }


def fmt_rate(r):
    return f"{r['n']}/{r['d']} = {r['rate']:.0%}" if r["d"] else "n/a (no check-ins)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="*", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    folders = a.folders or sorted(d for d in SIMULATION.iterdir() if d.is_dir())
    m = compute(folders)
    if a.json:
        print(json.dumps(m, indent=2))
        return 0
    print(f"Recommended experiments: {m['recommended_experiments']} (pending check-in: {m['pending_checkin']})")
    print(f"DUAR (PROVISIONAL primary candidate): {fmt_rate(m['DUAR'])}")
    print(f"  per-user companion:                 {fmt_rate(m['DUAR_per_user'])}")
    print(f"MAR (comparison, DEC-005 v0.1):       {fmt_rate(m['MAR_comparison'])}")
    print(f"Real-World Decision Rate:             {fmt_rate(m['real_world_decision_rate'])}")
    s = m["supporting"]
    for k in ("attempt_rate", "completion_rate", "decline_rate", "no_response_rate", "high_impact_targeting"):
        print(f"  {k:<22} {fmt_rate(s[k])}")
    for k in ("evidence_grade_mix", "usefulness_mean", "trust_mean", "fact_error_reports",
              "success_signals_observed", "goal_confidence_delta_mean", "attention_minutes_mean"):
        print(f"  {k:<22} {s[k]}")
    g = m["safety_gate"]
    print(f"SAFETY GATE (separate): {g['status']} (serious={g['serious_harm_events']}, minor={g['minor_harm_events']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
