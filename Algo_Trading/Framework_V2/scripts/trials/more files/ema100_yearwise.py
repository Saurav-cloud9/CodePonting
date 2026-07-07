"""
Year-wise PF breakdown for v1 + Below EMA100 + Above VWAP (the 1.039 combo).
"""
import pandas as pd, glob, os

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT  = 2.5
TGT_MULT = 4.5
EOD_HOUR = 15

def compute_indicators(df):
    df = df.copy()
    df['ema100'] = df['close'].ewm(span=100, adjust=False).mean()
    df['tp']      = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap']    = df['cum_tpv'] / df['cum_vol']
    return df

def run(df):
    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['ema100']):
            i += 1; continue

        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20'] and row['hour'] < EOD_HOUR):

            touch_date  = row['date']
            atr         = row['atr14']
            year        = pd.Timestamp(touch_date).year
            ema_below   = row['close'] < row['ema100']
            vwap_above  = row['close'] >= row['vwap']

            entry_idx = i + 1
            if entry_idx >= len(df) or df.iloc[entry_idx]['date'] != touch_date:
                i += 1; continue

            entry = df.iloc[entry_idx]['open']
            sl    = entry - SL_MULT * atr
            tgt   = entry + TGT_MULT * atr
            pnl   = None; outcome = None

            for k in range(entry_idx, len(df)):
                b = df.iloc[k]
                if b['hour'] >= EOD_HOUR:
                    pnl = b['open'] - entry; outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                if b['high'] >= tgt: pnl = tgt - entry; outcome = 'W'; break
                if b['low']  <= sl:  pnl = sl  - entry; outcome = 'L'; break

            if pnl is not None:
                trades.append({'pnl': pnl, 'outcome': outcome, 'year': year,
                               'ema_below': ema_below, 'vwap_above': vwap_above})
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
    df = compute_indicators(df)
    all_trades.extend(run(df))

tdf = pd.DataFrame(all_trades)

def show(label, grp):
    n  = len(grp)
    gp = grp[grp['pnl'] > 0]['pnl'].sum()
    gl = abs(grp[grp['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 999.0
    oc = grp['outcome'].value_counts()
    wr = (grp['outcome'] == 'W').sum() / n * 100
    print(f"  {label:<8} N={n:>5}  PF={pf:.3f}  WR={wr:4.1f}%  "
          f"W={oc.get('W',0):>4}  L={oc.get('L',0):>4}  "
          f"E+={oc.get('EOD+',0):>4}  E-={oc.get('EOD-',0):>4}")

# post-hoc filter — same logic as sweep
filtered = tdf[tdf['ema_below'] & tdf['vwap_above']]

print(f"\n{'='*70}")
print("  v1 + Below EMA100 + Above VWAP — year-wise (post-hoc filter)")
print(f"{'='*70}")
for yr in sorted(filtered['year'].unique()):
    show(str(yr), filtered[filtered['year'] == yr])
print(f"  {'-'*65}")
show('ALL', filtered)
