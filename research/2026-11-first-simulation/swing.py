import sys, json
import numpy as np, pandas as pd
OUT = sys.argv[1]; COST = float(sys.argv[2]); TAG = sys.argv[3]
RMULT = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
HOLD = int(sys.argv[5]) if len(sys.argv) > 5 else 15
P = lambda n: pd.read_parquet(f'{OUT}/{n}.parquet').astype('float64')
O, H, L, C, V = [P('adj_'+k) for k in ['Open','High','Low','Close','Volume']]
dates = C.index; T, N = C.shape
R = C.pct_change(fill_method=None); bad = (R > 1.0) | (R < -0.6)
badflag = bad.rolling(252, min_periods=1).max().fillna(0).astype(bool)
medturn = (C * V).rolling(126, min_periods=100).median()
elig = (C.notna().cumsum() >= 252) & (C >= 20) & (~badflag) & medturn.notna()
rank = medturn.where(elig).rank(axis=1, ascending=False)
month_end = pd.Series(dates, index=dates).groupby([dates.year, dates.month]).last().values
U = (rank <= 200).loc[month_end].reindex(dates).ffill().shift(1).fillna(False).astype(bool)

# ----- higher timeframe: completed weekly bars only -----
wk = dates.to_period('W-FRI')
Wc = C.groupby(wk).last(); Wl = L.groupby(wk).min(); Wh = H.groupby(wk).max()
w_up = (Wc > Wc.rolling(30, min_periods=25).mean()) & (Wc.rolling(10).mean() > Wc.rolling(30, min_periods=25).mean()) \
       & (Wl.rolling(4).min() > Wl.rolling(4).min().shift(4)) & (Wh.rolling(4).max() > Wh.rolling(4).max().shift(4))
w_up = w_up.shift(1)                                   # only weeks that have finished
weekly_up = pd.DataFrame(w_up.reindex(wk).values, index=dates, columns=C.columns).fillna(False).astype(bool)

# ----- daily timeframe: pullback into value area, then a price-action trigger -----
pc = C.shift(1)
tr = pd.concat([(H - L).stack(), (H - pc).abs().stack(), (L - pc).abs().stack()], axis=1).max(axis=1).unstack().reindex_like(C)
ATR = tr.rolling(14).mean()
ema20 = C.ewm(span=20, adjust=False, min_periods=20).mean(); ema50 = C.ewm(span=50, adjust=False, min_periods=50).mean()
pullback = (L.rolling(5).min() <= ema20 + 0.5 * ATR) & (C > ema50) & (C.rolling(20).max().shift(1) / C - 1 >= 0.03)
body = (C - O); rng = (H - L).replace(0, np.nan)
engulf = (body > 0) & (body.shift(1) < 0) & (C >= O.shift(1)) & (O <= C.shift(1))
hammer = ((np.minimum(O, C) - L) >= 2 * body.abs()) & ((H - np.maximum(O, C)) <= 0.3 * rng) & (C > O)
strong = (C > H.shift(1)) & ((C - L) / rng >= 0.75)
trigger = engulf | hammer | strong
setup_mtf = U & weekly_up & pullback & trigger
setup_notf = U & pullback & trigger                     # same entry, no higher-timeframe filter
setup_trigonly = U & trigger                            # candle alone
rs = C / C.shift(126) - 1

# ----- A4: do the candles alone predict anything? forward 5d return, entry next open -----
f5 = C.shift(-5) / O.shift(-1) - 1
print('A4 forward 5-day return after signal (entry next open, before costs)')
a4 = {}
for nm, m in [('any day in universe', U), ('bullish engulfing', U & engulf), ('hammer', U & hammer), ('strong close above prior high', U & strong),
              ('candle + weekly uptrend', U & trigger & weekly_up), ('candle + weekly uptrend + daily pullback', setup_mtf)]:
    row = {}
    for pn, a, b in [('IS', '2005', '2016-12-31'), ('OOS', '2017', '2024-12-31')]:
        mm = m[(dates >= a) & (dates <= b)]; x = pd.Series(f5[(dates >= a) & (dates <= b)].where(mm).values.ravel()).dropna()
        row[pn] = dict(n=int(len(x)), mean_pct=round(x.mean() * 100, 2), win=round((x > 0).mean() * 100, 1))
    a4[nm] = row
    print(f'  {nm:42s} IS n={row["IS"]["n"]:7d} mean {row["IS"]["mean_pct"]:5.2f}% win {row["IS"]["win"]:4.1f}% | OOS n={row["OOS"]["n"]:7d} mean {row["OOS"]["mean_pct"]:5.2f}% win {row["OOS"]["win"]:4.1f}%')

# ----- A3: event-driven portfolio simulation -----
def simulate(setup, label, max_pos=10, cap=0.10, risk=0.01, stopmode='swing', trail=False, rmult=None, hold=None, quiet=False):
    rmult = RMULT if rmult is None else rmult; hold = HOLD if hold is None else hold
    low10 = L.rolling(10).min().values
    Ov, Hv, Lv, Cv = O.values, H.values, L.values, C.values
    S = setup.values; RS = rs.values; A = ATR.values
    swing_low = L.rolling(5).min().values
    start = dates.get_loc(dates[dates >= '2005-01-01'][0])
    cash = 1.0; pos = {}; eq = np.ones(T); trades = []
    for t in range(start, T):
        # manage open positions on day t
        for j in list(pos):
            p = pos[j]; o, h, l, c = Ov[t, j], Hv[t, j], Lv[t, j], Cv[t, j]
            if np.isnan(c):
                p['stale'] += 1
                if p['stale'] > 10:
                    px = p['last']; cash += p['sh'] * px * (1 - COST); trades.append((p['d0'], dates[t], j, px / p['entry'] - 1 - 2 * COST, (px - p['entry']) / p['R'], 'stale')); del pos[j]
                continue
            p['stale'] = 0; p['last'] = c; p['days'] += 1; px = None
            if o <= p['stop']: px, why = o, 'gap_stop'
            elif l <= p['stop']: px, why = p['stop'], 'stop'            # stop checked before target (conservative)
            elif o >= p['tgt']: px, why = o, 'gap_target'
            elif h >= p['tgt']: px, why = p['tgt'], 'target'
            elif p['days'] >= hold: px, why = c, 'time'
            if px is not None:
                cash += p['sh'] * px * (1 - COST)
                trades.append((p['d0'], dates[t], j, px / p['entry'] * (1 - COST) / (1 + COST) - 1, (px - p['entry']) / p['R'], why)); del pos[j]
            elif trail and not np.isnan(low10[t, j]):
                p['stop'] = max(p['stop'], low10[t, j])
        # new entries: setups flagged at yesterday's close, buy-stop above yesterday's high
        if t > start:
            cand = np.where(S[t - 1])[0]
            cand = [j for j in cand if j not in pos and not np.isnan(RS[t - 1, j])]
            cand.sort(key=lambda j: -RS[t - 1, j])
            equity_now = cash + sum(p['sh'] * p['last'] for p in pos.values())
            for j in cand:
                if len(pos) >= max_pos: break
                o, h = Ov[t, j], Hv[t, j]; trig = Hv[t - 1, j]
                if np.isnan(o) or np.isnan(h) or h <= trig: continue
                entry = max(o, trig); stop = (swing_low[t - 1, j] - 0.25 * A[t - 1, j]) if stopmode == 'swing' else (entry - 2.0 * A[t - 1, j])
                Rr = entry - stop
                if not (0.01 <= Rr / entry <= 0.12): continue
                size = min(risk * equity_now / (Rr / entry), cap * equity_now, cash / (1 + COST))
                if size < 0.01 * equity_now: continue
                sh = size / entry; cash -= size * (1 + COST)
                pos[j] = dict(sh=sh, entry=entry, stop=stop, tgt=(np.inf if trail else entry + rmult * Rr), R=Rr, days=0, d0=dates[t], last=Cv[t, j] if not np.isnan(Cv[t, j]) else entry, stale=0)
                # same-day stop if the entry bar itself trades through the stop after entry (conservative: assume it can)
                if Lv[t, j] <= stop and Cv[t, j] <= entry:
                    p = pos[j]; cash += p['sh'] * stop * (1 - COST)
                    trades.append((dates[t], dates[t], j, stop / entry * (1 - COST) / (1 + COST) - 1, -1.0, 'stop_day0')); del pos[j]
        eq[t] = cash + sum(p['sh'] * p['last'] for p in pos.values())
    eqs = pd.Series(eq, index=dates); eqs = eqs[eqs.index >= '2005-01-01']
    tdf = pd.DataFrame(trades, columns=['d0', 'd1', 'j', 'ret', 'R', 'why'])
    out = {}
    for nm, a, b in [('full', '2005-01-01', '2024-12-31'), ('IS 2005-16', '2005-01-01', '2016-12-31'), ('OOS 2017-24', '2017-01-01', '2024-12-31')]:
        e = eqs[(eqs.index >= a) & (eqs.index <= b)]; r = e.pct_change().dropna(); yrs = len(r) / 252
        tt = tdf[(tdf.d0 >= a) & (tdf.d0 <= b)]
        w = tt.ret[tt.ret > 0]; l = tt.ret[tt.ret <= 0]
        out[nm] = dict(cagr=round(((e.iloc[-1] / e.iloc[0]) ** (1 / yrs) - 1) * 100, 1), sharpe=round(r.mean() * 252 / (r.std() * np.sqrt(252)), 2),
                       maxdd=round((e / e.cummax() - 1).min() * 100, 1), trades=int(len(tt)), win_pct=round((tt.ret > 0).mean() * 100, 1),
                       avg_win_pct=round(w.mean() * 100, 2), avg_loss_pct=round(l.mean() * 100, 2),
                       profit_factor=round(w.sum() / -l.sum(), 2) if len(l) else None, avg_trade_pct=round(tt.ret.mean() * 100, 2),
                       avg_exposure=None)
    if not quiet: print(f'{label:46s}', ' | '.join(f"{k}: CAGR {v['cagr']:5.1f}% Sh {v['sharpe']:4.2f} DD {v['maxdd']:6.1f}% n={v['trades']} win {v['win_pct']}% PF {v['profit_factor']} avg {v['avg_trade_pct']}%" for k, v in out.items()))
    out['exit_mix'] = tdf.why.value_counts(normalize=True).round(3).to_dict()
    return out, eqs, tdf

res = {'A4': a4}
rng_ = np.random.default_rng(7)
rand = U & pd.DataFrame(rng_.random(C.shape) < setup_mtf.values[U.values].mean() if False else rng_.random(C.shape) < (setup_mtf.sum().sum() / U.sum().sum()), index=dates, columns=C.columns)
print(f'\nA3 swing portfolios, cost {COST}/side, 1% risk per trade, max 10 positions, 10% cap per stock')
variants = [
 ('V1 tight swing-low stop, 2R target, 15d', dict()),
 ('V2 2-ATR stop, 2R target, 20d', dict(stopmode='atr2', hold=20)),
 ('V3 2-ATR stop, 3R target, 40d', dict(stopmode='atr2', rmult=3.0, hold=40)),
 ('V4 2-ATR stop, trail 10d low, 60d', dict(stopmode='atr2', trail=True, hold=60)),
]
for vl, kw in variants:
    for label, s_ in [('multi-timeframe', setup_mtf), ('daily only', setup_notf), ('candle only', setup_trigonly), ('RANDOM entry', rand)]:
        r, eqs, tdf = simulate(s_, f'{vl} | {label}', **kw); res[f'{vl} | {label}'] = r
        if s_ is setup_mtf:
            eqs.to_frame('eq').to_parquet(f'{OUT}/eq_swing_{TAG}_{vl[:2]}.parquet')
            top = tdf.groupby('j').size().sort_values(ascending=False)
            print('      exits:', r['exit_mix'], '| stocks traded:', tdf.j.nunique(), '| avg win', r['full']['avg_win_pct'], '% avg loss', r['full']['avg_loss_pct'], '%')
json.dump(res, open(f'{OUT}/swing_{TAG}.json', 'w'), indent=1, default=str)
