"""
Iteration #6 — MACD state sweep on v2
At each touch bar: classify MACD vs Signal and vs zero line.
States: A (MACD>Sig, >0)  B (MACD>Sig, <0)  C (MACD<Sig, >0)  D (MACD<Sig, <0)
"""
import sys, pandas as pd, glob
sys.path.insert(0, 'Algo_Trading/Framework_V2/core')
from ma_baseline_v1_1 import MABaselineV1_1

CSV_DIR = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
files   = sorted(glob.glob(f'{CSV_DIR}/*.csv'))
strat   = MABaselineV1_1()
EMA_COL = f'ema{strat.EMA_SPAN}'

def prepare(df):
    df = MABaselineV1_1.prepare(df)
    df['ema12']   = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26']   = df['close'].ewm(span=26, adjust=False).mean()
    df['macd']    = df['ema12'] - df['ema26']
    df['signal9'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df

def macd_state(macd_val, signal_val):
    above_signal = macd_val > signal_val
    above_zero   = macd_val > 0
    if above_signal and above_zero:   return 'A'
    if above_signal and not above_zero: return 'B'
    if not above_signal and above_zero: return 'C'
    return 'D'

all_trades = []

for f in files:
    df = pd.read_csv(f, low_memory=False)
    df.columns = df.columns.str.strip()
    for col in ['open','high','low','close','volume','ma20','atr14']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = prepare(df)

    i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row[EMA_COL]) or pd.isna(row['signal9']):
            i += 1; continue
        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20']
                and row['close'] >= row['vwap']
                and row['close'] < row[EMA_COL]):
            if row['hour'] >= strat.EOD_HOUR: i += 1; continue
            state      = macd_state(row['macd'], row['signal9'])
            touch_date = row['date']
            atr        = row['atr14']
            entry_idx  = i + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']
            sl    = entry - strat.SL_MULT  * atr
            tp   = entry + strat.TP_MULT * atr
            for k in range(entry_idx, len(df)):
                k_bar = df.iloc[k]
                if k_bar['hour'] >= strat.EOD_HOUR:
                    pnl = k_bar['open'] - entry; break
                if k_bar['high'] >= tp:
                    pnl = tp - entry; break
                if k_bar['low'] <= sl:
                    pnl = sl - entry; break
            all_trades.append({
                'pnl':   pnl,
                'state': state,
                'year':  entry_bar['datetime'].year,
                'macd':  row['macd'],
                'sig':   row['signal9'],
            })
            i = k + 1
        else:
            i += 1

tdf = pd.DataFrame(all_trades)

# ── Overall by state ──────────────────────────────────────────
print('== Overall (30 stocks, 2022-2025) ==========================')
print(f"{'State':<7} {'N':>5}  {'PF':>7}  {'WR%':>6}  {'Description'}")
print('-' * 60)
descs = {'A':'MACD>Sig, above 0', 'B':'MACD>Sig, below 0',
         'C':'MACD<Sig, above 0', 'D':'MACD<Sig, below 0'}
for state in ['A','B','C','D']:
    g = tdf[tdf.state == state]
    if len(g) == 0: continue
    gp = g[g.pnl>0].pnl.sum(); gl = g[g.pnl<0].pnl.abs().sum()
    wr = (g.pnl>0).mean()*100
    pf = gp/gl if gl>0 else float('inf')
    print(f"  {state}    {len(g):>5}  {pf:>7.3f}  {wr:>5.1f}%  {descs[state]}")

gp = tdf[tdf.pnl>0].pnl.sum(); gl = tdf[tdf.pnl<0].pnl.abs().sum()
print('-' * 60)
print(f"  ALL  {len(tdf):>5}  {gp/gl:>7.3f}  {(tdf.pnl>0).mean()*100:>5.1f}%  v2 baseline")

# ── Year-wise by state ────────────────────────────────────────
print()
print('== Year-wise PF by state ====================================')
print(f"{'State':<7} {'2022':>7} {'2023':>7} {'2024':>7} {'2025':>7}  {'N':>5}")
print('-' * 50)
for state in ['A','B','C','D']:
    g = tdf[tdf.state == state]
    row_str = f'  {state}    '
    for yr in [2022,2023,2024,2025]:
        gy = g[g.year==yr]
        if len(gy) < 10:
            row_str += f"{'  —':>7}"
        else:
            gp = gy[gy.pnl>0].pnl.sum(); gl = gy[gy.pnl<0].pnl.abs().sum()
            row_str += f"{gp/gl:>7.3f}" if gl>0 else f"{'  inf':>7}"
    row_str += f"  {len(g):>5}"
    print(row_str)
