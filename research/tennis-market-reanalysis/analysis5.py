from load import *
d = load()
d['lvl'] = np.where(d.cat.isin(['Tour 250/500', 'Masters/1000', 'Grand Slam']), np.where(d.qual, 'Tour Q', 'Tour main'), d.cat)
st = 'close'
x = d[d[f'{st}_ok'] & d.settles & (d.cat != 'ITF')].copy()
x['seg_bo5'] = np.where(x.bo == 5, 'Bo5 (men slam main)', 'Bo3')
x['profit'] = np.where(x[f'{st}_fwin'] == 1, x[f'{st}_fodds'] - 1, -1)
def seg(col):
    for yrs, lab in (((2021, 2022, 2023), '21-23'), ((2024,), '2024')):
        for heavy in (False, True):
            s = x[x.year.isin(yrs) & ((x[f'{st}_fp'] >= .75) if heavy else True)]
            g = s.groupby(['lvl', col]).agg(n=('y', 'size'), pred=(f'{st}_fp', 'mean'), won=(f'{st}_fwin', 'mean'), roi=('profit', 'mean'))
            g['diff'] = g.won - g.pred; g['z'] = g['diff'] / np.sqrt(g.pred * (1 - g.pred) / g.n)
            print(f"-- {col} {lab} {'fav>=75%' if heavy else 'all favs'}"); print(g[g.n >= 150].round(3).to_string())
seg('genre'); seg('surface'); seg('seg_bo5')
