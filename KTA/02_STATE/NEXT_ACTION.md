# NEXT ACTION

1. **If the owner has answered batch 1** (`02_STATE/OWNER_DECISIONS_PENDING.md`): record the answers there. Apply each approved change to the authority docs and the registry XLSX, and regenerate the mirror (`python KTA/tools/render_registries.py`). Reconcile every affected artifact (Propagation Rule). Then ask pilot batch 2 (`03_CURRENT_WORK/V0_PILOT_PREPARATION_v0.1.md` §10).
2. **Otherwise** (non-material, allowed now): build `03_CURRENT_WORK/ENGINE_DRAFTING_TEMPLATE_v0.1.md`. It is the LLM drafting prompt and packet skeleton that turns intake notes into `packet_r1.engine.json` following MPR-01..20. Include one worked example, from a new simulated intake, that passes `python KTA/tools/kta_check.py`.

Verification commands (repo root): `pip install jsonschema && python KTA/tools/kta_check.py && python -m unittest KTA/tools/test_kta_check.py`
