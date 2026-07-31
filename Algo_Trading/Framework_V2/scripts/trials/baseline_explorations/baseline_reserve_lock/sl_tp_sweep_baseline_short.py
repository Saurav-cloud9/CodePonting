"""
SL x TP grid sweep — MA Rejection SHORT baseline
30 stocks · 2015-2025 · DS3 parquets (11-year full run)
Signal: high >= MA20 → close < MA20 within MAX_TR_GAP=3 → short at next bar open
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF reference
Vectorized numpy ZPF for speed.
"""
import sys, io, glob, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
OUT_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\reports'
EOD_HOUR   = 15
MAX_TR_GAP = 3

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_vec_short(entry, exit_px):
    """Vectorized Zerodha charge for SHORT (entry=sell, exit=buy)."""
    brok  = np.minimum(0.0003 * entry, 20) + np.minimum(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load(f):
    df = pd.read_parquet(f)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date']  = df['datetime'].dt.date
    df['hour']  = df['datetime'].dt.hour
    df['year']  = df['datetime'].dt.year
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tp_m):
    """Returns lists: pnl, entry, exit_px, year, date."""
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14 = arrays['ma20'], arrays['atr14']
    hour, date, year = arrays['hour'], arrays['date'], arrays['year']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        if high[i] >= ma20[i] and hour[i] < EOD_HOUR:
            touch_date = date[i]; atr = atr14[i]; rej = -1
            for j in range(i, min(i + MAX_TR_GAP + 1, n)):
                if date[j] != touch_date or hour[j] >= EOD_HOUR: break
                if close[j] < ma20[j]: rej = j; break
            if rej < 0: i += 1; continue
            ei = rej + 1
            if ei >= n or date[ei] != touch_date: i += 1; continue
            entry = open_[ei]; sl = entry + sl_m * atr; tp = entry - tp_m * atr
            k = ei
            for k in range(ei, n):
                if date[k] != touch_date:
                    exit_px = close[k - 1]; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; break
                if high[k] >= sl:
                    exit_px = sl; break
                if low[k] <= tp:
                    exit_px = tp; break
            pnl_out.append(entry - exit_px)
            entry_out.append(entry); exit_out.append(exit_px)
            yr_out.append(year[ei]); dt_out.append(pd.Timestamp(date[ei]))
            i = k + 1
        else:
            i += 1
    return pnl_out, entry_out, exit_out, yr_out, dt_out


def zpf_from_arrays(pnl, zpnl):
    zw = zpnl[zpnl > 0].sum(); zl = -zpnl[zpnl <= 0].sum()
    return round(zw / zl, 3) if zl > 0 else 0.0


def zshd_from_arrays(zpnl, dates):
    tdf = pd.DataFrame({'zpnl': zpnl, 'date': dates})
    daily = tdf.set_index('date').resample('D')['zpnl'].sum()
    daily = daily[daily != 0]
    return round((daily.mean() / daily.std()) * np.sqrt(252), 3) if len(daily) > 1 else 0.0


# ── Load all stocks ────────────────────────────────────────────────────────────
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
print(f'Loaded. Running {len(SL_VALS)} x {len(TP_VALS)} grid sweep...')

# ── Grid sweep ─────────────────────────────────────────────────────────────────
# Store (pnl, entry, exit_px, years, dates) per combo for later analysis
combo_data  = {}
pf_grid  = np.zeros((len(SL_VALS), len(TP_VALS)))
zpf_grid = np.zeros((len(SL_VALS), len(TP_VALS)))

for si, sl_m in enumerate(SL_VALS):
    for ti, tp_m in enumerate(TP_VALS):
        all_pnl = []; all_entry = []; all_exit = []; all_yr = []; all_dt = []
        for arr in stock_arrays:
            p, e, x, y, d = run_combo(arr, sl_m, tp_m)
            all_pnl.extend(p); all_entry.extend(e); all_exit.extend(x)
            all_yr.extend(y); all_dt.extend(d)
        pnl   = np.array(all_pnl)
        entry = np.array(all_entry)
        exit_ = np.array(all_exit)
        zpnl  = pnl - zerodha_vec_short(entry, exit_)
        gw = pnl[pnl > 0].sum(); gl = -pnl[pnl < 0].sum()
        pf_grid[si, ti]  = round(gw / gl, 3) if gl > 0 else 0.0
        zpf_grid[si, ti] = zpf_from_arrays(pnl, zpnl)
        combo_data[(sl_m, tp_m)] = (pnl, zpnl, np.array(all_yr), all_dt)

# ── ZPF grid ───────────────────────────────────────────────────────────────────
print(f'\nZPF Grid (rows=SL, cols=TP):')
print(f"{'SL\\TP':>8}" + ''.join(f'{t:>7.1f}' for t in TP_VALS))
for si, sl_m in enumerate(SL_VALS):
    print(f'{sl_m:>8.1f}' + ''.join(f'{zpf_grid[si, ti]:>7.3f}' for ti in range(len(TP_VALS))))

# ── Top 5 by ZPF ──────────────────────────────────────────────────────────────
flat = sorted(
    [(zpf_grid[si, ti], pf_grid[si, ti], SL_VALS[si], TP_VALS[ti])
     for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))],
    reverse=True
)
print(f'\nTop 5 by ZPF:')
print(f"  {'SL':>4}  {'TP':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'ZSh(D)':>8}")
for zpf, pf, sl_m, tp_m in flat[:5]:
    pnl, zpnl, yrs, dts = combo_data[(sl_m, tp_m)]
    print(f"  {sl_m:>4.1f}  {tp_m:>4.1f}  {len(pnl):>7,}  {pf:>6.3f}  {zpf:>6.3f}  {zshd_from_arrays(zpnl, dts):>8.3f}")

# ── Best combo detail ──────────────────────────────────────────────────────────
best_zpf, best_pf, best_sl, best_tp = flat[0]
pnl, zpnl, yrs, dts = combo_data[(best_sl, best_tp)]
print(f'\nBest combo (ZPF): SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={len(pnl):,}  PF={best_pf:.3f}  ZPF={best_zpf:.3f}  ZSh(D)={zshd_from_arrays(zpnl, dts):.3f}')

print(f'\n{"Year":<6} {"N":>6}  {"PF":>6}  {"ZPF":>6}  {"ZSh(D)":>8}')
for yr in sorted(np.unique(yrs)):
    mask = yrs == yr
    p_y = pnl[mask]; z_y = zpnl[mask]; d_y = [d for d, m in zip(dts, mask) if m]
    gw_y = p_y[p_y > 0].sum(); gl_y = -p_y[p_y < 0].sum()
    pf_y  = round(gw_y / gl_y, 3) if gl_y > 0 else 0.0
    zpf_y = zpf_from_arrays(p_y, z_y)
    flag = '✅' if zpf_y >= 1.0 else ('🟡' if zpf_y >= 0.9 else '❌')
    print(f'  {yr}  {mask.sum():>6}  {pf_y:>6.3f}  {zpf_y:>6.3f}  {zshd_from_arrays(z_y, d_y):>8.3f}  {flag}')

# ── ZPF Heatmap ────────────────────────────────────────────────────────────────
grid_flipped = np.flipud(zpf_grid)
sl_labels    = SL_VALS[::-1]
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
im = ax.imshow(grid_flipped, cmap='RdYlGn', vmin=0.65, vmax=0.90, aspect='auto')
ax.set_xticks(range(len(TP_VALS))); ax.set_xticklabels(TP_VALS, color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels, color='#aaa')
ax.set_xlabel('TP Multiplier', color='#aaa', fontsize=11)
ax.set_ylabel('SL Multiplier', color='#aaa', fontsize=11)
ax.set_title('ZPF Heatmap — MA Rejection SHORT  |  30 Stocks · 2015-2025  |  Zerodha charges',
             color='white', fontsize=13, pad=12)
for si in range(len(SL_VALS)):
    for ti in range(len(TP_VALS)):
        v = grid_flipped[si, ti]
        ax.text(ti, si, f'{v:.3f}', ha='center', va='center',
                fontsize=9, color='black' if 0.72 < v < 0.88 else 'white')
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('ZPF', color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#aaa')
plt.tight_layout()
out = os.path.join(OUT_DIR, 'sl_tp_sweep_baseline_short_zpf.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f'\nHeatmap saved: {out}')
