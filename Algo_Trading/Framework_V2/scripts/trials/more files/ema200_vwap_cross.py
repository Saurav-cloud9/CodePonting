"""
Cross-tabulate EMA200 vs VWAP context at touch bar.
Shows PF for each combination: (above/below EMA200) x (above/below VWAP)
Runs both baseline (all touch types) and v1 (wick-only) for comparison.
"""
import pandas as pd, glob, os, sys

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'

SL_MULT  = 2.5
TP_MULT = 4.5
EOD_HOUR = 15

def compute_indicators(df):
    df = df.copy()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['tp']     = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap']    = df['cum_tpv'] / df['cum_vol']
    return df

def run(df, v1=True):
    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['ema200']):
            i += 1; continue

        touch_base = row['low'] <= row['ma20'] and row['hour'] < EOD_HOUR
        if v1:
            touch_cond = touch_base and row['open'] > row['ma20'] and row['close'] > row['ma20']
        else:
            touch_cond = touch_base

        if touch_cond:

            touch_date  = row['date']
            atr         = row['atr14']
            vwap_above  = row['close'] >= row['vwap']
            ema_above   = row['close'] >= row['ema200']

            # find bounce bar
            bounce_idx = None
            for j in range(i, i + 4):
                if j >= len(df): break
                b = df.iloc[j]
                if b['date'] != touch_date or b['hour'] >= EOD_HOUR: break
                if b['close'] > b['ma20']: bounce_idx = j; break
            if bounce_idx is None: i += 1; continue

            entry_idx = bounce_idx + 1
            if entry_idx >= len(df) or df.iloc[entry_idx]['date'] != touch_date:
                i += 1; continue

            entry = df.iloc[entry_idx]['open']
            sl    = entry - SL_MULT * atr
            tp   = entry + TP_MULT * atr
            pnl   = None; outcome = None

            for k in range(entry_idx, len(df)):
                b = df.iloc[k]
                if b['hour'] >= EOD_HOUR:
                    pnl = b['open'] - entry
                    outcome = 'EOD+' if pnl > 0 else 'EOD-'
                    break
                if b['high'] >= tp: pnl = tp - entry;  outcome = 'W'; break
                if b['low']  <= sl:  pnl = sl  - entry;  outcome = 'L'; break

            if pnl is not None:
                trades.append({
                    'pnl':        pnl,
                    'outcome':    outcome,
                    'vwap_above': vwap_above,
                    'ema_above':  ema_above,
                })
            i = k + 1
        else:
            i += 1
    return trades

base_trades, v1_trades = [], []
for csv_path in sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv'))):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','volume','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = compute_indicators(df)
    base_trades.extend(run(df, v1=False))
    v1_trades.extend(run(df, v1=True))

base_tdf = pd.DataFrame(base_trades)
tdf      = pd.DataFrame(v1_trades)

def pf(grp):
    gp = grp[grp['pnl'] > 0]['pnl'].sum()
    gl = abs(grp[grp['pnl'] < 0]['pnl'].sum())
    return gp / gl if gl > 0 else 999.0

def show(label, grp):
    n  = len(grp)
    oc = grp['outcome'].value_counts()
    print(f"  {label:<30} N={n:>6}  PF={pf(grp):.3f}  "
          f"W={oc.get('W',0):>4}  L={oc.get('L',0):>4}  "
          f"E+={oc.get('EOD+',0):>4}  E-={oc.get('EOD-',0):>4}")

def print_table(title, df):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    groups = {
        'Above EMA200 + Above VWAP': df[ df['ema_above'] &  df['vwap_above']],
        'Above EMA200 + Below VWAP': df[ df['ema_above'] & ~df['vwap_above']],
        'Below EMA200 + Above VWAP': df[~df['ema_above'] &  df['vwap_above']],
        'Below EMA200 + Below VWAP': df[~df['ema_above'] & ~df['vwap_above']],
        'Above EMA200 (all)'       : df[ df['ema_above']],
        'Below EMA200 (all)'       : df[~df['ema_above']],
        'Above VWAP (all)'         : df[ df['vwap_above']],
        'Below VWAP (all)'         : df[~df['vwap_above']],
        'ALL'                      : df,
    }
    for label, grp in groups.items():
        show(label, grp)

print_table("Baseline — all touch types, 30 stocks 2022-2025", base_tdf)
print_table("v1 — wick-only touch, 30 stocks 2022-2025", tdf)
