import pandas as pd, numpy as np, os, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
BASE_SL=2.5; BASE_TP=4.5; MAX_TB_GAP=3; EOD_HOUR=15

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    return 100 - (100 / (1 + gain/loss))

def run_backtest_excursions(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open','high','low','close','ma20','atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    trades = []; i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']): i += 1; continue
        if row['low'] <= row['ma20']:
            if row['hour'] >= EOD_HOUR: i += 1; continue
            touch_date = row['date']; atr = row['atr14']; bounce_bar = None
            for j in range(i, i + MAX_TB_GAP + 1):
                b = df.iloc[j]
                if b['date'] != touch_date: break
                if b['hour'] >= EOD_HOUR: break
                if b['close'] > b['ma20']: bounce_bar = b; break
            if bounce_bar is None: i += 1; continue
            entry_idx = j + 1
            if entry_idx >= len(df): i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date: i += 1; continue
            entry = entry_bar['open']

            # collect ALL bars until EOD (no SL/TP stop — needed for grid scan)
            bars = []
            k = entry_idx
            while k < len(df):
                kb = df.iloc[k]
                if kb['hour'] >= EOD_HOUR:
                    bars.append({'h': None, 'l': None,
                                 'eod_open': (kb['open'] - entry) / atr})
                    k += 1; break
                bars.append({'h': (kb['high'] - entry) / atr,
                             'l': (kb['low']  - entry) / atr,
                             'eod_open': None})
                k += 1

            # advance i using BASE_SL/TP so position guarding is consistent
            k2 = entry_idx
            while k2 < len(df):
                kb = df.iloc[k2]
                if kb['hour'] >= EOD_HOUR: k2 += 1; break
                if kb['high'] >= entry + BASE_TP*atr or kb['low'] <= entry - BASE_SL*atr:
                    k2 += 1; break
                k2 += 1

            trades.append({'atr': atr, 'entry': entry, 'bars': bars})
            i = k2
        else:
            i += 1
    return trades

# ── collect all trade excursions ──────────────────────────────
print('Running backtest (one pass)...')
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for csv_path in csv_files:
    all_trades.extend(run_backtest_excursions(csv_path))
print(f'Trades collected: {len(all_trades)}')

# ── evaluate outcome for any (sl, tp) ───────────────────────
def evaluate(trades, sl, tp):
    pnls = []
    for t in trades:
        for bar in t['bars']:
            if bar['eod_open'] is not None:
                pnls.append(bar['eod_open'] * t['atr']); break
            if bar['h'] >= tp:
                pnls.append(tp * t['atr']); break
            if bar['l'] <= -sl:
                pnls.append(-sl * t['atr']); break
    arr = np.array(pnls)
    gp = arr[arr>0].sum(); gl = abs(arr[arr<0].sum())
    return gp/gl if gl>0 else 999, len(pnls)

# ── CHART 1: PnL distribution at baseline ────────────────────
print('Computing baseline PnL distribution...')
base_pnls = []
for t in all_trades:
    for bar in t['bars']:
        if bar['eod_open'] is not None:
            base_pnls.append(bar['eod_open'] * t['atr']); break
        if bar['h'] >= BASE_TP:
            base_pnls.append(BASE_TP * t['atr']); break
        if bar['l'] <= -BASE_SL:
            base_pnls.append(-BASE_SL * t['atr']); break

arr = np.array(base_pnls)
sl_line = -BASE_SL * np.median([t['atr'] for t in all_trades])
tp_line =  BASE_TP * np.median([t['atr'] for t in all_trades])

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 5))
ax.hist(arr, bins=120, color='#00aaff', alpha=0.7, edgecolor='none')
ax.axvline(0,       color='white',   linewidth=1,   linestyle=':',  label='Zero')
ax.axvline(sl_line, color='#ff4444', linewidth=1.2, linestyle='--', label=f'SL (2.5×ATR median)')
ax.axvline(tp_line,color='#00ff88', linewidth=1.2, linestyle='--', label=f'TP (4.5×ATR median)')
ax.set_title('PnL Distribution — Baseline (SL=2.5, TP=4.5) — 30 Stocks', fontsize=13)
ax.set_xlabel('Raw PnL per trade (points)'); ax.set_ylabel('Trade Count')
ax.legend(); plt.tight_layout()
out1 = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\pnl_distribution.png'
plt.savefig(out1, dpi=150); plt.close()
print(f'Saved: {out1}')

# ── CHART 2: SL x TP grid heatmap ───────────────────────────
print('Running SL x TP grid scan...')
sl_vals  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
tp_vals = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]

grid = np.zeros((len(sl_vals), len(tp_vals)))
for i, sl in enumerate(sl_vals):
    for j, tp in enumerate(tp_vals):
        pf, _ = evaluate(all_trades, sl, tp)
        grid[i, j] = round(pf, 3)
        print(f'  SL={sl} TP={tp} PF={pf:.3f}')

fig, ax = plt.subplots(figsize=(12, 6))
im = ax.imshow(grid, cmap='RdYlGn', aspect='auto', vmin=0.7, vmax=1.3, origin='lower')
plt.colorbar(im, ax=ax, label='Profit Factor')
ax.set_xticks(range(len(tp_vals))); ax.set_xticklabels(tp_vals)
ax.set_yticks(range(len(sl_vals)));  ax.set_yticklabels(sl_vals)
ax.set_xlabel('TP Multiplier'); ax.set_ylabel('SL Multiplier')
ax.set_title('PF Heatmap — SL × TP Grid (30 Stocks, 2022–2025)', fontsize=13)
for i in range(len(sl_vals)):
    for j in range(len(tp_vals)):
        ax.text(j, i, f'{grid[i,j]:.3f}', ha='center', va='center', fontsize=8,
                color='black' if 0.85 < grid[i,j] < 1.15 else 'white')
plt.tight_layout()
out2 = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports\sl_tp_heatmap.png'
plt.savefig(out2, dpi=150); plt.close()
print(f'Saved: {out2}')
