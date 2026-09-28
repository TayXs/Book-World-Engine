# Research findings behind this skill (tennis edge research, DEV period, run 2026-09-24)

Data: Jeff Sackmann ATP/WTA results 2020–2026 and Valuebetennis Pinnacle opening and last-pre-match (closing) odds 2021–2026. Walk-forward testing 2021–2024. The 2025–26 holdout was never opened.

## Numbers the brief may quote (2022–24, matches with both prices)
- **Who wins.** The betting favourite won **~68%** of matches (ATP 67.8–68.2%, WTA 67.7%). Our best fundamentals model was right 65.5%; ranking alone 63–64%. Favourites priced above 75% won **84–86%**.
- **Money.** Backing every favourite at opening odds returned **−3.3% per bet** (95% range −4.9% to −1.4%). Heavy favourites above 75%: ATP +0.4% (−1.6% to +2.1%), WTA −1.7%. That is break-even at best. Longshots below 25% lost **17–21%**.
- **Forecast quality.** Pinnacle's price, with its cut removed, beat every model we built (log loss about 0.58 vs 0.61). Closing prices beat opening prices. Adding public fundamentals to the price made forecasts worse.
- **Margin allocation.** Bookmakers load more of their cut onto longshots. The proportional de-vig therefore understates favourites slightly; the power de-vig was closest to calibrated (calibration slope ~1.00).
- **Margins.** Pinnacle's median cut is ~3% at opening. The odds found on preview sites carry more: about 5–6% on tour matches and 8–9% on Challengers (observed 2026-09-24). Expected returns are worse accordingly.
- **Line movement (exploratory, not confirmed).** Fundamentals slightly anticipate which way odds move before a match (+0.5–0.9% relative), far too little to overcome the cut.

## Conclusion
No robust exploitable edge was found. The market's fair probabilities are the best available forecast of who wins, and backing them loses roughly the size of the cut over time.

## Derived notes used by the brief (arithmetic, not new research)
- **Accumulators.** The chance that all picks win is the product of their fair chances, and the cut compounds too. Four picks at 85% all win about 52% of the time; at a 5% cut on each, the accumulator's expected return is about −18% versus about −5% for a single.
- **Freshness.** Closing prices beat opening prices in the research, so later and sharper odds give more accurate chances. Preview-site "initial odds" can be 12–24 h old.
