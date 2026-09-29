# Stress-trace regression fixtures (repair R5)

Each folder encodes the **correct** handling of one stress trace from `FAILURE_MODE_REVIEW_v0.1.md` §2. Every folder must pass `kta_check.py`. `tools/test_regression.py` then applies the **wrong** handling to each one and asserts that the checker rejects it.

| Folder | Trace | Correct handling | Test for the wrong handling |
|---|---|---|---|
| `ST-1-thin-map` | Messy intake: 2 tasks, low coverage, 15 min/week | Map-building `time_audit` first, `map_confidence: low`, micro mode (INV-15) | A shadow test instead → INV-15 |
| `ST-2-prohibits-policy` | Employer prohibits AI | Off-work practice on synthetic material only (MPR-14, FM-19) | Redacted or confidential work material → INV-08 |
| `ST-3-repeat-non-attempt` | Two non-attempts in a row | `rediagnose` (A5, overrides branch B5) | `simplify` again → A5 expected |
| `ST-4-harm` | Real figures pasted before scope confirmed | `escalate` (A1). Minor harm, so the safety gate stays clear. | `continue` → A1 expected |
| `ST-5-declined` | The user declines the experiment | `continue` with explain and research (A18); not a non-attempt; no prediction needed | Status `accepted` without a prediction → INV-14 |

ST-2 to ST-5 are derived from the simulation fixtures. Regenerate everything with `python KTA/tools/fixtures/build_all.py`, and **never edit these JSON files by hand**.
