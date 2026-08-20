"""
CBQ (Charge Break-even Qty) — Iteration #5 (v1.1)
v1.1 = v1 + Above VWAP + Below EMA100 | SL=2.5x, TP=4.5x | 30 stocks 2022-2025
Finds the quantity at which NPF crosses 1.0 after full Kotak Neo charges.
"""
import sys, io, glob, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'Algo_Trading/Framework_V2/core')
from ma_baseline_v1_1 import MABaselineV1_1

CSV_DIR = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min'
ATR_LEN = 14; MA_LEN = 20

def load(f):
    df = pd.read_csv(f, low_memory=False); df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime']).apply(
        lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values('datetime').reset_index(drop=True)
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['ma20'] = df['close'].rolling(MA_LEN).mean()
    prev_c = df['close'].shift(1)
    tr = pd.concat([df['high']-df['low'],
                    (df['high']-prev_c).abs(),
                    (df['low']-prev_c).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()
    df = df.dropna(subset=['ma20','atr14']).reset_index(drop=True)
    return MABaselineV1_1.prepare(df)

def npf_at_qty(trades, qty):
    net_trades = []; total_charge = 0
    for t in trades:
        entry = t['entry']; exit_ = t['exit']; raw = t['pnl'] * qty
        brok  = min((entry + exit_) * qty * 0.0005, 40)
        stt   = exit_ * qty * 0.00025
        txn   = (entry + exit_) * qty * 0.0000297
        sebi  = (entry + exit_) * qty * 0.000001
        stamp = entry * qty * 0.00003
        gst   = 0.18 * (brok + txn)
        charge = brok + stt + txn + sebi + stamp + gst
        total_charge += charge
        net_trades.append(raw - charge)
    w = sum(x for x in net_trades if x > 0)
    l = sum(-x for x in net_trades if x < 0)
    return (w/l if l > 0 else 0), sum(net_trades), total_charge/len(trades) if trades else 0

# ── Main ─────────────────────────────────────────────────────────────────────
files = sorted(glob.glob(f'{CSV_DIR}/*.csv'))
print(f'Loading {len(files)} stocks...')
strategy = MABaselineV1_1()
all_trades = []

for f in files:
    df = load(f)
    raw = strategy.run(df)
    # attach entry/exit prices for charge calc
    i = 0
    while i < len(df) - 1:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue
        ema_col = f'ema{strategy.EMA_SPAN}'
        if (row['low'] <= row['ma20'] and row['open'] > row['ma20']
                and row['close'] > row['ma20']
                and row['close'] >= row['vwap']
                and row['close'] < row[ema_col]
                and row['hour'] < strategy.EOD_HOUR):
            touch_date = row['date']; atr = row['atr14']
            ei = i + 1
            if ei >= len(df) or df.iloc[ei]['date'] != touch_date: i += 1; continue
            entry = df.iloc[ei]['open']
            sl  = entry - strategy.SL_MULT  * atr
            tp = entry + strategy.TP_MULT * atr
            for k in range(ei, len(df)):
                kb = df.iloc[k]
                if kb['hour'] >= strategy.EOD_HOUR:
                    exit_px = kb['open']; pnl = exit_px - entry; break
                if kb['high'] >= tp:
                    exit_px = tp; pnl = tp - entry; break
                if kb['low']  <= sl:
                    exit_px = sl;  pnl = sl  - entry; break
            all_trades.append({'pnl': pnl, 'entry': entry, 'exit': exit_px,
                                'year': df.iloc[ei]['datetime'].year})
            i = k + 1
        else:
            i += 1

print(f'Total trades: {len(all_trades)}')
raw_w = sum(t['pnl'] for t in all_trades if t['pnl'] > 0)
raw_l = sum(-t['pnl'] for t in all_trades if t['pnl'] < 0)
print(f'Raw PF: {raw_w/raw_l:.3f}  (SL={strategy.SL_MULT}x, TP={strategy.TP_MULT}x)')
print()

QTY_LIST = [1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000]
print(f"{'Qty':>6}  {'NPF':>6}  {'Net PnL':>10}  {'Avg charge':>11}")
print('-'*45)
crossed = False
for qty in QTY_LIST:
    npf_val, net_pnl, avg_c = npf_at_qty(all_trades, qty)
    marker = '  <-- NPF > 1.0' if npf_val >= 1.0 and not crossed else ''
    if npf_val >= 1.0: crossed = True
    print(f'{qty:>6}  {npf_val:>6.3f}  {net_pnl:>10.0f}  {avg_c:>11.2f}{marker}')

print()
print('Year-wise at qty=1:')
for yr in [2022, 2023, 2024, 2025]:
    g = [t for t in all_trades if t['year'] == yr]
    if not g: continue
    npf_val, net_pnl, avg_c = npf_at_qty(g, 1)
    gw = sum(t['pnl'] for t in g if t['pnl'] > 0)
    gl = sum(-t['pnl'] for t in g if t['pnl'] < 0)
    print(f'  {yr}  N={len(g)}  Raw PF={gw/gl:.3f}  NPF={npf_val:.3f}  Net PnL={net_pnl:.0f}')
