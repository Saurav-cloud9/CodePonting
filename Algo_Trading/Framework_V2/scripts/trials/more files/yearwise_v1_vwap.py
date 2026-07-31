"""
Year-wise breakdown for iteration #2 (v1) and #3 (v1 + Above VWAP).
Filter applied at entry — realistic simulation.
"""
import pandas as pd, glob, os

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT  = 2.5
TP_MULT = 4.5
EOD_HOUR = 15

def compute_vwap(df):
    df = df.copy()
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
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue

        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20'] and row['hour'] < EOD_HOUR):

            touch_date = row['date']
            atr        = row['atr14']
            year       = pd.Timestamp(touch_date).year
            vwap_above = row['close'] >= row['vwap']

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
                trades.append({'pnl': pnl, 'outcome': outcome,
                               'year': year, 'vwap_above': vwap_above})
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
    df = compute_vwap(df)
    all_trades.extend(run(df))

tdf = pd.DataFrame(all_trades)

def show(label, grp):
    n  = len(grp)
    gp = grp[grp['pnl'] > 0]['pnl'].sum()
    gl = abs(grp[grp['pnl'] < 0]['pnl'].sum())
    pf = gp / gl if gl > 0 else 999.0
    oc = grp['outcome'].value_counts()
    wr = (grp['outcome'] == 'W').sum() / n * 100
    print(f"  {label:<8} N={n:>6}  PF={pf:.3f}  WR={wr:4.1f}%  "
          f"W={oc.get('W',0):>4}  L={oc.get('L',0):>4}  "
          f"E+={oc.get('EOD+',0):>4}  E-={oc.get('EOD-',0):>4}")

def print_table(title, df):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    for yr in sorted(df['year'].unique()):
        show(str(yr), df[df['year'] == yr])
    print(f"  {'-'*65}")
    show('ALL', df)

print_table("#2 — v1 (wick-only, no filter)", tdf)
print_table("#3 — v1 + Above VWAP", tdf[tdf['vwap_above']])
