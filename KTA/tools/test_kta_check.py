"""Mutation tests for kta_check.py.

Each test breaks one rule in a valid simulation packet and asserts that the checker reports
exactly that rule. Run with either command:
    python -m unittest KTA/tools/test_kta_check.py
    pytest KTA/tools/test_kta_check.py
"""
import contextlib
import copy
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kta_check as kc  # noqa: E402

SIM = kc.SIMULATION


def load(folder, name):
    return json.loads((SIM / folder / name).read_text())


def run_packet(p):
    rep = kc.Report()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kc.check_packet(p, rep, "test")
    return rep, buf.getvalue()


class BaselineTest(unittest.TestCase):
    def test_all_simulation_folders_pass(self):
        schemas, registry = kc.load_schemas()
        rep = kc.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            kc.check_registry(schemas, rep)
            for d in sorted(x for x in SIM.iterdir() if x.is_dir()):
                kc.check_folder(d, schemas, registry, rep)
        self.assertEqual(rep.errors, 0)


class InvariantMutationTest(unittest.TestCase):
    def setUp(self):
        self.acc = load("SIM-ACC", "packet_r1.json")

    def assertFlags(self, p, code):
        rep, out = run_packet(p)
        self.assertGreater(rep.errors, 0, f"expected {code} error, got none")
        self.assertIn(code, out)

    def test_baseline_packet_clean(self):
        rep, out = run_packet(self.acc)
        self.assertEqual(rep.errors, 0, out)

    def test_inv01_out_of_scope_with_mission(self):
        p = copy.deepcopy(self.acc)
        p["scope_check"]["result"] = "out_of_scope"
        self.assertFlags(p, "INV-01")

    def test_inv02_dangling_reference(self):
        p = copy.deepcopy(self.acc)
        p["mission"]["focus_areas"][0]["task_ids"].append("T99")
        self.assertFlags(p, "INV-02")

    def test_inv05_experiment_targets_research_item(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["targets"]["uncertainty_ids"] = ["UQ03"]
        self.assertFlags(p, "INV-05")

    def test_inv05_rating_only_measures(self):
        p = copy.deepcopy(self.acc)
        for m in p["first_experiment"]["measures"]:
            m["type"] = "rating_0_10"
        self.assertFlags(p, "INV-05")

    def test_inv06_depends_on_open_world_fact(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["depends_on"] = ["UQ03"]
        self.assertFlags(p, "INV-06")

    def test_inv06_unverified_claim_shown_as_fact(self):
        p = copy.deepcopy(self.acc)
        p["claims"][1]["shown_as"] = "fact"
        self.assertFlags(p, "INV-06")

    def test_inv07_over_budget(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["effort"]["minutes_total"] = 500
        self.assertFlags(p, "INV-07")

    def test_inv08_confidential_data_with_unknown_policy(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["materials"]["data_class"] = "confidential"
        self.assertFlags(p, "INV-08")

    def test_inv09_untargeted_high_impact_item(self):
        p = copy.deepcopy(self.acc)
        p["mission"]["sequence"] = [s for s in p["mission"]["sequence"] if s["id"] != "S1"]
        self.assertFlags(p, "INV-09")

    def test_inv09_kind_route_mismatch(self):
        p = copy.deepcopy(self.acc)
        p["uncertainty_ledger"][2]["route"] = "experiment"  # world_fact cannot be an experiment
        self.assertFlags(p, "INV-09")

    def test_inv10_risk_score_field(self):
        p = copy.deepcopy(self.acc)
        p["task_map"]["tasks"][0]["automation_risk"] = 0.7
        self.assertFlags(p, "INV-10")

    def test_inv10_risk_percentage_text(self):
        p = copy.deepcopy(self.acc)
        p["mission"]["focus_areas"][0]["rationale"] = "This task is 70% automatable."
        self.assertFlags(p, "INV-10")

    def test_inv11_revision_without_parent(self):
        p = copy.deepcopy(self.acc)
        p["meta"]["revision"] = 2
        p["meta"]["packet_id"] = "MP-SIM-ACC-r2"
        self.assertFlags(p, "INV-11")

    def test_inv12_missing_null_result_branch(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["branches"] = [b for b in p["first_experiment"]["branches"] if b["condition_type"] != "null_result"]
        self.assertFlags(p, "INV-12")

    def test_inv13_late_checkin(self):
        p = copy.deepcopy(self.acc)
        p["feedback_plan"]["checkin_at_days"] = 30
        self.assertFlags(p, "INV-13")

    def test_inv14_missing_user_prediction(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["prediction"]["user"] = None
        self.assertFlags(p, "INV-14")

    def test_inv14_declined_experiment_exempt(self):
        p = copy.deepcopy(self.acc)
        p["first_experiment"]["status"] = "declined"
        p["first_experiment"]["prediction"]["user"] = None
        rep, out = run_packet(p)
        self.assertNotIn("INV-14", out)

    def test_inv15_thin_map_needs_audit(self):
        p = copy.deepcopy(self.acc)
        p["task_map"]["tasks"] = p["task_map"]["tasks"][:1]
        self.assertFlags(p, "INV-15")

    def test_inferred_trait_high_confidence(self):
        p = copy.deepcopy(self.acc)
        p["task_map"]["tasks"][0]["traits"]["analysis_intensity"]["confidence"] = "high"
        self.assertFlags(p, "Task Map")


class DecisionTableTest(unittest.TestCase):
    def test_wrong_decision_for_not_attempted_time(self):
        pk = load("SIM-DES", "packet_r1.json")
        fb = load("SIM-DES", "feedback_FB01.json")
        ad = load("SIM-DES", "decision_AD01.json")
        ad["decision"], ad["table_rules"] = "continue", ["A13"]
        rep = kc.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            kc.check_decision(ad, fb, pk, rep, "test")
        self.assertGreater(rep.errors, 0)

    def test_second_non_attempt_requires_rediagnose(self):
        fb = load("SIM-DES", "feedback_FB01.json")
        self.assertEqual(kc.expected_rules(fb, prior_non_attempt=True), ("A5", "rediagnose"))

    def test_declined_is_not_a_non_attempt(self):
        fb = load("SIM-DES", "feedback_FB01.json")
        fb["attempt_status"], fb["blockers"] = "declined", []
        self.assertEqual(kc.expected_rules(fb, prior_non_attempt=True), ("A18", "continue"))

    def test_harm_overrides_everything(self):
        fb = load("SIM-ACC", "feedback_FB01.json")
        fb["harm_report"] = {"occurred": True, "severity": "minor"}
        self.assertEqual(kc.expected_rules(fb, prior_non_attempt=False), ("A1", "escalate"))

    def test_resolution_on_weak_evidence_rejected(self):
        pk = load("SIM-ACC", "packet_r1.json")
        fb = load("SIM-ACC", "feedback_FB01.json")
        ad = load("SIM-ACC", "decision_AD01.json")
        fb["evidence_grade"] = "E1"
        rep = kc.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            kc.check_decision(ad, fb, pk, rep, "test")
        self.assertGreater(rep.errors, 0)


class RegistryTest(unittest.TestCase):
    def test_unknown_feed_path_detected(self):
        schemas, _ = kc.load_schemas()
        self.assertTrue(kc.schema_path_exists("task_map.tasks[].traits.predictability", schemas))
        self.assertFalse(kc.schema_path_exists("task_map.tasks[].automation_risk", schemas))



def run_feedback(fb, pk):
    rep = kc.Report()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kc.check_feedback(fb, pk, rep, "test")
    return rep, buf.getvalue()


def run_lint(doc):
    rep = kc.Report()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kc.confidential_lint(doc, rep, "test")
    return rep, buf.getvalue()


class RepairR1NullVsInconclusiveTest(unittest.TestCase):
    """R1 / FM-23: measured no-effect (null_result) is distinct from too-little-data (inconclusive)."""

    def setUp(self):
        self.pk = load("SIM-ACC", "packet_r1.json")
        self.fb = load("SIM-ACC", "feedback_FB01.json")
        self.ad = load("SIM-ACC", "decision_AD01.json")

    def test_inv12_requires_inconclusive_branch(self):
        p = copy.deepcopy(self.pk)
        p["first_experiment"]["branches"] = [b for b in p["first_experiment"]["branches"] if b["condition_type"] != "inconclusive"]
        rep, out = run_packet(p)
        self.assertIn("INV-12", out)

    def test_classified_result_needs_e2(self):
        fb = copy.deepcopy(self.fb)
        fb["evidence_grade"] = "E1"
        for o in fb["observations"]:
            o["grade"] = "E1"
        rep, out = run_feedback(fb, self.pk)
        self.assertIn("R1", out)

    def test_inconclusive_maps_to_a16b(self):
        fb = copy.deepcopy(self.fb)
        fb["result_class"] = "inconclusive"
        self.assertEqual(kc.expected_rules(fb, False), ("A16b", "modify"))

    def test_null_result_follows_branch(self):
        fb = copy.deepcopy(self.fb)
        fb["result_class"] = "null_result"
        ad = copy.deepcopy(self.ad)
        ad.update({"decision": "simplify", "table_rules": ["A16a"], "branch_id": "B4"})
        rep = kc.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            kc.check_decision(ad, fb, self.pk, rep, "test")
        self.assertEqual(rep.errors, 0)
        ad["decision"] = "continue"
        ad["branch_id"] = None
        rep = kc.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            kc.check_decision(ad, fb, self.pk, rep, "test")
        self.assertGreater(rep.errors, 0)


class RepairR2ConfidentialBoundaryTest(unittest.TestCase):
    """R2 / INV-16 / DEC-009 P1."""

    def setUp(self):
        self.pk = load("SIM-ACC", "packet_r1.json")

    def test_email_is_error(self):
        p = copy.deepcopy(self.pk)
        p["task_map"]["tasks"][0]["description"] += " Send to j.doe@example.com."
        rep, out = run_lint(p)
        self.assertIn("INV-16 email", out)
        self.assertGreater(rep.errors, 0)

    def test_phone_is_error_but_dates_are_not(self):
        rep, out = run_lint({"a": "call +44 20 7946 0958", "b": "2026-10-01T22:10Z"})
        self.assertEqual(rep.errors, 1)

    def test_coarse_quantities_allowed(self):
        rep, out = run_lint({"a": "about 30% of time, roughly 6 projects, 22 vs 38 minutes, 4 days instead of 6"})
        self.assertEqual((rep.errors, rep.warnings), (0, 0))

    def test_money_and_org_names_warn(self):
        rep, out = run_lint({"a": "Budget of $250,000 approved by Acme Widgets Ltd"})
        self.assertEqual(rep.errors, 0)
        self.assertGreaterEqual(rep.warnings, 2)

    def test_privacy_check_attestation_required(self):
        p = copy.deepcopy(self.pk)
        p["meta"]["privacy_check"]["performed"] = False
        rep, out = run_packet(p)
        self.assertIn("INV-16", out)

    def test_prohibits_policy_blocks_redacted_work_material(self):
        p = copy.deepcopy(self.pk)
        p["context"]["employer_ai_policy"] = {"status": "prohibits"}
        p["first_experiment"]["materials"]["data_class"] = "redacted_nonconfidential"
        rep, out = run_packet(p)
        self.assertIn("prohibitive policy", out)


class RepairR3TrustProgressTest(unittest.TestCase):
    def setUp(self):
        self.pk = load("SIM-ACC", "packet_r1.json")
        self.fb = load("SIM-ACC", "feedback_FB01.json")

    def test_unknown_success_signal_rejected(self):
        fb = copy.deepcopy(self.fb)
        fb["mission_progress"] = {"success_signals_observed": ["Promoted to CFO"], "evidence_grade": "E2"}
        rep, out = run_feedback(fb, self.pk)
        self.assertIn("R3", out)

    def test_signal_needs_evidence(self):
        fb = copy.deepcopy(self.fb)
        fb["mission_progress"] = {"success_signals_observed": [self.pk["goal"]["success_signals"][0]], "evidence_grade": "E0"}
        rep, out = run_feedback(fb, self.pk)
        self.assertIn("R3", out)

if __name__ == "__main__":
    unittest.main()
