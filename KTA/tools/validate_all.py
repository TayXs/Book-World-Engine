"""Run the complete KTA validation suite. It must be green before any release.

    pip install jsonschema openpyxl
    python KTA/tools/validate_all.py

Steps:
  1. Fixtures are reproducible: rebuilding them from tools/fixtures/ changes nothing.
  2. The registry Markdown mirror matches the XLSX.
  3. kta_check.py: schemas, invariants INV-01..16, decision table, lint, registry traceability.
  4. Unit, mutation, regression and metrics tests (tools/test_*.py).
  5. State files: PROJECT_STATE.json is valid and has the keys CLAUDE.md requires.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import runpy
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
KTA = TOOLS.parent
sys.path.insert(0, str(TOOLS))

REQUIRED_STATE_KEYS = ["project_version", "current_stage", "current_lane", "current_objective", "current_artifact",
                       "last_completed", "active_questions", "proposed_material_changes", "blockers", "next_action",
                       "last_updated"]


def digest(paths):
    return {str(p.relative_to(KTA)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def fixture_files():
    return [p for d in ("simulation", "regression") for p in (KTA / "03_CURRENT_WORK" / d).rglob("*.json")]


def step(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    return ok


def main():
    results = []

    before = digest(fixture_files())
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(TOOLS / "fixtures" / "build_all.py"), run_name="__main__")
    after = digest(fixture_files())
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    results.append(step("1 fixtures reproducible from tools/fixtures", not changed,
                        f"{len(after)} files" if not changed else f"changed on rebuild: {changed[:5]}"))

    mirror = KTA / "04_REGISTRIES" / "KTA_REGISTRIES_v0.1_RENDERED.md"
    old = mirror.read_bytes()
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(TOOLS / "render_registries.py"), run_name="__main__")
    results.append(step("2 registry mirror matches XLSX", mirror.read_bytes() == old))

    import kta_check
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = kta_check.main([])
    last = [line for line in buf.getvalue().splitlines() if line.startswith("RESULT")]
    results.append(step("3 kta_check (registry + simulation + regression)", rc == 0, last[0] if last else ""))

    suite = unittest.defaultTestLoader.discover(str(TOOLS), pattern="test_*.py", top_level_dir=str(TOOLS))
    stream = io.StringIO()
    res = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    detail = f"{res.testsRun} tests, {len(res.failures)} failures, {len(res.errors)} errors"
    results.append(step("4 unit/mutation/regression/metrics tests", res.wasSuccessful(), detail))
    if not res.wasSuccessful():
        print(stream.getvalue())

    try:
        st = json.loads((KTA / "02_STATE" / "PROJECT_STATE.json").read_text())
        missing = [k for k in REQUIRED_STATE_KEYS if k not in st]
        results.append(step("5 PROJECT_STATE.json valid with required keys", not missing, f"missing {missing}" if missing else ""))
    except json.JSONDecodeError as e:
        results.append(step("5 PROJECT_STATE.json valid with required keys", False, str(e)))

    ok = all(results)
    print(f"\nVALIDATION: {'GREEN' if ok else 'RED'} ({sum(results)}/{len(results)} steps passed)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
