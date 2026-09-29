"""Regression tests for the stress traces (repair R5) and the metrics tool (repair R4).

Each ST folder encodes the correct handling of a stress trace and must check clean. Each
test then applies the *wrong* handling and asserts the checker rejects it.
    python -m unittest KTA/tools/test_regression.py
"""
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kta_check as kc  # noqa: E402
import kta_metrics as km  # noqa: E402

REG = kc.REGRESSION
SCHEMAS, REGISTRY = kc.load_schemas()


def check_dir(folder):
    rep = kc.Report()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kc.check_folder(folder, SCHEMAS, REGISTRY, rep)
    return rep, buf.getvalue()


@contextlib.contextmanager
def mutated(folder_name, name, fn):
    """Copy a regression folder to a temp dir, mutate one JSON file, yield the temp folder."""
    tmp = Path(tempfile.mkdtemp())
    dst = tmp / folder_name
    shutil.copytree(REG / folder_name, dst)
    doc = json.loads((dst / name).read_text())
    fn(doc)
    (dst / name).write_text(json.dumps(doc))
    try:
        yield dst
    finally:
        shutil.rmtree(tmp)


class RegressionFoldersClean(unittest.TestCase):
    def test_all_regression_folders_pass(self):
        folders = sorted(d for d in REG.iterdir() if d.is_dir())
        self.assertEqual(len(folders), 5)
        for d in folders:
            rep, out = check_dir(d)
            self.assertEqual(rep.errors, 0, f"{d.name}:\n{out}")


class StressTraceMutations(unittest.TestCase):
    def test_st1_thin_map_rejects_non_audit_experiment(self):
        def fn(p):
            p["first_experiment"]["archetype"] = "shadow_test"
        with mutated("ST-1-thin-map", "packet_r1.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("INV-15", out)

    def test_st2_prohibits_rejects_redacted_work_material(self):
        def fn(p):
            p["first_experiment"]["materials"]["data_class"] = "redacted_nonconfidential"
        with mutated("ST-2-prohibits-policy", "packet_r1.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("prohibitive policy", out)

    def test_st2_prohibits_rejects_confidential_material(self):
        def fn(p):
            p["first_experiment"]["materials"]["data_class"] = "confidential"
        with mutated("ST-2-prohibits-policy", "packet_r1.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("INV-08", out)

    def test_st3_second_non_attempt_must_rediagnose(self):
        def fn(ad):
            ad.update({"decision": "simplify", "table_rules": ["A6"]})
        with mutated("ST-3-repeat-non-attempt", "decision_AD02.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("A5", out)

    def test_st4_harm_must_escalate(self):
        def fn(ad):
            ad.update({"decision": "continue", "table_rules": ["A13"], "branch_id": "B1"})
        with mutated("ST-4-harm", "decision_AD01.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("A1", out)

    def test_st5_decline_is_not_a_non_attempt(self):
        fb = json.loads((REG / "ST-5-declined" / "feedback_FB01.json").read_text())
        self.assertEqual(kc.expected_rules(fb, prior_non_attempt=True), ("A18", "continue"))

    def test_st5_declined_needs_no_prediction_but_proposed_active_does(self):
        def fn(p):
            p["first_experiment"]["status"] = "accepted"
        with mutated("ST-5-declined", "packet_r1.json", fn) as d:
            rep, out = check_dir(d)
        self.assertIn("INV-14", out)


class MetricsTest(unittest.TestCase):
    def test_simulation_values(self):
        m = km.compute(sorted(d for d in kc.SIMULATION.iterdir() if d.is_dir()))
        self.assertEqual((m["DUAR"]["n"], m["DUAR"]["d"]), (2, 3))
        self.assertEqual((m["MAR_comparison"]["n"], m["MAR_comparison"]["d"]), (2, 3))
        self.assertEqual(m["pending_checkin"], 3)
        self.assertEqual(m["safety_gate"]["status"], "clear")

    def test_decline_counts_in_denominator(self):
        m = km.compute([REG / "ST-5-declined"])
        self.assertEqual((m["DUAR"]["n"], m["DUAR"]["d"]), (0, 1))
        self.assertEqual(m["supporting"]["decline_rate"]["n"], 1)

    def test_null_result_is_decision_useful_but_inconclusive_is_not(self):
        base = copy.deepcopy(next(km.cycles(kc.SIMULATION / "SIM-ACC")))
        base["feedback"] = copy.deepcopy(base["feedback"])
        base["decision"] = copy.deepcopy(base["decision"])
        base["feedback"]["result_class"] = "null_result"
        base["decision"]["table_rules"] = ["A16a"]
        self.assertTrue(km.classify(base)["decision_useful"])
        base["feedback"]["result_class"] = "inconclusive"
        base["decision"]["table_rules"] = ["A16b"]
        self.assertFalse(km.classify(base)["decision_useful"])

    def test_safety_gate_is_separate_from_duar(self):
        """Owner decision D4: serious harm triggers the gate but does not change DUAR."""
        folder = kc.SIMULATION / "SIM-ACC"
        before = km.compute([folder])
        tmp = Path(tempfile.mkdtemp())
        try:
            dst = tmp / "SIM-ACC"
            shutil.copytree(folder, dst)
            fb = json.loads((dst / "feedback_FB01.json").read_text())
            fb["harm_report"] = {"occurred": True, "severity": "serious"}
            (dst / "feedback_FB01.json").write_text(json.dumps(fb))
            after = km.compute([dst])
        finally:
            shutil.rmtree(tmp)
        self.assertEqual(after["DUAR"], before["DUAR"])
        self.assertEqual(before["safety_gate"]["status"], "clear")
        self.assertEqual(after["safety_gate"]["status"], "TRIGGERED")

    def test_st4_minor_harm_does_not_trigger_gate(self):
        m = km.compute([REG / "ST-4-harm"])
        self.assertEqual(m["safety_gate"]["status"], "clear")
        self.assertEqual(m["safety_gate"]["minor_harm_events"], 1)


if __name__ == "__main__":
    unittest.main()
