# NEXT ACTION

**Lane 02 v0.1 is waiting for owner acceptance.** Do not start the drafting prompt, and do not apply any authoritative change, until the owner replies to D1–D6 (`02_STATE/OWNER_DECISIONS_PENDING.md`; detail in `03_CURRENT_WORK/KTA_LANE_02_ACCEPTANCE_PACKET_v0.1.md` §8).

When the reply arrives:
1. Record the answers in `OWNER_DECISIONS_PENDING.md`.
2. Apply the approved diffs from packet §7: Blueprint, Current State, Constitution and governance files, registry XLSX (then run `tools/render_registries.py`), Source Manifest, `KTA/CLAUDE.md`, Lane Map. Propagate every change.
3. Build release KTA-REL-0.1: a Git tag, a bundle with SHA-256 manifest, and Drive sync per D1.
4. Carry out repairs R1–R5. `kta_check.py` must report 0 errors and all tests must pass.
5. Follow packet §10 from step 3 onward.

Verify with: `pip install jsonschema && python KTA/tools/kta_check.py && python -m unittest KTA/tools/test_kta_check.py`
