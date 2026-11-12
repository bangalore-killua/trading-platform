import sys, os, glob
import numpy as np, pandas as pd
src, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(src, 'daily', '*.csv')))
idx_names = set()
frames = {}
START = '2003-01-01'
n_bad = 0
for f in files:
    name = os.path.basename(f)[:-4]
    try:
        df = pd.read_csv(f, usecols=['Date','Open','High','Low','Close','Volume','DLV_QTY'], parse_dates=['Date'])
    except Exception:
        try:
            df = pd.read_csv(f, usecols=['Date','Open','High','Low','Close','Volume'], parse_dates=['Date'])
            df['DLV_QTY'] = np.nan
        except Exception as e:
            n_bad += 1; continue
    df = df.dropna(subset=['Date','Close']).drop_duplicates('Date').set_index('Date').sort_index()
    df = df[df.index >= START]
    if len(df) < 300: continue
    frames[name] = df
print('loaded', len(frames), 'bad', n_bad)
is_index = [n for n in frames if n.startswith('nifty') or n == 'india vix']
print('index-like files:', len(is_index))
stocks = [n for n in frames if n not in is_index]
dates = pd.DatetimeIndex(sorted(set().union(*[frames[n].index for n in ['reliance','infy','sbin']])))
print('dates', dates[0], dates[-1], len(dates))
def panel(col, names):
    return pd.DataFrame({n: frames[n][col].reindex(dates) for n in names}).astype('float32')
for col in ['Open','High','Low','Close','Volume','DLV_QTY']:
    panel(col, stocks).to_parquet(os.path.join(out, f'stk_{col}.parquet'))
for col in ['Open','High','Low','Close']:
    panel(col, is_index).to_parquet(os.path.join(out, f'idx_{col}.parquet'))
print('stocks', len(stocks))
