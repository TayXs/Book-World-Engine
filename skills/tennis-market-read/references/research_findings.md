# Research findings behind this skill (tennis edge research, DEV period; re-run and extended 2026-09-28)

Data: Jeff Sackmann ATP/WTA results 2020–2026 and Valuebetennis Pinnacle opening and last-pre-match (closing) odds 2021–2026. Walk-forward testing 2021–2024. The 2025–26 holdout was never opened.

Re-run 2026-09-28 on the same real data: the pipeline reproduces every number below. (The shipped pipeline stops on its duplicate-key gate because the Sackmann core lists two Davis Cup singles pairings twice, in 2024 and 2025; those 4 rows were dropped for the re-run. All leakage tests pass.)

## Numbers the brief may quote (2022–24, matches with both prices)
- **Who wins.** The betting favourite won **~68%** of matches (ATP 67.8–68.2%, WTA 67.7%). Our best fundamentals model was right 65.5%; ranking alone 63–64%. Favourites priced above 75% won **84–86%**.
- **Money.** Backing every favourite at opening odds returned **−3.3% per bet** (95% range −4.9% to −1.4%). Heavy favourites above 75%: ATP +0.4% (−1.6% to +2.1%), WTA −1.7%. That is break-even at best. Longshots below 25% lost **17–21%**.
- **Forecast quality.** Pinnacle's price, with its cut removed, beat every model we built (log loss about 0.58 vs 0.61). Closing prices beat opening prices. Adding public fundamentals to the price made forecasts worse.
- **Margin allocation.** Bookmakers load more of their cut onto longshots. The proportional de-vig therefore understates favourites slightly; the power de-vig was closest to calibrated (calibration slope ~1.00).
- **Margins.** Pinnacle's median cut at opening is ~3% on tour main draws, ~5% in tour qualifying and ~7% on Challengers and ITFs. The odds found on preview sites carry more: about 5–6% on tour matches and 8–9% on Challengers (observed 2026-09-24). Expected returns are worse accordingly.
- **Line movement (exploratory, not confirmed).** Fundamentals slightly anticipate which way odds move before a match (+0.5–0.9% relative), far too little to overcome the cut.

## Conclusion
No robust exploitable edge was found. The market's fair probabilities are the best available forecast of who wins, and backing them loses roughly the size of the cut over time.

## All-level re-analysis (2026-09-28)
Valuebetennis Pinnacle odds for every level (ITF, Challenger/WTA 125, tour qualifying, tour main draw), 314,245 matches 2021–24, not just the tour matches that join to the results file. Explored on 2021–23, new rules checked on 2024; 2025–26 left sealed. Settlement: Pinnacle's rule (void without a completed set). Scripts: `research/tennis-market-reanalysis/` in the repo.

| Level (opening prices, 2021–24) | Matches | Pinnacle cut | Favourite won | Back all favourites | Above 75%: won / return |
|---|---|---|---|---|---|
| Tour main draw | 18,802 | 3.0% | 68.1% | −2.5% | 84.7% / −0.1% |
| Tour qualifying | 9,821 | 4.8% | 68.7% | −2.0% | 84.6% / −1.2% |
| Challenger / WTA 125 | 54,727 | 7.0% | 66.7% | −4.4% | 82.2% / −3.4% |
| ITF | 54,739 | 7.5% | 70.8% | −4.4% | 84.2% / −3.2% |

- **Power de-vig is right at every level.** It had the best or tied log loss at all five levels, opening and closing; Shin is almost identical and proportional is worst. A level-specific recalibration fitted on 2021–23 did not improve 2024 (tour main draw: −0.0002 log loss, 95% CI −0.0009 to +0.0005).
- **No segment is mispriced in both periods.** Checked by tour, surface, best-of-3 vs best-of-5 and qualifying vs main draw. Two hints, not significant after this many looks: tour main-draw favourites above 90% won ~2 points more than the fair chance (95.8% vs 93.8%, and 96.0% vs 93.9% in 2024; +1.5% return at Pinnacle's opening price, gone at a preview site's cut), and men's best-of-5 Slam favourites above 75% won ~2 points more. Neither is an edge.
- **Qualifying is priced as well as the main draw.**
- **Closing beats opening at every level.** Between opening and close the favourite flips in ~5% of matches and the chance moves ~3 points on average.
- **The accumulator ladder is accurate.** Taking the day's top N favourites (tour + Challenger), the predicted all-win chance matched the actual rate within about a point for N = 1–5 (opening prices: top 4 predicted 62.7%, actual 62.2%). Independence is a fair assumption.
- **The pool matters more than anything else.** Day's top 4 from the whole slate: all won 62–64%. Top 4 from 12 random matches that day: 41%. Return still falls with each pick: at Pinnacle's opening price, about −1% for the single top favourite, −2.7% for two, −5% for three, −7.8% for four.
- **Retirements and walkovers.** About 2.5–3.1% retirements and 0.7–0.9% walkovers on tour (Sackmann 2021–24). Pinnacle voids a bet without a completed set; other bookmakers differ.
- **Data caveat.** Valuebetennis scores are often truncated (about 12% look unfinished), so they can't be used to count retirements; only the winner field and the one-set rule are relied on.

## Derived notes used by the brief (arithmetic, not new research)
- **Accumulators.** The chance that all picks win is the product of their fair chances, and the cut compounds too. Four picks at 85% all win about 52% of the time; at a 5% cut on each, the accumulator's expected return is about −18% versus about −5% for a single.
- **Freshness.** Closing prices beat opening prices in the research, so later and sharper odds give more accurate chances. Preview-site "initial odds" can be 12–24 h old.
