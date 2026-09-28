from load import *
d = load()
def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
E = d[d.year <= 2023]; V = d[d.year == 2024]
print("=== 1. De-vig methods: log loss (lower better), favourite-oriented calibration  [2021-23 | 2024]")
for st in ('open', 'close'):
    for c in ['ITF', 'Challenger', 'Tour 250/500', 'Masters/1000', 'Grand Slam']:
        out = []
        for part in (E, V):
            x = part[(part.cat == c) & part[f'{st}_ok'] & part.settles]
            out.append(f"n={len(x):6d} " + " ".join(f"{m[:4]} {ll(x[f'{st}_{m}'], x.y):.4f}" for m in ('proportional', 'power', 'shin'))
                       + f" | fav won {x[f'{st}_fwin'].mean():.3f} vs power {x[f'{st}_fp'].mean():.3f} prop {x[f'{st}_fprop'].mean():.3f} shin {x[f'{st}_fshin'].mean():.3f}")
        print(f"{st:5} {c:13} " + "  ||  ".join(out))
print("\n=== 2. Pinnacle margin (median overround)")
print(d[d.open_ok].groupby('cat')[['open_ov', 'close_ov']].median().round(4))
print("\n=== 3. Opening vs closing (same matches, both prices, power): log loss")
for c in ['ITF', 'Challenger', 'Tour 250/500', 'Masters/1000', 'Grand Slam']:
    x = d[(d.cat == c) & d.open_ok & d.close_ok & d.settles & (d.year <= 2023)]
    fl = ((x.open_power >= .5) != (x.close_power >= .5)).mean()
    mv = (x.close_fp - x.open_fp).abs().mean()
    print(f"{c:13} n={len(x):6d} open {ll(x.open_power, x.y):.4f} close {ll(x.close_power, x.y):.4f}  favourite flips {fl:.1%}, mean |move| {mv:.3f}")
