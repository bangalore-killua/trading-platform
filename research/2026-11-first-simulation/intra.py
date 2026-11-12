import sys, glob, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]; RT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0004; TAG = sys.argv[4] if len(sys.argv) > 4 else 'base'
fs = sorted(glob.glob(f'{SRC}/1min/*/*.csv'))
df = pd.concat([pd.read_csv(f, usecols=['Timestamp','Open','High','Low','Close']) for f in fs])
df['ts'] = pd.to_datetime(df.Timestamp); df = df.drop_duplicates('ts').set_index('ts').sort_index()
df = df.between_time('09:15', '15:29')
df['d'] = df.index.date
print('1-min bars', len(df), df.index[0], df.index[-1], 'days', df.d.nunique())
cnt = df.groupby('d').size(); good = cnt[cnt >= 360].index
print('full sessions', len(good), '| dropped short/odd sessions', len(cnt) - len(good))
df = df[df.d.isin(set(good))]
daily = df.groupby('d').agg(o=('Open', 'first'), h=('High', 'max'), l=('Low', 'min'), c=('Close', 'last'))
daily['sma20'] = daily.c.rolling(20).mean(); daily['bias'] = np.sign(daily.c - daily.sma20).shift(1)    # known before the open
daily['pc'] = daily.c.shift(1)
# continuous 5m / 15m series with EMAs carried across days
def bars(n):
    g = df.groupby(['d', (df.index.hour * 60 + df.index.minute - 555) // n])
    b = g.agg(o=('Open', 'first'), h=('High', 'max'), l=('Low', 'min'), c=('Close', 'last'), n=('Close', 'size'))
    b['ema20'] = b.c.ewm(span=20, adjust=False).mean(); return b
b5, b15 = bars(5), bars(15)
days = [d for d in daily.index if not np.isnan(daily.loc[d, 'bias'])]
def grid(d, x):
    idx = pd.date_range(pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=15), periods=375, freq='1min')
    y = x[['Open','High','Low','Close']].reindex(idx)
    c = y.Close.ffill().bfill()
    for k in ['Open','High','Low','Close']: y[k] = y[k].fillna(c)
    return y
G = {d: grid(d, x) for d, x in df.groupby('d')}
# validation against an independent daily index file
try:
    ref_o = pd.read_parquet(f'{OUT}/idx_Open.parquet')['nifty 50'].dropna(); ref_c = pd.read_parquet(f'{OUT}/idx_Close.parquet')['nifty 50'].dropna()
    dd = daily.copy(); dd.index = pd.to_datetime(dd.index); j = dd.join(pd.DataFrame({'ro': ref_o, 'rc': ref_c}), how='inner')
    print('validation vs independent daily file: days', len(j), '| median abs close diff %', round(((j.c / j.rc - 1).abs().median()) * 100, 3), '| median abs open diff %', round(((j.o / j.ro - 1).abs().median()) * 100, 3))
    print('independent file: mean open->close %', round((j.rc / j.ro - 1).mean() * 100, 3), '| mean overnight %', round((j.ro / j.rc.shift(1) - 1).mean() * 100, 3), '| 1-min file open->close %', round((j.c / j.o - 1).mean() * 100, 3))
except Exception as e: print('validation skipped', e)

def exit_scan(hi, lo, cl, i0, side, stop, tgt, last):
    """walk 1-min bars after entry; stop checked before target inside a bar."""
    for i in range(i0, last + 1):
        if side > 0:
            if lo[i] <= stop: return stop, i, 'stop'
            if tgt is not None and hi[i] >= tgt: return tgt, i, 'target'
        else:
            if hi[i] >= stop: return stop, i, 'stop'
            if tgt is not None and lo[i] <= tgt: return tgt, i, 'target'
    return cl[last], last, 'eod'

def orb(d, x, n=15, use_bias=False, stop_mid=False):
    hi, lo, cl = x.High.values, x.Low.values, x.Close.values
    rh, rl = hi[:n].max(), lo[:n].min(); last = 360          # exit by 15:15
    out = []
    for i in range(n, 316):                                   # entries until 14:30
        up, dn = hi[i] > rh, lo[i] < rl
        if up and dn: return out
        if up or dn:
            side = 1 if up else -1
            if use_bias and side != daily.loc[d, 'bias']: return out
            entry = rh if up else rl
            stop = ((rh + rl) / 2) if stop_mid else (rl if up else rh)
            px, j, why = exit_scan(hi, lo, cl, i + 1, side, stop, None, last)
            out.append(side * (px / entry - 1) - RT); return out
    return out

def mtf(d, x, rmult=2.0, use_daily=True, use_15=True):
    hi, lo, cl = x.High.values, x.Low.values, x.Close.values
    f5 = b5.loc[d]; f15 = b15.loc[d]; out = []; busy_until = -1; last = 360
    bias = daily.loc[d, 'bias']
    for k in range(7, 63):                                    # 5m bars ending 09:50 .. 14:30
        if len(out) >= 2: break
        i_close = (k + 1) * 5 - 1                             # index of the 1-min bar that completes 5m bar k
        if i_close <= busy_until or k not in f5.index or (k - 1) not in f5.index: continue
        k15 = (i_close + 1) // 15 - 1                         # last completed 15m bar
        if k15 < 1 or k15 not in f15.index: continue
        sess_mid = (hi[:i_close + 1].max() + lo[:i_close + 1].min()) / 2
        c15, e15 = f15.c[k15], f15.ema20[k15]
        for side in (1, -1):
            if use_daily and side != bias: continue
            if use_15 and not ((c15 > e15 and cl[i_close] > sess_mid) if side > 0 else (c15 < e15 and cl[i_close] < sess_mid)): continue
            prev, cur = f5.loc[k - 1], f5.loc[k]
            if side > 0: ok = (prev.l <= prev.ema20) and (cur.c > prev.h) and (cur.c > cur.ema20)
            else:        ok = (prev.h >= prev.ema20) and (cur.c < prev.l) and (cur.c < cur.ema20)
            if not ok: continue
            entry = cur.c
            stop = min(prev.l, cur.l) if side > 0 else max(prev.h, cur.h)
            risk = abs(entry - stop)
            if risk < 0.0008 * entry or risk > 0.006 * entry: continue
            tgt = entry + side * rmult * risk
            px, j, why = exit_scan(hi, lo, cl, i_close + 1, side, stop, tgt, last)
            out.append(side * (px / entry - 1) - RT); busy_until = j; break
    return out

def mom(d, x, mode):
    cl, op = x.Close.values, x.Open.values; pc = daily.loc[d, 'pc']
    if mode == 'first30_last30':
        s = np.sign(cl[29] / pc - 1); return [s * (cl[374] / cl[344] - 1) - RT] if s != 0 else []
    if mode == 'first30_rest':
        s = np.sign(cl[29] / pc - 1); return [s * (cl[360] / cl[29] - 1) - RT] if s != 0 else []
    if mode == 'gap_fade':
        g = op[0] / pc - 1
        return [-np.sign(g) * (cl[60] / op[0] - 1) - RT] if abs(g) > 0.003 else []
    if mode == 'long_open_close':
        return [cl[360] / op[0] - 1 - RT]

def report(name, fn):
    rows = []
    for d in days:
        x = G[d]
        for r in fn(d, x): rows.append((d, r))
    t = pd.DataFrame(rows, columns=['d', 'r']); t['d'] = pd.to_datetime(t.d)
    res = {}
    for nm, a, b in [('full', '2017', '2026-12-31'), ('IS 2017-21', '2017', '2021-12-31'), ('OOS 2022-26', '2022', '2026-12-31')]:
        tt = t[(t.d >= a) & (t.d <= b)]
        if len(tt) < 5: res[nm] = None; continue
        dp = tt.groupby('d').r.sum(); alld = pd.DatetimeIndex([pd.Timestamp(q) for q in days]); alld = alld[(alld >= a) & (alld <= b)]
        dp = dp.reindex(alld).fillna(0); eq = (1 + dp).cumprod()
        w, l = tt.r[tt.r > 0], tt.r[tt.r <= 0]
        res[nm] = dict(trades=int(len(tt)), win_pct=round((tt.r > 0).mean() * 100, 1), avg_trade_pct=round(tt.r.mean() * 100, 3),
                       gross_avg_pct=round((tt.r.mean() + RT) * 100, 3), pf=round(w.sum() / -l.sum(), 2),
                       ann_ret_pct=round(dp.mean() * 252 * 100, 1), sharpe=round(dp.mean() / dp.std() * np.sqrt(252), 2), maxdd_pct=round((eq / eq.cummax() - 1).min() * 100, 1))
    f = lambda v: 'n/a' if v is None else f"n={v['trades']:5d} win {v['win_pct']:4.1f}% net/trade {v['avg_trade_pct']:6.3f}% (gross {v['gross_avg_pct']:6.3f}%) PF {v['pf']:4.2f} ann {v['ann_ret_pct']:5.1f}% Sh {v['sharpe']:5.2f} DD {v['maxdd_pct']:6.1f}%"
    print(f'{name:44s}\n     IS  2017-21: {f(res["IS 2017-21"])}\n     OOS 2022-26: {f(res["OOS 2022-26"])}')
    return res

print(f'\nIntraday tests on the Nifty 50 index, 1x notional, round-trip cost {RT*100:.2f}%')
R = {}
R['hold open to 15:15 every day (baseline)'] = report('BASE long open->15:15 every day', lambda d, x: mom(d, x, 'long_open_close'))
R['ORB 15m'] = report('ORB 15-min range breakout, stop other side', lambda d, x: orb(d, x, 15))
R['ORB 30m'] = report('ORB 30-min range breakout, stop other side', lambda d, x: orb(d, x, 30))
R['ORB 15m + daily trend'] = report('ORB 15-min + daily trend filter', lambda d, x: orb(d, x, 15, use_bias=True))
R['ORB 30m + daily trend, stop mid'] = report('ORB 30-min + daily trend, stop at mid', lambda d, x: orb(d, x, 30, use_bias=True, stop_mid=True))
R['MTF daily+15m+5m pullback 2R'] = report('MULTI-TF daily bias + 15m trend + 5m pullback, 2R', lambda d, x: mtf(d, x))
R['MTF 15m+5m only 2R'] = report('MULTI-TF 15m trend + 5m pullback (no daily), 2R', lambda d, x: mtf(d, x, use_daily=False))
R['5m pullback only 2R'] = report('5m pullback candle only (no higher timeframe)', lambda d, x: mtf(d, x, use_daily=False, use_15=False))
R['MTF 3R'] = report('MULTI-TF daily + 15m + 5m pullback, 3R', lambda d, x: mtf(d, x, rmult=3.0))
R['first30->last30 momentum'] = report('Intraday momentum: first 30m sign -> last 30m', lambda d, x: mom(d, x, 'first30_last30'))
R['first30->rest momentum'] = report('Intraday momentum: first 30m sign -> rest of day', lambda d, x: mom(d, x, 'first30_rest'))
R['gap fade first hour'] = report('Gap fade (gap > 0.3%), first hour', lambda d, x: mom(d, x, 'gap_fade'))
json.dump(R, open(f'{OUT}/intra_{TAG}.json', 'w'), indent=1)
