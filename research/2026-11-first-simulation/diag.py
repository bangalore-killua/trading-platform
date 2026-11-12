import sys, runpy, io, contextlib
import numpy as np, pandas as pd
sys.argv = ['swing.py', sys.argv[1] if len(sys.argv) > 1 else 'out', '0.002', 'diag']
src = open('swing.py').read()
src = src[:src.index("res = {'A4': a4}")]
g = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, 'swing_head', 'exec'), g)
simulate, setup_mtf, dates, C, O, H, L = g['simulate'], g['setup_mtf'], g['dates'], g['C'], g['O'], g['H'], g['L']
r, eqs, tdf = simulate(setup_mtf, 'diag', stopmode='atr2', hold=20, quiet=True)
print(tdf.ret.describe(percentiles=[.01,.05,.25,.5,.75,.95,.99]).round(4).to_string())
print(tdf.groupby('why').agg(n=('ret','size'), mean_ret=('ret','mean'), mean_R=('R','mean'), min_ret=('ret','min')).round(4).to_string())
print('trades with ret < -20%:', (tdf.ret < -0.2).sum(), ' sum of their returns:', round(tdf.ret[tdf.ret < -0.2].sum(), 2), ' of total', round(tdf.ret.sum(), 2))
w = tdf.sort_values('ret').head(6)
for _, x in w.iterrows():
    j = int(x.j); n = C.columns[j]; t0 = dates.get_loc(x.d0); t1 = dates.get_loc(x.d1)
    print(n, x.d0.date(), x.d1.date(), round(x.ret, 3), x.why, '| closes:', C.iloc[t0-1:t1+1, j].round(1).tolist()[:8], '| open at exit', round(O.iloc[t1, j], 1))
hold = (tdf.d1 - tdf.d0).dt.days
print('median calendar days held', hold.median(), '| avg positions open (approx):', round(hold.sum() / (dates[-1] - pd.Timestamp('2005-01-01')).days, 2))
# gross expectancy in R units
print('mean R per trade (gross of costs):', round(tdf.R.mean(), 3), '| by period:', tdf.groupby(tdf.d0.dt.year >= 2017).R.mean().round(3).to_dict())
