#!/usr/bin/env python3
"""Turn published tennis odds into fair win chances, margins, a ranked list of the most probable winners,
and honest expected returns. Pure standard library.

Input: a JSON file with a list of rows, one per (match, bookmaker/source):
  {"tour": "ATP", "event": "Chengdu", "round": "R32", "player_a": "Hurkacz", "player_b": "Shevchenko",
   "odds_a": 1.14, "odds_b": 5.6, "odds_format": "decimal" | "american",   # american: e.g. -500 / 333
   "source": "Tennis Tonic", "source_note": "initial odds", "age_hours": 15,  # optional: hours old at run time
   "sharp": false,                                                           # optional: Pinnacle / exchange price
   "start": "optional text"}
Several rows for the same match (any order of players) are merged into one match.

Usage: python fair_odds.py matches.json [--top 5] [--combo 4] [--min-chance 0.5] [--json out.json]

How the fair chance is chosen (research, 2022-24 Pinnacle data):
  * each row is de-vigged with the POWER method (closest to calibrated; does not understate heavy favourites);
  * sharp rows (Pinnacle, Betfair/exchange) are used alone when present, because the sharp price beat every
    other forecast we built;
  * otherwise the freshest rows are averaged (rows more than FRESH_WINDOW hours older than the newest are
    dropped), because later prices beat earlier ones and a consensus of books is steadier than any one book.
Expected return is shown at the first-listed source's price and at the best price found for the favourite."""
import argparse, json, math

SHARP_WORDS = ("pinnacle", "betfair", "exchange", "smarkets", "matchbook")
FRESH_WINDOW = 6          # hours
STALE_HOURS = 12
SPLIT_WARN = 0.05         # sources disagree on the favourite's chance by more than 5 points
HEAVY, FAV = 0.75, 0.60


def to_decimal(x, fmt):
    x = float(x)
    if fmt == "american":
        return 1 + x / 100 if x > 0 else 1 + 100 / abs(x)
    return x


def power_fair(oa, ob):
    qa, qb = 1 / oa, 1 / ob
    lo, hi = 0.5, 3.0                      # find k with qa^k + qb^k = 1 (k > 1 when there is a margin)
    for _ in range(100):
        k = (lo + hi) / 2
        lo, hi = (k, hi) if qa ** k + qb ** k > 1 else (lo, k)
    pa = qa ** ((lo + hi) / 2)
    return pa, 1 - pa


def name(x):
    return str(x).strip().lower()


def is_sharp(m):
    return bool(m.get("sharp")) or any(w in name(m.get("source", "")) for w in SHARP_WORDS)


def check_row(m):
    """Validate and de-vig one source's pair. Returns the row with odds, margin, fair chances or an exclusion."""
    fmt = m.get("odds_format", "decimal")
    oa, ob = to_decimal(m["odds_a"], fmt), to_decimal(m["odds_b"], fmt)
    r = dict(m, odds_a_dec=round(oa, 3), odds_b_dec=round(ob, 3))
    if oa <= 1 or ob <= 1:
        r["status"] = "EXCLUDED: odds must be above 1"; return r
    margin = 1 / oa + 1 / ob - 1
    r["margin"] = margin
    if not (0 <= margin <= 0.15):
        r["status"] = f"EXCLUDED: margin {margin:.1%} outside 0-15% (likely a data error or mismatched odds)"; return r
    pa, pb = power_fair(oa, ob)
    r.update(status="OK", fair_a=pa, fair_b=pb, prop_a=(1 / oa) / (1 + margin), prop_b=(1 / ob) / (1 + margin),
             sharp=is_sharp(m))
    return r


def oriented(r, a):
    """(fair chance, odds) for player a, then for the other player, whichever way round the row lists them."""
    if name(r["player_a"]) == a:
        return r["fair_a"], r["odds_a_dec"], r["fair_b"], r["odds_b_dec"]
    return r["fair_b"], r["odds_b_dec"], r["fair_a"], r["odds_a_dec"]


def age(r):
    return r["age_hours"] if isinstance(r.get("age_hours"), (int, float)) else None


def merge(rows):
    """One match from its valid rows. The lead row (sharp first, then freshest, then first listed) supplies the
    odds shown and the 'quoted' price; the fair chance is the lead row or the average of the fresh pool."""
    a, b = rows[0]["player_a"], rows[0]["player_b"]
    sharp = [r for r in rows if r["sharp"]]
    pool = sharp or rows
    ages = [age(r) for r in pool if age(r) is not None]
    if ages:
        pool = [r for r in pool if age(r) is None or age(r) <= min(ages) + FRESH_WINDOW]
    lead = sorted(pool, key=lambda r: age(r) if age(r) is not None else float("inf"))[0]
    pa = sum(oriented(r, name(a))[0] for r in pool) / len(pool)
    all_pa = [oriented(r, name(a))[0] for r in rows]
    fav, dog = (a, b) if pa >= 0.5 else (b, a)
    fav_prob = max(pa, 1 - pa)
    quoted = oriented(lead, name(fav))[1]
    best_row = max(rows, key=lambda r: oriented(r, name(fav))[1])
    best = oriented(best_row, name(fav))[1]
    m = {k: rows[0].get(k) for k in ("tour", "event", "round", "start")}
    m.update(player_a=a, player_b=b, odds_a_dec=oriented(lead, name(a))[1], odds_b_dec=oriented(lead, name(b))[1],
             margin=lead["margin"], fair_a=pa, fair_b=1 - pa,
             prop_a=lead["prop_a"] if name(lead["player_a"]) == name(a) else lead["prop_b"],
             prop_b=lead["prop_b"] if name(lead["player_a"]) == name(a) else lead["prop_a"],
             favourite=fav, underdog=dog, fav_prob=fav_prob, fav_odds=quoted,
             fav_expected_return=fav_prob * quoted - 1,
             best_odds=best, best_source=best_row.get("source", "?"), best_expected_return=fav_prob * best - 1,
             sources=[r.get("source", "?") for r in rows],
             basis=("sharp price" if sharp else ("consensus of %d" % len(pool) if len(pool) > 1
                                                  else ("freshest of %d" % len(rows) if len(rows) > 1 else "single source"))),
             split=max(all_pa) - min(all_pa), age_hours=age(lead),
             source=lead.get("source", "?"), source_note=lead.get("source_note"))
    m["tier"] = "heavy favourite" if fav_prob > HEAVY else ("favourite" if fav_prob > FAV else "close match")
    flags = []
    if m["split"] > SPLIT_WARN:
        flags.append(f"sources disagree by {m['split']:.0%}")
    if isinstance(m["age_hours"], (int, float)) and m["age_hours"] > STALE_HOURS:
        flags.append(f"odds ~{m['age_hours']:.0f}h old, may have moved")
    m["flags"] = flags
    return m


def combo_stats(legs, use_best=False):
    p = math.prod(r["fav_prob"] for r in legs)
    o = math.prod(r["best_odds" if use_best else "fav_odds"] for r in legs)
    return p, o, p * o - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("matches"); ap.add_argument("--top", type=int, default=5); ap.add_argument("--combo", type=int, default=4)
    ap.add_argument("--min-chance", type=float, default=0.5,
                    help="largest set of top favourites whose all-win chance stays at or above this")
    ap.add_argument("--json")
    a = ap.parse_args()

    groups, excluded = {}, []
    for m in json.load(open(a.matches)):
        r = check_row(m)
        if r["status"] != "OK":
            excluded.append(r); continue
        groups.setdefault(" vs ".join(sorted([name(m["player_a"]), name(m["player_b"])])), []).append(r)
    matches = [merge(rows) for rows in groups.values()]
    ranked = sorted(matches, key=lambda r: -r["fav_prob"])

    ladder = []
    for n in range(1, min(a.combo, len(ranked)) + 1):
        p, o, ev = combo_stats(ranked[:n])
        ladder.append({"legs": n, "players": [r["favourite"] for r in ranked[:n]], "chance_all_win": p,
                       "combined_odds": o, "expected_return": ev, "expected_return_best": combo_stats(ranked[:n], True)[2]})
    combo = ladder[-1] if len(ladder) >= 2 else {}
    safer = next((s for s in reversed(ladder) if s["legs"] >= 2 and s["chance_all_win"] >= a.min_chance), {})
    heavy = [r for r in ranked if r["tier"] == "heavy favourite"]

    print("MATCHES (fair chance = power method; proportional of the lead source in brackets)")
    for r in matches:
        extra = f", source: {r['source']}; basis: {r['basis']} ({', '.join(r['sources'])})" if len(r["sources"]) > 1 else f", source: {r['source']}"
        print(f"- [{r.get('tour') or ''} {r.get('event') or ''} {r.get('round') or ''}] {r['player_a']} {r['odds_a_dec']} vs "
              f"{r['player_b']} {r['odds_b_dec']} -> {r['fair_a']:.0%} / {r['fair_b']:.0%}  (prop {r['prop_a']:.0%}/{r['prop_b']:.0%}),"
              f" margin {r['margin']:.1%}{extra}" + (f"  !! {'; '.join(r['flags'])}" if r["flags"] else ""))
    for r in excluded:
        print(f"- {r.get('event', '')}: {r['player_a']} vs {r['player_b']}  {r['status']}")

    print(f"\nMOST PROBABLE WINNERS (top {a.top})")
    for i, r in enumerate(ranked[:a.top], 1):
        best = (f"; best price {r['best_odds']:.3g} ({r['best_source']}) -> {r['best_expected_return']:+.1%}"
                if r["best_odds"] > r["fav_odds"] else "")
        print(f"{i}. {r['favourite']} ({r.get('event') or ''}) {r['fav_prob']:.0%} at {r['fav_odds']:.3g} -> expected return "
              f"{r['fav_expected_return']:+.1%} per unit{best} [{r['tier']}]")

    if ladder:
        print("\nCHANCE ALL WIN, adding favourites in order: " + " | ".join(
            f"top {s['legs']}: {s['chance_all_win']:.0%}" for s in ladder))
    if combo:
        print(f"IF ALL TOP {combo['legs']} WIN: chance {combo['chance_all_win']:.0%}, combined odds {combo['combined_odds']:.2f}, "
              f"expected return {combo['expected_return']:+.1%} per unit (best prices: {combo['expected_return_best']:+.1%}; "
              f"assumes independent matches)")
    if safer:
        print(f"HIGHEST-PROBABILITY SET (all-win chance >= {a.min_chance:.0%}): top {safer['legs']} "
              f"({', '.join(safer['players'])}) -> {safer['chance_all_win']:.0%}, expected return {safer['expected_return']:+.1%}")
    else:
        print(f"HIGHEST-PROBABILITY SET: no set of 2+ favourites keeps the all-win chance >= {a.min_chance:.0%}")
    print(f"HEAVY FAVOURITES (>75%, historically won 84-86%): {len(heavy)}"
          + (f" - {', '.join(r['favourite'] + ' ' + format(r['fav_prob'], '.0%') for r in heavy)}" if heavy else ""))

    if a.json:
        json.dump({"matches": matches, "excluded": excluded, "ranked": [r["favourite"] for r in ranked],
                   "ladder": ladder, "combo": combo, "highest_probability_set": safer,
                   "heavy_favourites": [r["favourite"] for r in heavy]}, open(a.json, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
