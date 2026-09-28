from load import *
d = load()
rng = np.random.default_rng(1)
SK = d[d.cat.isin(['Challenger', 'Tour 250/500', 'Masters/1000', 'Grand Slam']) & d.settles]
print("=== Accumulator ladder: top-N favourites of the day (skill universe: tour + Challenger/WTA125)")
for st in ('open', 'close'):
    x = SK[SK[f'{st}_ok']]
    for mode in ('whole day', '12 random matches/day'):
        rows = []
        for day, g in x.groupby('day'):
            if mode != 'whole day':
                if len(g) < 12: continue
                g = g.sample(12, random_state=int(rng.integers(1e9)))
            g = g.sort_values(f'{st}_fp', ascending=False)
            for n in (1, 2, 3, 4, 5):
                if len(g) >= n:
                    t = g.head(n)
                    rows.append((n, t[f'{st}_fp'].prod(), t[f'{st}_fwin'].prod(), np.prod(t[f'{st}_fodds']), t.year.iloc[0]))
        r = pd.DataFrame(rows, columns=['n', 'pred', 'won', 'odds', 'year'])
        r['profit'] = np.where(r.won == 1, r.odds - 1, -1)
        g = r.groupby('n').agg(days=('won', 'size'), pred=('pred', 'mean'), won=('won', 'mean'), roi=('profit', 'mean'))
        print(f"--- [{st}] {mode}"); print(g.round(4).to_string())
