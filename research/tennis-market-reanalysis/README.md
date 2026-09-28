# Tennis market re-analysis (2026-09-28)

Checks behind the `tennis-market-read` skill (`skills/tennis-market-read`). No data is stored here.

## Data
- Valuebetennis Pinnacle odds, `valuebetennis-matchs-2021.csv` … `2024.csv` (CC BY 4.0), all levels.
- `devig.py` from the tennis_edge_research kit.

```sh
export TENNIS_ODDS_DIR=/path/to/valuebetennis-matches.csv   # folder with the yearly CSVs
export RESEARCH_SRC=/path/to/tennis_edge_research/src
python3 analysis1.py   # de-vig method comparison, Pinnacle margins, opening vs closing
python3 analysis2.py   # favourite hit rate and flat-bet return by probability band and level
python3 analysis3.py   # per-level recalibration: fit 2021-23, score 2024 (no reliable gain)
python3 analysis4.py   # accumulator ladder: predicted vs actual all-win rate, whole slate vs 12 matches
python3 analysis5.py   # segments: tour, surface, best-of-5, qualifying
python3 analysis6_level_summary.py   # the LEVEL_HISTORY table used by fair_odds.py
```

Split: explore on 2021–23, check on 2024. 2025–26 is untouched, because the pre-registration reserves it for the one-time holdout run.

## Notes
- Round codes in the Valuebetennis `tour` column: 1–3 qualifying, 4 first main-draw round, 5 R2, 6 R3, 7 R16, 9 QF, 10 SF, 12 F, 8/13–17 round robin.
- Settlement: void without a score or without one completed set (Pinnacle's rule). Scores are often truncated, so "incomplete" is not used as a retirement flag.

## Research pipeline re-run (DEV only)
`tennis_edge_research/run_real.sh` stops on its duplicate-key gate. The Sackmann core lists the same Davis Cup singles pairing twice in two ties: AUT–TUR 2024 (Neumayer–Ilkel, match_num 2 and 3) and ESA–ROU 2025 (Ghetu–Cruz). All 4 rows were dropped from a copy of the processed tables before re-running DEV. **This is a protocol deviation and should be added to PREREGISTRATION.md section 10.** All other leakage tests passed. DEV then reproduced the skill's published numbers: H3 (Rfund beats opening) and H5 (positive CLV) are REJECTED for both tours.
