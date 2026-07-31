"""
EMA sweep built on top of v1 + Above VWAP.
Filter-at-entry (realistic). Finds top 3 combos by PF, prints year-wise for each.
"""
import pandas as pd, glob, os

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SL_MULT  = 2.5
TP_MULT = 4.5
EOD_HOUR = 15
EMA_SPANS = [50, 100, 150, 200, 250]

def compute_indicators(df):
    df = df.copy()
    for s in EMA_SPANS:
        df[f'ema{s}'] = df['close'].ewm(span=s, adjust=False).mean()
    df['tp']      = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap']    = df['cum_tpv'] / df['cum_vol']
    return df

def run(df, ema_span, ema_above_filter):
    trades = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row[f'ema{ema_span}']):
            i += 1; continue

        vwap_ok = row['close'] >= row['vwap']
        ema_ok  = (row['close'] >= row[f'ema{ema_span}']) == ema_above_filter

        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20'] and row['hour'] < EOD_HOUR
                and vwap_ok and ema_ok):

            touch_date = row['date']
            atr        = row['atr14']
            year       = pd.Timestamp(touch_date).year

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
                trades.append({'pnl': pnl, 'outcome': outcome, 'year': year})
            i = k + 1
        else:
            i += 1
    return trades

# collect all combos
combos = {}
for s in EMA_SPANS:
    for above in [True, False]:
        label = f"EMA{s} {'above' if above else 'below'}"
        combos[label] = {'span': s, 'above': above, 'trades': []}

dfs = []
for csv_path in sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv'))):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','volume','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = compute_indicators(df)
    for label, cfg in combos.items():
        combos[label]['trades'].extend(run(df, cfg['span'], cfg['above']))

def pf_of(trades):
    tdf = pd.DataFrame(trades)
    gp  = tdf[tdf['pnl'] > 0]['pnl'].sum()
    gl  = abs(tdf[tdf['pnl'] < 0]['pnl'].sum())
    return gp / gl if gl > 0 else 999.0

# rank by PF, pick top 3
ranked = sorted(combos.items(), key=lambda x: pf_of(x[1]['trades']), reverse=True)[:3]

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

for label, cfg in ranked:
    tdf = pd.DataFrame(cfg['trades'])
    overall_pf = pf_of(cfg['trades'])
    print(f"\n{'='*70}")
    print(f"  v1 + Above VWAP + {label}  |  Overall PF={overall_pf:.3f}  N={len(tdf):,}")
    print(f"{'='*70}")
    for yr in sorted(tdf['year'].unique()):
        show(str(yr), tdf[tdf['year'] == yr])
    print(f"  {'-'*65}")
    show('ALL', tdf)
