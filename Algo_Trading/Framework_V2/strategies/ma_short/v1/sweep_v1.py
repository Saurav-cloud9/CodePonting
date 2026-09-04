"""
SL x TP grid sweep — MA Rejection v1 (SHORT) clean-touch
30 stocks · 2015-2025 · DS3 parquets (11-year full run)
Signal : single bar where high>=MA20 AND open<MA20 AND close<MA20 → short at next bar open
Cutoff : live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
         (rerun 2026-09-04, replacing the pre-refinement 2026-07-29 numbers)
Logic  : single-pass (i = k+1 after each trade) — position guard intact
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF / Sh(D) reference
Exit-mix: SL-hit%/TP-hit%/EOD+%/EOD-% tracked per combo (2026-09-04 — wide SL/TP
          combos were winning by raw ZPF because they barely bind intraday and
          most trades just ride to EOD; this flags that instead of hiding it).
          Validated against strategies/_baseline_2026-09-04/ — this rerun's raw
          PF/ZPF/N per combo must exactly match the pre-instrumentation baseline
          (same signal/data/cutoff, purely additive tagging).
Output : sweep_cache_v1.npz (full 90-cell grid) + sweep_v1_results.md (top-5) +
         exit_breakdown_full.csv (90 rows), written alongside this script.
"""
import sys, io, glob, os
from datetime import time as _time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
OUT_DIR  = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/outputs/reports'
EOD_HOUR = 15
LAST_TOUCH_TIME   = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)

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
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['time'] = df['datetime'].dt.time
    df['year'] = df['datetime'].dt.year
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tp_m):
    """Returns lists: pnl, entry, exit_px, year, date."""
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14             = arrays['ma20'],  arrays['atr14']
    hour, date, time_, year = arrays['hour'],  arrays['date'], arrays['time'], arrays['year']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []; type_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        # v1 clean-touch: wick touches MA, body stays below; live-matching touch cutoff
        if (high[i] >= ma20[i] and open_[i] < ma20[i] and
                close[i] < ma20[i] and time_[i] <= LAST_TOUCH_TIME):
            ei = i + 1
            # entry next bar, same day; cancelled outright if past entry cutoff (no trade)
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1; continue
            entry = open_[ei]; atr = atr14[i]
            sl = entry + sl_m * atr; tp = entry - tp_m * atr
            signal_date = date[i]
            k = ei
            etype = 'EOD'
            for k in range(ei, n):
                if date[k] != signal_date:
                    exit_px = close[k - 1]; etype = 'EOD'; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; etype = 'EOD'; break
                if high[k] >= sl:
                    exit_px = sl; etype = 'SL'; break
                if low[k] <= tp:
                    exit_px = tp; etype = 'TP'; break
            pnl_out.append(entry - exit_px)
            entry_out.append(entry); exit_out.append(exit_px)
            yr_out.append(year[ei]); dt_out.append(pd.Timestamp(date[ei]))
            type_out.append(etype)
            i = k + 1
        else:
            i += 1
    return pnl_out, entry_out, exit_out, yr_out, dt_out, type_out


def pf_from_arrays(pnl):
    gw = pnl[pnl > 0].sum(); gl = -pnl[pnl < 0].sum()
    return round(float(gw / gl), 3) if gl > 0 else 0.0


def zpf_from_arrays(zpnl):
    zw = zpnl[zpnl > 0].sum(); zl = -zpnl[zpnl <= 0].sum()
    return round(float(zw / zl), 3) if zl > 0 else 0.0


def shd_from_arrays(pnl, dates):
    tdf = pd.DataFrame({'pnl': pnl, 'date': dates})
    daily = tdf.set_index('date').resample('D')['pnl'].sum()
    daily = daily[daily != 0]
    return round(float((daily.mean() / daily.std()) * np.sqrt(252)), 3) if len(daily) > 1 and daily.std() > 0 else 0.0


def zshd_from_arrays(zpnl, dates):
    tdf = pd.DataFrame({'zpnl': zpnl, 'date': dates})
    daily = tdf.set_index('date').resample('D')['zpnl'].sum()
    daily = daily[daily != 0]
    return round(float((daily.mean() / daily.std()) * np.sqrt(252)), 3) if len(daily) > 1 and daily.std() > 0 else 0.0


def pct_prof_days(zpnl, dates):
    tdf = pd.DataFrame({'zpnl': zpnl, 'date': dates})
    daily = tdf.set_index('date').resample('D')['zpnl'].sum()
    daily = daily[daily != 0]
    if len(daily) == 0:
        return 0.0, 0
    return round(float((daily > 0).mean() * 100), 1), len(daily)


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
        'time':  df['time'].values,
        'year':  df['year'].values,  'n':     len(df),
    })
print(f'Loaded. Running {len(SL_VALS)} x {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combo grid sweep...')

# ── Grid sweep ─────────────────────────────────────────────────────────────────
combo_data = {}
pf_grid   = np.zeros((len(SL_VALS), len(TP_VALS)))
zpf_grid  = np.zeros((len(SL_VALS), len(TP_VALS)))
shd_grid  = np.zeros((len(SL_VALS), len(TP_VALS)))
zshd_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
n_grid    = np.zeros((len(SL_VALS), len(TP_VALS)), dtype=int)

exit_rows = []
for si, sl_m in enumerate(SL_VALS):
    for ti, tp_m in enumerate(TP_VALS):
        all_pnl = []; all_entry = []; all_exit = []; all_yr = []; all_dt = []; all_type = []
        for arr in stock_arrays:
            p, e, x, y, d, t = run_combo(arr, sl_m, tp_m)
            all_pnl.extend(p); all_entry.extend(e); all_exit.extend(x)
            all_yr.extend(y); all_dt.extend(d); all_type.extend(t)
        pnl   = np.array(all_pnl, dtype=float)
        entry = np.array(all_entry, dtype=float)
        exit_ = np.array(all_exit, dtype=float)
        types = np.array(all_type)
        zpnl  = pnl - zerodha_vec_short(entry, exit_)
        pf   = pf_from_arrays(pnl)
        zpf  = zpf_from_arrays(zpnl)
        shd  = shd_from_arrays(pnl, all_dt)
        zshd = zshd_from_arrays(zpnl, all_dt)
        pf_grid[si, ti]   = pf
        zpf_grid[si, ti]  = zpf
        shd_grid[si, ti]  = shd
        zshd_grid[si, ti] = zshd
        n_grid[si, ti]    = len(pnl)
        combo_data[(sl_m, tp_m)] = (pnl, zpnl, np.array(all_yr), all_dt)
        ntot = len(pnl)
        sl_pct  = round(float((types == 'SL').sum()) / ntot * 100, 1) if ntot else 0.0
        tp_pct  = round(float((types == 'TP').sum()) / ntot * 100, 1) if ntot else 0.0
        eod_mask = types == 'EOD'
        eod_plus_pct  = round(float((eod_mask & (pnl > 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        eod_minus_pct = round(float((eod_mask & (pnl <= 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        exit_rows.append({'sl': sl_m, 'tp': tp_m, 'n': ntot, 'pf': pf, 'zpf': zpf,
                           'shd': shd, 'zshd': zshd, 'sl_hit_pct': sl_pct, 'tp_hit_pct': tp_pct,
                           'eod_plus_pct': eod_plus_pct, 'eod_minus_pct': eod_minus_pct})
        print(f'  SL={sl_m:.1f} TP={tp_m:.1f}  N={len(pnl):,}  PF={pf:.3f}  ZPF={zpf:.3f}  Sh(D)={shd:.3f}  ZSh(D)={zshd:.3f}  '
              f'SL%={sl_pct:.1f} TP%={tp_pct:.1f} EOD+%={eod_plus_pct:.1f} EOD-%={eod_minus_pct:.1f}')

# ── Save raw grid cache (matches 6bce's sweep_cache_<version>.npz convention) ──
cache_path = os.path.join(SCRIPT_DIR, 'sweep_cache_v1.npz')
np.savez(cache_path, overall_grid=zpf_grid, pf_grid=pf_grid, shd_grid=shd_grid, zshd_grid=zshd_grid, n_grid=n_grid)
print(f'\nGrid cache saved: {cache_path}')

# ── Validate against pre-instrumentation baseline (must match exactly) ─────────
baseline_path = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/strategies/_baseline_2026-09-04/ma_short_v1_sweep_cache.npz'
if os.path.exists(baseline_path):
    bl = np.load(baseline_path)
    mismatches = []
    if not np.allclose(bl['overall_grid'], zpf_grid, atol=1e-6):
        mismatches.append('ZPF grid')
    if not np.allclose(bl['pf_grid'], pf_grid, atol=1e-6):
        mismatches.append('PF grid')
    if not np.array_equal(bl['n_grid'], n_grid):
        mismatches.append('N grid')
    if mismatches:
        print(f'\n⚠️  VALIDATION FAILED against baseline — mismatched: {mismatches}. '
              f'Instrumentation may have broken the underlying trade logic — do not trust exit-mix numbers.')
    else:
        print('\n✅ Validation OK — PF/ZPF/N grids match pre-instrumentation baseline exactly.')
else:
    print(f'\n⚠️  No baseline found at {baseline_path} — skipping validation.')

# ── Exit-mix CSV + healthy-subset top-5 (EOD% <= 30 threshold) ─────────────────
exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, 'exit_breakdown_full.csv')
exit_df.to_csv(csv_path, index=False)
print(f'Exit breakdown saved: {csv_path}')

exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']
healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
best_idx = np.unravel_index(np.argmax(zpf_grid), zpf_grid.shape)
top5_raw_sl, top5_raw_tp = SL_VALS[best_idx[0]], TP_VALS[best_idx[1]]
raw_row = exit_df[(exit_df['sl'] == top5_raw_sl) & (exit_df['tp'] == top5_raw_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={top5_raw_sl} TP={top5_raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')
print('\nHealthy-subset top-5 (EOD% <= 30):')
print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

# ── ZPF grid ───────────────────────────────────────────────────────────────────
print(f'\nZPF Grid (rows=SL, cols=TP):')
print(f"{'SL\\TP':>8}" + ''.join(f'{t:>7.1f}' for t in TP_VALS))
for si, sl_m in enumerate(SL_VALS):
    print(f'{sl_m:>8.1f}' + ''.join(f'{zpf_grid[si, ti]:>7.3f}' for ti in range(len(TP_VALS))))

# ── Full 90-combo table ────────────────────────────────────────────────────────
print(f'\nAll 90 combos:')
print(f"  {'SL':>4}  {'TP':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
flat_zpf = sorted(
    [(zpf_grid[si, ti], pf_grid[si, ti], shd_grid[si, ti], zshd_grid[si, ti],
      SL_VALS[si], TP_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))],
    reverse=True
)
for si in range(len(SL_VALS)):
    for ti in range(len(TP_VALS)):
        print(f"  {SL_VALS[si]:>4.1f}  {TP_VALS[ti]:>4.1f}  {n_grid[si, ti]:>7,}  "
              f"{pf_grid[si, ti]:>6.3f}  {zpf_grid[si, ti]:>6.3f}  "
              f"{shd_grid[si, ti]:>7.3f}  {zshd_grid[si, ti]:>8.3f}")

# ── Top 5 by ZPF ───────────────────────────────────────────────────────────────
print(f'\nTop 5 by ZPF:')
print(f"  {'SL':>4}  {'TP':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
for zpf, pf, shd, zshd, sl_m, tp_m, n in flat_zpf[:5]:
    print(f"  {sl_m:>4.1f}  {tp_m:>4.1f}  {n:>7,}  {pf:>6.3f}  {zpf:>6.3f}  {shd:>7.3f}  {zshd:>8.3f}")

# ── Top 5 by ZSh(D) ────────────────────────────────────────────────────────────
flat_zshd = sorted(
    [(zshd_grid[si, ti], zpf_grid[si, ti], pf_grid[si, ti], shd_grid[si, ti],
      SL_VALS[si], TP_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))],
    reverse=True
)
print(f'\nTop 5 by ZSh(D):')
print(f"  {'SL':>4}  {'TP':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
for zshd, zpf, pf, shd, sl_m, tp_m, n in flat_zshd[:5]:
    print(f"  {sl_m:>4.1f}  {tp_m:>4.1f}  {n:>7,}  {pf:>6.3f}  {zpf:>6.3f}  {shd:>7.3f}  {zshd:>8.3f}")

# ── Best combo detail (by ZPF) ─────────────────────────────────────────────────
best_zpf, best_pf, best_shd, best_zshd, best_sl, best_tp, best_n = flat_zpf[0]
pnl, zpnl, yrs, dts = combo_data[(best_sl, best_tp)]
pct_days, n_days = pct_prof_days(zpnl, dts)
print(f'\nBest combo (ZPF): SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={len(pnl):,}  Days={n_days:,}  PF={best_pf:.3f}  ZPF={best_zpf:.3f}  '
      f'Sh(D)={best_shd:.3f}  ZSh(D)={best_zshd:.3f}  %ProfDays={pct_days:.1f}%')

print(f'\n{"Year":<6} {"N":>6}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  Flag')
for yr in range(2015, 2026):
    mask = yrs == yr
    if mask.sum() == 0:
        continue
    p_y = pnl[mask]; z_y = zpnl[mask]
    d_y = [d for d, m in zip(dts, mask) if m]
    pf_y   = pf_from_arrays(p_y)
    zpf_y  = zpf_from_arrays(z_y)
    shd_y  = shd_from_arrays(p_y, d_y)
    zshd_y = zshd_from_arrays(z_y, d_y)
    flag = '✅' if zpf_y >= 1.0 else ('🟡' if zpf_y >= 0.9 else '❌')
    print(f'  {yr}  {mask.sum():>6}  {pf_y:>6.3f}  {zpf_y:>6.3f}  {shd_y:>7.3f}  {zshd_y:>8.3f}  {flag}')

# ── Best by ZSh(D) overall line ────────────────────────────────────────────────
best2_zshd, best2_zpf, best2_pf, best2_shd, best2_sl, best2_tp, best2_n = flat_zshd[0]
print(f'\nBest combo (ZSh(D)): SL={best2_sl}x  TP={best2_tp}x  '
      f'N={best2_n:,}  PF={best2_pf:.3f}  ZPF={best2_zpf:.3f}  '
      f'Sh(D)={best2_shd:.3f}  ZSh(D)={best2_zshd:.3f}')

# ── ZPF Heatmap ────────────────────────────────────────────────────────────────
grid_flipped = np.flipud(zpf_grid)
sl_labels    = SL_VALS[::-1]
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
vmin = float(np.nanmin(zpf_grid)) if zpf_grid.size else 0.65
vmax = float(np.nanmax(zpf_grid)) if zpf_grid.size else 0.90
# pad slightly so cells are readable
pad = max(0.02, (vmax - vmin) * 0.05)
im = ax.imshow(grid_flipped, cmap='RdYlGn', vmin=vmin - pad, vmax=vmax + pad, aspect='auto')
ax.set_xticks(range(len(TP_VALS))); ax.set_xticklabels(TP_VALS, color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels, color='#aaa')
ax.set_xlabel('TP Multiplier', color='#aaa', fontsize=11)
ax.set_ylabel('SL Multiplier', color='#aaa', fontsize=11)
ax.set_title('ZPF Heatmap — MA Rejection v1 SHORT  |  30 Stocks · 2015-2025  |  Zerodha',
             color='white', fontsize=13, pad=12)
for si in range(len(SL_VALS)):
    for ti in range(len(TP_VALS)):
        v = grid_flipped[si, ti]
        mid = (vmin + vmax) / 2
        ax.text(ti, si, f'{v:.3f}', ha='center', va='center',
                fontsize=9, color='black' if abs(v - mid) < (vmax - vmin) * 0.35 else 'white')
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('ZPF', color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#aaa')
plt.tight_layout()
out = os.path.join(OUT_DIR, 'sl_tp_sweep_v1_short.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f'\nHeatmap saved: {out}')
