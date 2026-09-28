from load import *
d = load()
B = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0]
def band_table(x, st, label):
    x = x[x[f'{st}_ok'] & x.settles].copy()
    x['band'] = pd.cut(x[f'{st}_fp'], B, right=False)
    x['profit'] = np.where(x[f'{st}_fwin'] == 1, x[f'{st}_fodds'] - 1, -1)
    g = x.groupby('band', observed=True).agg(n=('y', 'size'), pred=(f'{st}_fp', 'mean'), won=(f'{st}_fwin', 'mean'), roi=('profit', 'mean'))
    g['won-pred'] = g.won - g.pred
    g['se_roi'] = x.groupby('band', observed=True).profit.std() / np.sqrt(g.n)
    print(f"--- {label} [{st}] n={len(x)} fav won {x[f'{st}_fwin'].mean():.3f} (pred {x[f'{st}_fp'].mean():.3f}), all-fav ROI {x.profit.mean():+.3%}")
    print(g.round(4).to_string())
SK = d.cat.isin(['Challenger', 'Tour 250/500', 'Masters/1000', 'Grand Slam'])
for yrs, lab in (((2021, 2022, 2023), '2021-23'), ((2024,), '2024')):
    part = d[d.year.isin(yrs)]
    print(f"\n##### {lab}")
    for st in ('open', 'close'):
        band_table(part[part.cat.isin(['Tour 250/500', 'Masters/1000', 'Grand Slam']) & ~part.qual], st, 'TOUR main draw')
        band_table(part[part.cat.isin(['Tour 250/500', 'Masters/1000', 'Grand Slam']) & part.qual], st, 'TOUR qualifying')
        band_table(part[(part.cat == 'Challenger')], st, 'CHALLENGER (all)')
        band_table(part[(part.cat == 'ITF')], st, 'ITF')
