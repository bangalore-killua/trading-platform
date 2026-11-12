import sys, json
import numpy as np, pandas as pd
OUT = sys.argv[1]; COST = float(sys.argv[2]) if len(sys.argv) > 2 else 0.002
TAG = sys.argv[3] if len(sys.argv) > 3 else 'base'
P = lambda n: pd.read_parquet(f'{OUT}/{n}.parquet')
O, H, L, C, V, D = [P('adj_'+k).astype('float64') for k in ['Open','High','Low','Close','Volume','DLV_QTY']]
IC = P('idx_Close').astype('float64')
dates = C.index; T, N = C.shape
R = C.pct_change(fill_method=None)
bad = (R > 1.0) | (R < -0.6)
R = R.mask(bad)
badflag = bad.rolling(252, min_periods=1).max().fillna(0).astype(bool)

# ---------- point-in-time universe: top 200 by 126d median turnover ----------
turn = (C * V)
medturn = turn.rolling(126, min_periods=100).median()
hist = C.notna().cumsum()
elig = (hist >= 252) & (C >= 20) & (~badflag) & medturn.notna()
rank = medturn.where(elig).rank(axis=1, ascending=False)
month_end = pd.Series(dates, index=dates).groupby([dates.year, dates.month]).last().values
U = (rank <= 200).loc[month_end].reindex(dates).ffill().shift(1).fillna(False).astype(bool)   # known the day before
print('universe size median', int(U.sum(axis=1)[dates >= '2005'].median()))

def stats(eq, label):
    out = {}
    for nm, a, b in [('full', '2005-01-01', '2024-12-31'), ('IS 2005-16', '2005-01-01', '2016-12-31'), ('OOS 2017-24', '2017-01-01', '2024-12-31')]:
        e = eq[(eq.index >= a) & (eq.index <= b)]
        r = e.pct_change().dropna()
        yrs = len(r) / 252
        cagr = (e.iloc[-1] / e.iloc[0]) ** (1 / yrs) - 1
        vol = r.std() * np.sqrt(252)
        dd = (e / e.cummax() - 1).min()
        out[nm] = dict(cagr=round(cagr * 100, 1), vol=round(vol * 100, 1), sharpe=round(r.mean() * 252 / vol, 2) if vol > 0 else 0, maxdd=round(dd * 100, 1))
    print(f'{label:42s}', ' | '.join(f"{k}: CAGR {v['cagr']:5.1f}% Sh {v['sharpe']:4.2f} DD {v['maxdd']:6.1f}%" for k, v in out.items()))
    return out

res = {}
# ---------- benchmarks ----------
ew_ret = R.where(U).mean(axis=1).fillna(0)
ew = (1 + ew_ret).cumprod(); ew = ew[ew.index >= '2005-01-01']
res['bench_equal_weight_universe'] = stats(ew, 'BENCH equal-weight universe (same bias)')
n50 = IC['nifty 50'].dropna(); n500 = IC['nifty 500'].dropna()
def simple(e, a='2017-01-01'):
    e = e[e.index >= a]; r = e.pct_change().dropna(); yrs = len(r)/252
    return dict(cagr=round(((e.iloc[-1]/e.iloc[0])**(1/yrs)-1)*100,1), sharpe=round(r.mean()*252/(r.std()*np.sqrt(252)),2), maxdd=round((e/e.cummax()-1).min()*100,1))
res['bench_nifty50_2017_24'] = simple(n50); res['bench_nifty500_2017_24'] = simple(n500)
print('BENCH real Nifty 50  2017-24 (price only):', res['bench_nifty50_2017_24'])
print('BENCH real Nifty 500 2017-24 (price only):', res['bench_nifty500_2017_24'])

# ---------- A2: cross-sectional multi-signal ranking ----------
def z(x):
    x = x.where(U)
    lo, hi = x.quantile(0.02, axis=1), x.quantile(0.98, axis=1)
    x = x.clip(lo, hi, axis=0)
    return x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1), axis=0)
sig = {
 'mom_12_1': C.shift(21) / C.shift(252) - 1,
 'mom_6_1': C.shift(21) / C.shift(126) - 1,
 'near_52w_high': C / C.rolling(252, min_periods=200).max(),
 'low_vol': -R.rolling(126, min_periods=100).std(),
 'reversal_5d': -(C / C.shift(5) - 1),
 'delivery_accum': (D / V).rolling(20, min_periods=10).mean() / (D / V).rolling(120, min_periods=60).mean(),
}
Z = {k: z(v) for k, v in sig.items()}
fwd21 = (C.shift(-22) / C.shift(-1) - 1)       # enter next close, hold 21d
print('\nSingle-signal test: top-quintile minus bottom-quintile forward 21d return, and rank IC')
sigres = {}
for k, zz in Z.items():
    q = zz.rank(axis=1, pct=True)
    row = {}
    for nm, a, b in [('IS', '2005', '2016'), ('OOS', '2017', '2024')]:
        m = (dates >= a) & (dates <= b + '-12-31')
        top = fwd21.where(q >= 0.8)[m].mean(axis=1); bot = fwd21.where(q <= 0.2)[m].mean(axis=1)
        ic = zz[m].rank(axis=1).corrwith(fwd21[m].rank(axis=1), axis=1)
        row[nm] = dict(spread_pct=round((top - bot).mean() * 100, 2), ic=round(ic.mean(), 3), ic_t=round(ic.mean() / ic.std() * np.sqrt(m.sum() / 21), 1))
    sigres[k] = row
    print(f'  {k:16s} IS spread {row["IS"]["spread_pct"]:5.2f}%  IC {row["IS"]["ic"]:6.3f} (t {row["IS"]["ic_t"]:4.1f}) | OOS spread {row["OOS"]["spread_pct"]:5.2f}%  IC {row["OOS"]["ic"]:6.3f} (t {row["OOS"]["ic_t"]:4.1f})')
res['signals'] = sigres

def run_rank(comp, topn=20, every=21, regime=None, cap_per_stock=None):
    comp = comp.where(U)
    w = pd.DataFrame(0.0, index=dates, columns=C.columns)
    cur = pd.Series(0.0, index=C.columns)
    start = dates.get_loc(dates[dates >= '2005-01-01'][0])
    turn_total = 0.0
    rets = np.zeros(T)
    Rv = R.fillna(0).values
    cur_v = cur.values.copy()
    reb_days = set(range(start, T, every))
    pending = None
    for t in range(start, T):
        # apply weights decided yesterday at today's close: today's return earned on yesterday's holdings
        rets[t] = (cur_v * Rv[t]).sum()
        if pending is not None:
            tw = pending; pending = None
            tr = np.abs(tw - cur_v).sum()
            rets[t] -= tr * COST
            turn_total += tr
            cur_v = tw
        else:
            g = cur_v * (1 + Rv[t]); s = g.sum() + (1 - cur_v.sum())
            cur_v = g / s if s > 0 else cur_v
        if t in reb_days:
            row = comp.iloc[t].dropna()
            if len(row) >= topn:
                pick = row.nlargest(topn).index
                tw = np.zeros(N); tw[C.columns.get_indexer(pick)] = 1.0 / topn
                if regime is not None and not regime.iloc[t]:
                    tw[:] = 0.0
                pending = tw
    eq = pd.Series((1 + rets).cumprod(), index=dates)
    yrs = (T - start) / 252
    return eq[eq.index >= '2005-01-01'], turn_total / yrs

core = (Z['mom_12_1'] + Z['mom_6_1'] + Z['near_52w_high'] + Z['low_vol']) / 4
allsig = sum(Z[k].fillna(0) for k in Z) / len(Z)
ewidx = (1 + ew_ret).cumprod()
regime = (ewidx > ewidx.rolling(200).mean())
print('\nA2 ranking portfolios, top 20 equal weight, cost', COST, 'per side')
for label, comp, kw in [
    ('RANK momentum+quality, monthly', core, {}),
    ('RANK all 6 signals, monthly', allsig, {}),
    ('RANK momentum+quality, weekly', core, dict(every=5)),
    ('RANK momentum+quality, monthly + regime', core, dict(regime=regime)),
    ('RANK momentum+quality, top 40 monthly', core, dict(topn=40)),
]:
    eq, to = run_rank(comp, **kw)
    r = stats(eq, label); r['turnover_x_per_year'] = round(to / 2, 1); res[label] = r
    if label == 'RANK momentum+quality, monthly': eq.to_frame('eq').to_parquet(f'{OUT}/eq_rank_{TAG}.parquet')
    print('    annual one-way turnover x', round(to / 2, 1))


# ---------- stress and year-by-year ----------
eqA, _ = run_rank(core); eqB, _ = run_rank(core, regime=regime)
eqC, _ = run_rank(core.shift(2), regime=regime.shift(2).fillna(False))          # act two days late
eqD, _ = run_rank(core, topn=10, regime=regime)
res['RANK + regime, signals 2 days late'] = stats(eqC, 'STRESS rank + regime, 2 days late')
res['RANK + regime, top 10'] = stats(eqD, 'STRESS rank + regime, top 10 only')
U100 = (rank <= 100).loc[month_end].reindex(dates).ffill().shift(1).fillna(False).astype(bool)
eqE, _ = run_rank(core.where(U100), regime=regime)
res['RANK + regime, top-100 liquid only'] = stats(eqE, 'STRESS rank + regime, 100 most liquid only')
yr = lambda e: e.groupby(e.index.year).last().pct_change().mul(100).round(1)
tab = pd.DataFrame({'rank': yr(eqA), 'rank+regime': yr(eqB), 'equal-wt universe': yr(ew), 'Nifty 500': yr(n500)})
print('\nYear-by-year returns %'); print(tab.loc[2006:].to_string())
t2 = tab.loc[2017:2024]
print('years 2017-24 where rank+regime beat Nifty 500:', int((t2['rank+regime'] > t2['Nifty 500']).sum()), 'of', len(t2))
t3 = tab.loc[2006:2024]
print('years 2006-24 where rank+regime beat equal-weight universe:', int((t3['rank+regime'] > t3['equal-wt universe']).sum()), 'of', len(t3))
res['yearly'] = tab.loc[2006:].to_dict()
rb = eqB.pct_change().dropna(); 
print('rank+regime: worst month %', round(eqB.resample('ME').last().pct_change().min()*100,1), '| share of months positive %', round((eqB.resample('ME').last().pct_change()>0).mean()*100,1), '| time in cash %', round((~regime[regime.index>='2005']).mean()*100,1))
eqB.to_frame('eq').to_parquet(f'{OUT}/eq_rankreg_{TAG}.parquet'); ew.to_frame('eq').to_parquet(f'{OUT}/eq_ew.parquet')
json.dump(res, open(f'{OUT}/daily_{TAG}.json', 'w'), indent=1)
