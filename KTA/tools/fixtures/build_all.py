"""Rebuild every KTA fixture: the simulation folders, then the regression folders derived from them.

    python KTA/tools/fixtures/build_all.py
    python KTA/tools/kta_check.py        # must report 0 errors
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for script in ("sim_acc.py", "sim_des.py", "sim_sal.py", "sim_edge.py", "build_regression.py"):
    runpy.run_path(str(HERE / script), run_name="__main__")
