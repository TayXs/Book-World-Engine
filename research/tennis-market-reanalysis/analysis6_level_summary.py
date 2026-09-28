"""Per-level summary used for LEVEL_HISTORY in fair_odds.py (2021-24, favourite = higher power-method chance)."""
from load import *
d = load()
d['lvl'] = np.where(d.cat.isin(['Tour 250/500', 'Masters/1000', 'Grand Slam']), np.where(d.qual, 'Tour qualifying', 'Tour main draw'), d.cat)
for st in ('open', 'close'):
    x = d[d[f'{st}_ok'] & d.settles].copy()
    x['profit'] = np.where(x[f'{st}_fwin'] == 1, x[f'{st}_fodds'] - 1, -1)
    h = x[f'{st}_fp'] >= .75
    g = x.groupby('lvl').agg(n=('y', 'size'), fav_won=(f'{st}_fwin', 'mean'), fav_roi=('profit', 'mean'), cut=(f'{st}_ov', 'median'))
    g['heavy_n'] = x[h].groupby('lvl').size(); g['heavy_won'] = x[h].groupby('lvl')[f'{st}_fwin'].mean()
    g['heavy_pred'] = x[h].groupby('lvl')[f'{st}_fp'].mean(); g['heavy_roi'] = x[h].groupby('lvl').profit.mean()
    print(st, '2021-24'); print(g.round(3).to_string())
