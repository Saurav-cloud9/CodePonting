"""
SL x TGT grid sweep — MA Bounce v1 (LONG) clean-touch
30 stocks · 2015-2025 · DS3 parquets (11-year full run)
Signal : single bar where low<=MA20 AND open>MA20 AND close>MA20 → long at next bar open
Logic  : single-pass (i = k+1 after each trade) — position guard intact
"""
import sys, io, glob, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
OUT_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports'
EOD_HOUR = 15

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TGT_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def load(f):
    df = pd.read_parquet(f)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].apply(lambda x: x.replace(tzinfo=None))
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['year'] = df['datetime'].dt.year
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tgt_m):
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14             = arrays['ma20'],  arrays['atr14']
    hour, date, year        = arrays['hour'],  arrays['date'], arrays['year']
    n = arrays['n']
    trades = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        # v1 clean-touch: wick touches MA, body stays above
        if (low[i] <= ma20[i] and open_[i] > ma20[i] and
                close[i] > ma20[i] and hour[i] < EOD_HOUR):
            ei = i + 1
            if ei >= n or date[ei] != date[i]:
                i += 1; continue
            entry = open_[ei]; atr = atr14[i]
            sl = entry - sl_m * atr; tgt = entry + tgt_m * atr
            k = ei
            for k in range(ei, n):
                if date[k] != date[i]:
                    pnl = close[k - 1] - entry; break
                if hour[k] >= EOD_HOUR:
                    pnl = open_[k] - entry; break
                if low[k] <= sl:
                    pnl = sl - entry; break
                if high[k] >= tgt:
                    pnl = tgt - entry; break
            trades.append({'pnl': pnl, 'year': year[ei],
                           'date': pd.Timestamp(date[ei])})
            i = k + 1
        else:
            i += 1
    return trades


def calc_pf(trades):
    if not trades: return 0.0
    w = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    l = sum(-t['pnl'] for t in trades if t['pnl'] < 0)
    return w / l if l > 0 else 0.0


def calc_sharpe(trades):
    if len(trades) < 2: return 0.0
    tdf = pd.DataFrame(trades)
    m = tdf.resample('ME', on='date')['pnl'].sum()
    return round((m.mean() / m.std()) * np.sqrt(12), 3) if m.std() > 0 else 0.0


# ── Load ───────────────────────────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks...')
stock_arrays = []
for f in files:
    df = load(f)
    stock_arrays.append({
        'high':  df['high'].values,  'low':   df['low'].values,
        'open_': df['open'].values,  'close': df['close'].values,
        'ma20':  df['ma20'].values,  'atr14': df['atr14'].values,
        'hour':  df['hour'].values,  'date':  df['date'].values,
        'year':  df['year'].values,  'n':     len(df),
    })
print(f'Loaded. Running {len(SL_VALS)} x {len(TGT_VALS)} grid sweep...')

# ── Grid sweep ─────────────────────────────────────────────────────────────────
results = {}
pf_grid = np.zeros((len(SL_VALS), len(TGT_VALS)))

for si, sl_m in enumerate(SL_VALS):
    for ti, tgt_m in enumerate(TGT_VALS):
        all_t = []
        for arr in stock_arrays:
            all_t.extend(run_combo(arr, sl_m, tgt_m))
        results[(sl_m, tgt_m)] = all_t
        pf_grid[si, ti] = calc_pf(all_t)

# ── PF grid ────────────────────────────────────────────────────────────────────
print(f'\nPF Grid (rows=SL, cols=TGT):')
print(f"{'SL\\TGT':>8}" + ''.join(f'{t:>7.1f}' for t in TGT_VALS))
for si, sl_m in enumerate(SL_VALS):
    print(f'{sl_m:>8.1f}' + ''.join(f'{pf_grid[si, ti]:>7.3f}' for ti in range(len(TGT_VALS))))

# ── Top 5 ──────────────────────────────────────────────────────────────────────
flat = sorted(
    [(pf_grid[si, ti], SL_VALS[si], TGT_VALS[ti])
     for si in range(len(SL_VALS)) for ti in range(len(TGT_VALS))],
    reverse=True
)
print(f'\nTop 5 by PF:')
print(f"  {'SL':>4}  {'TGT':>4}  {'N':>7}  {'PF':>6}  {'Sharpe':>7}")
for pf, sl_m, tgt_m in flat[:5]:
    t = results[(sl_m, tgt_m)]
    print(f"  {sl_m:>4.1f}  {tgt_m:>4.1f}  {len(t):>7,}  {pf:>6.3f}  {calc_sharpe(t):>7.3f}")

print(f'\nTop 5 by Sharpe:')
sharpe_flat = sorted(
    [(calc_sharpe(results[(SL_VALS[si], TGT_VALS[ti])]), SL_VALS[si], TGT_VALS[ti])
     for si in range(len(SL_VALS)) for ti in range(len(TGT_VALS))],
    reverse=True
)
print(f"  {'SL':>4}  {'TGT':>4}  {'N':>7}  {'PF':>6}  {'Sharpe':>7}")
for sh, sl_m, tgt_m in sharpe_flat[:5]:
    t = results[(sl_m, tgt_m)]
    pf = calc_pf(t)
    print(f"  {sl_m:>4.1f}  {tgt_m:>4.1f}  {len(t):>7,}  {pf:>6.3f}  {sh:>7.3f}")

# ── Best combo detail ──────────────────────────────────────────────────────────
best_pf, best_sl, best_tgt = flat[0]
best_t = results[(best_sl, best_tgt)]
print(f'\nBest combo: SL={best_sl}x  TGT={best_tgt}x')
print(f'Overall: N={len(best_t):,}  PF={best_pf:.3f}  Sharpe={calc_sharpe(best_t):.3f}')

print(f'\n{"Year":<6} {"N":>5}  {"PF":>6}  {"Sharpe":>7}')
for yr in range(2015, 2026):
    g = [t for t in best_t if t['year'] == yr]
    if not g: continue
    gp = sum(t['pnl'] for t in g if t['pnl'] > 0)
    gl = sum(-t['pnl'] for t in g if t['pnl'] < 0)
    print(f'  {yr}  {len(g):>5}  {gp/gl if gl>0 else 0:>6.3f}  {calc_sharpe(g):>7.3f}')

# ── Heatmap ────────────────────────────────────────────────────────────────────
grid_flipped = np.flipud(pf_grid)
sl_labels    = SL_VALS[::-1]
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
im = ax.imshow(grid_flipped, cmap='RdYlGn', vmin=0.75, vmax=1.10, aspect='auto')
ax.set_xticks(range(len(TGT_VALS))); ax.set_xticklabels(TGT_VALS, color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels, color='#aaa')
ax.set_xlabel('TGT Multiplier', color='#aaa', fontsize=11)
ax.set_ylabel('SL Multiplier', color='#aaa', fontsize=11)
ax.set_title('PF Heatmap — MA Bounce v1 LONG  |  30 Stocks · 2015-2025',
             color='white', fontsize=13, pad=12)
for si in range(len(SL_VALS)):
    for ti in range(len(TGT_VALS)):
        v = grid_flipped[si, ti]
        ax.text(ti, si, f'{v:.3f}', ha='center', va='center',
                fontsize=9, color='black' if 0.85 < v < 1.05 else 'white')
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('Profit Factor', color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#aaa')
plt.tight_layout()
out = os.path.join(OUT_DIR, 'sl_tgt_sweep_v1_long.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f'\nHeatmap saved: {out}')
