"""
EMA sweep across multiple lengths — all 4 combos with VWAP on v1 touches.
Output: PF and N for each (EMA length x VWAP context) combination.
"""
import pandas as pd, glob, os

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT  = 2.5
TP_MULT = 4.5
EOD_HOUR = 15
EMA_SPANS = [50, 100, 150, 200, 250]

def compute_indicators(df, spans):
    df = df.copy()
    for s in spans:
        df[f'ema{s}'] = df['close'].ewm(span=s, adjust=False).mean()
    df['tp']      = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap']    = df['cum_tpv'] / df['cum_vol']
    return df

def run(df, spans):
    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue
        if any(pd.isna(row[f'ema{s}']) for s in spans): i += 1; continue

        # v1 touch
        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20'] and row['hour'] < EOD_HOUR):

            touch_date = row['date']
            atr        = row['atr14']
            vwap_above = row['close'] >= row['vwap']
            ema_above  = {s: row['close'] >= row[f'ema{s}'] for s in spans}

            entry_idx = i + 1
            if entry_idx >= len(df) or df.iloc[entry_idx]['date'] != touch_date:
                i += 1; continue

            entry = df.iloc[entry_idx]['open']
            sl    = entry - SL_MULT * atr
            tp   = entry + TP_MULT * atr
            pnl   = None; outcome = None

            for k in range(entry_idx, len(df)):
                b = df.iloc[k]
                if b['hour'] >= EOD_HOUR:
                    pnl = b['open'] - entry; outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                if b['high'] >= tp: pnl = tp - entry; outcome = 'W'; break
                if b['low']  <= sl:  pnl = sl  - entry; outcome = 'L'; break

            if pnl is not None:
                trades.append({
                    'pnl': pnl, 'outcome': outcome,
                    'vwap_above': vwap_above, **{f'ema{s}_above': ema_above[s] for s in spans}
                })
            i = k + 1
        else:
            i += 1
    return trades

all_trades = []
for csv_path in sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv'))):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','volume','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = compute_indicators(df, EMA_SPANS)
    all_trades.extend(run(df, EMA_SPANS))

tdf = pd.DataFrame(all_trades)

def pf_n(grp):
    n  = len(grp)
    gp = grp[grp['pnl'] > 0]['pnl'].sum()
    gl = abs(grp[grp['pnl'] < 0]['pnl'].sum())
    p  = gp / gl if gl > 0 else 999.0
    return p, n

def cell(grp):
    p, n = pf_n(grp)
    return f"{p:.3f} (N={n:,})"

combos = [
    ('Above EMA + Above VWAP', lambda d, s:  d[f'ema{s}_above'] &  d['vwap_above']),
    ('Above EMA + Below VWAP', lambda d, s:  d[f'ema{s}_above'] & ~d['vwap_above']),
    ('Below EMA + Above VWAP', lambda d, s: ~d[f'ema{s}_above'] &  d['vwap_above']),
    ('Below EMA + Below VWAP', lambda d, s: ~d[f'ema{s}_above'] & ~d['vwap_above']),
]

col_w = 22
print(f"\n{'EMA':<8}", end='')
for label, _ in combos:
    print(f"  {label:<{col_w}}", end='')
print()
print('-' * (8 + (col_w + 2) * len(combos)))

for s in EMA_SPANS:
    print(f"  EMA{s:<4}", end='')
    for _, mask_fn in combos:
        grp = tdf[mask_fn(tdf, s)]
        print(f"  {cell(grp):<{col_w}}", end='')
    print()

# EMA-only marginals (no VWAP filter)
print(f"\n{'EMA':<8}  {'Below EMA (no VWAP)':<26}  {'Above EMA (no VWAP)':<26}")
print('-' * 65)
for s in EMA_SPANS:
    below = tdf[~tdf[f'ema{s}_above']]
    above = tdf[ tdf[f'ema{s}_above']]
    print(f"  EMA{s:<4}  {cell(below):<26}  {cell(above):<26}")
