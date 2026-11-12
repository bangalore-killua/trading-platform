import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
OUT = sys.argv[1]
P = lambda n: pd.read_parquet(f'{OUT}/{n}.parquet').astype('float64')
O, H, L, C, V, D = [P('stk_'+k) for k in ['Open','High','Low','Close','Volume','DLV_QTY']]
fr = [1/2, 1/3, 1/4, 1/5, 1/6, 1/10, 1/20, 2/3, 3/5, 2/5, 3/4, 4/5, 5/6, 2.0, 5.0, 10.0]
fr = np.array(fr)
n_fix = 0; log = []
for col in C.columns:
    c = C[col].values; o = O[col].values
    idx = np.where(~np.isnan(c))[0]
    if len(idx) < 2: continue
    prev = pd.Series(c).ffill().shift(1).values
    gap = o / prev
    dts = C.index.values; lastd = pd.Series(np.where(np.isnan(c), np.datetime64('NaT'), dts)).ffill().shift(1).values
    age = (dts - lastd).astype('timedelta64[D]').astype(float)
    cand = np.where(((gap < 0.72) | (gap > 1.4)) & (age <= 6) & (gap > 0))[0]
    for t in cand:
        g = gap[t]
        k = fr[np.argmin(np.abs(fr - g))]
        if True:
            for X in (O, H, L, C): X.iloc[:t, X.columns.get_loc(col)] *= g
            V.iloc[:t, V.columns.get_loc(col)] /= g; D.iloc[:t, D.columns.get_loc(col)] /= g
            n_fix += 1; log.append((col, C.index[t].date(), round(g, 3), round(k, 3)))
            c = C[col].values; prev = pd.Series(c).ffill().shift(1).values; gap = O[col].values / prev
print('unadjusted corporate actions repaired:', n_fix)
print(pd.DataFrame(log, columns=['stock','date','gap','ratio']).assign(year=lambda d: pd.to_datetime(d.date).dt.year).groupby('year').size().to_string())
R = C.pct_change(fill_method=None)
print('remaining one-day moves < -33%:', int((R < -0.33).sum().sum()), '| > +60%:', int((R > 0.6).sum().sum()))
for k, X in zip(['Open','High','Low','Close','Volume','DLV_QTY'], [O, H, L, C, V, D]):
    X.astype('float32').to_parquet(f'{OUT}/adj_{k}.parquet')
