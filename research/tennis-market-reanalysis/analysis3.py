from load import *
from sklearn.linear_model import LogisticRegression
d = load()
def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
lg = lambda p: np.log(p / (1 - p))
d['lvl'] = np.where(d.cat.isin(['Tour 250/500', 'Masters/1000', 'Grand Slam']), np.where(d.qual, 'TourQ', 'Tour'), d.cat)
rng = np.random.default_rng(0)
for st in ('open', 'close'):
    x = d[d[f'{st}_ok'] & d.settles].copy()
    # random orientation so the intercept is meaningful: work with favourite side, fav prob p, outcome fwin
    x['z'] = lg(x[f'{st}_fp'].clip(0.5 + 1e-6, 1 - 1e-6))
    tr, te = x[x.year <= 2023], x[x.year == 2024]
    print(f"\n[{st}] recalibration logit(won) = a + b*logit(power fav prob), fitted 2021-23, scored 2024")
    tot_base = tot_cal = n = 0
    for lv in ['ITF', 'Challenger', 'TourQ', 'Tour']:
        a, b = tr[tr.lvl == lv], te[te.lvl == lv]
        m = LogisticRegression(C=1e6).fit(a[['z']], a[f'{st}_fwin'])
        pc = m.predict_proba(b[['z']])[:, 1]
        base, cal = ll(b[f'{st}_fp'], b[f'{st}_fwin']), ll(pc, b[f'{st}_fwin'])
        # same fit on 2024 to see if params are stable
        m2 = LogisticRegression(C=1e6).fit(b[['z']], b[f'{st}_fwin'])
        print(f"  {lv:10} a={m.intercept_[0]:+.3f} b={m.coef_[0][0]:.3f} (2024 alone: a={m2.intercept_[0]:+.3f} b={m2.coef_[0][0]:.3f})  "
              f"2024 logloss power {base:.5f} -> recal {cal:.5f}  ({(cal-base)*1e4:+.1f} e-4, n={len(b)})")
        tot_base += base * len(b); tot_cal += cal * len(b); n += len(b)
    print(f"  ALL 2024: {tot_base/n:.5f} -> {tot_cal/n:.5f}")
    # bootstrap by event week for Tour only
    b = te[te.lvl == 'Tour']; a = tr[tr.lvl == 'Tour']
    m = LogisticRegression(C=1e6).fit(a[['z']], a[f'{st}_fwin']); b = b.assign(pc=m.predict_proba(b[['z']])[:, 1])
    b['wk'] = b.date.dt.isocalendar().week.values
    y, p0, p1 = b[f'{st}_fwin'].values, b[f'{st}_fp'].clip(1e-6, 1-1e-6).values, b.pc.values
    l0 = -(y*np.log(p0)+(1-y)*np.log(1-p0)); l1 = -(y*np.log(p1)+(1-y)*np.log(1-p1)); diff = l1 - l0
    wks = b.wk.values; uw = np.unique(wks); bs = []
    for _ in range(2000):
        s = rng.choice(uw, len(uw)); bs.append(np.concatenate([diff[wks == w] for w in s]).mean())
    print(f"  Tour main 2024 recal - power: {diff.mean()*1e4:+.1f}e-4, 95% CI [{np.percentile(bs,2.5)*1e4:+.1f}, {np.percentile(bs,97.5)*1e4:+.1f}]e-4")
