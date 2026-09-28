"""Load Valuebetennis Pinnacle odds (all levels), parse settlement, de-vig. DEV years only (2021-2024)."""
import os, re, sys, numpy as np, pandas as pd
# TENNIS_ODDS_DIR: folder with valuebetennis-matchs-<year>.csv; RESEARCH_SRC: tennis_edge_research/src (for devig.py)
sys.path.insert(0, os.environ.get('RESEARCH_SRC', 'tennis_edge_research/src'))
import devig
D = os.environ.get('TENNIS_ODDS_DIR', 'valuebetennis-matches.csv') + '/'
CAT = {'ITF': 'ITF', 'Challenger': 'Challenger', 'Main tour': 'Tour 250/500', 'Masters': 'Masters/1000', 'Grand Chelem': 'Grand Slam'}
SET = re.compile(r'^(\d+)-(\d+)(\(\d+\))?$')


def set_done(a, b):
    hi, lo = max(a, b), min(a, b)
    return (hi == 6 and lo <= 4) or (hi == 7 and lo in (5, 6)) or (hi > 7 and hi - lo == 2) or (hi >= 10 and hi - lo >= 2)


def settle(score, bo):
    """(settles_under_pinnacle_rule, incomplete) from a joueur1-oriented score string. Scores in this file are often
    truncated, so "incomplete" is NOT a reliable retirement flag; only the settlement rule (>=1 full set) is used."""
    if not isinstance(score, str) or not score.strip():
        return False, False                          # walkover / unknown -> void
    sets = [SET.match(s) for s in score.split()]
    if not all(sets):
        return False, False
    sets = [(int(m.group(1)), int(m.group(2))) for m in sets]
    done = [s for s in sets if set_done(*s)]
    need = 3 if bo == 5 else 2
    w1 = sum(a > b for a, b in done); w2 = sum(b > a for a, b in done)
    complete = max(w1, w2) == need and len(done) == len(sets)
    if complete:
        return True, False
    return len(done) >= 1, True                     # retirement: settles only after one full set


def load(years=(2021, 2022, 2023, 2024)):
    d = pd.concat([pd.read_csv(f'{D}valuebetennis-matchs-{y}.csv', sep=';', encoding='utf-8-sig') for y in years])
    d = d[d.categorie.isin(CAT) & ~d.tournoi.str.contains('juniors', case=False, na=False)].copy()
    d['cat'] = d.categorie.map(CAT)
    d['date'] = pd.to_datetime(d.date); d['year'] = d.date.dt.year; d['day'] = d.date.dt.date
    d['qual'] = d.tour.isin([1, 2, 3])
    d['bo'] = np.where((d.categorie == 'Grand Chelem') & (d.genre == 'atp') & ~d.qual, 5, 3)
    s = [settle(sc, bo) for sc, bo in zip(d.score, d.bo)]
    d['settles'] = [x[0] for x in s]; d['retired'] = [x[1] for x in s]
    d['y'] = (d.vainqueur_id == d.joueur1_id).astype(int)
    for st, a, b in (('open', 'cote1_ouverture', 'cote2_ouverture'), ('close', 'cote1_cloture', 'cote2_cloture')):
        oa, ob = d[a].values, d[b].values
        ov = 1 / oa + 1 / ob - 1
        ok = (oa > 1) & (ob > 1) & (ov >= 0) & (ov <= 0.15)
        d[f'{st}_ok'] = ok; d[f'{st}_ov'] = np.where(ok, ov, np.nan)
        for m in ('proportional', 'power', 'shin'):
            d[f'{st}_{m}'] = np.where(ok, devig.METHODS[m](oa, ob), np.nan)
        # favourite-oriented view (power)
        p = d[f'{st}_power']
        fav1 = p >= 0.5
        d[f'{st}_fp'] = np.where(fav1, p, 1 - p)
        d[f'{st}_fodds'] = np.where(fav1, oa, ob)
        d[f'{st}_fprop'] = np.where(fav1, d[f'{st}_proportional'], 1 - d[f'{st}_proportional'])
        d[f'{st}_fshin'] = np.where(fav1, d[f'{st}_shin'], 1 - d[f'{st}_shin'])
        d[f'{st}_fwin'] = np.where(fav1, d.y, 1 - d.y)
    return d.reset_index(drop=True)
