"""
SL x TGT grid sweep — MA Rejection v1 (SHORT) clean-touch
30 stocks · 2015-2025 · DS3 parquets (11-year full run)
Signal : single bar where high>=MA20 AND open<MA20 AND close<MA20 → short at next bar open
Logic  : single-pass (i = k+1 after each trade) — position guard intact
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF / Sh(D) reference
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
    df['year'] = df['datetime'].dt.year
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tgt_m):
    """Returns lists: pnl, entry, exit_px, year, date."""
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14             = arrays['ma20'],  arrays['atr14']
    hour, date, year        = arrays['hour'],  arrays['date'], arrays['year']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        # v1 clean-touch: wick touches MA, body stays below
        if (high[i] >= ma20[i] and open_[i] < ma20[i] and
                close[i] < ma20[i] and hour[i] < EOD_HOUR):
            ei = i + 1
            # entry next bar, same day; skip if EOD bar or date change
            if ei >= n or date[ei] != date[i] or hour[ei] >= EOD_HOUR:
                i += 1; continue
            entry = open_[ei]; atr = atr14[i]
            sl = entry + sl_m * atr; tgt = entry - tgt_m * atr
            signal_date = date[i]
            k = ei
            for k in range(ei, n):
                if date[k] != signal_date:
                    exit_px = close[k - 1]; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; break
                if high[k] >= sl:
                    exit_px = sl; break
                if low[k] <= tgt:
                    exit_px = tgt; break
            pnl_out.append(entry - exit_px)
            entry_out.append(entry); exit_out.append(exit_px)
            yr_out.append(year[ei]); dt_out.append(pd.Timestamp(date[ei]))
            i = k + 1
        else:
            i += 1
    return pnl_out, entry_out, exit_out, yr_out, dt_out


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
        'year':  df['year'].values,  'n':     len(df),
    })
print(f'Loaded. Running {len(SL_VALS)} x {len(TGT_VALS)} = {len(SL_VALS)*len(TGT_VALS)} combo grid sweep...')

# ── Grid sweep ─────────────────────────────────────────────────────────────────
combo_data = {}
pf_grid   = np.zeros((len(SL_VALS), len(TGT_VALS)))
zpf_grid  = np.zeros((len(SL_VALS), len(TGT_VALS)))
shd_grid  = np.zeros((len(SL_VALS), len(TGT_VALS)))
zshd_grid = np.zeros((len(SL_VALS), len(TGT_VALS)))
n_grid    = np.zeros((len(SL_VALS), len(TGT_VALS)), dtype=int)

for si, sl_m in enumerate(SL_VALS):
    for ti, tgt_m in enumerate(TGT_VALS):
        all_pnl = []; all_entry = []; all_exit = []; all_yr = []; all_dt = []
        for arr in stock_arrays:
            p, e, x, y, d = run_combo(arr, sl_m, tgt_m)
            all_pnl.extend(p); all_entry.extend(e); all_exit.extend(x)
            all_yr.extend(y); all_dt.extend(d)
        pnl   = np.array(all_pnl, dtype=float)
        entry = np.array(all_entry, dtype=float)
        exit_ = np.array(all_exit, dtype=float)
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
        combo_data[(sl_m, tgt_m)] = (pnl, zpnl, np.array(all_yr), all_dt)
        print(f'  SL={sl_m:.1f} TGT={tgt_m:.1f}  N={len(pnl):,}  PF={pf:.3f}  ZPF={zpf:.3f}  Sh(D)={shd:.3f}  ZSh(D)={zshd:.3f}')

# ── ZPF grid ───────────────────────────────────────────────────────────────────
print(f'\nZPF Grid (rows=SL, cols=TGT):')
print(f"{'SL\\TGT':>8}" + ''.join(f'{t:>7.1f}' for t in TGT_VALS))
for si, sl_m in enumerate(SL_VALS):
    print(f'{sl_m:>8.1f}' + ''.join(f'{zpf_grid[si, ti]:>7.3f}' for ti in range(len(TGT_VALS))))

# ── Full 90-combo table ────────────────────────────────────────────────────────
print(f'\nAll 90 combos:')
print(f"  {'SL':>4}  {'TGT':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
flat_zpf = sorted(
    [(zpf_grid[si, ti], pf_grid[si, ti], shd_grid[si, ti], zshd_grid[si, ti],
      SL_VALS[si], TGT_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TGT_VALS))],
    reverse=True
)
for si in range(len(SL_VALS)):
    for ti in range(len(TGT_VALS)):
        print(f"  {SL_VALS[si]:>4.1f}  {TGT_VALS[ti]:>4.1f}  {n_grid[si, ti]:>7,}  "
              f"{pf_grid[si, ti]:>6.3f}  {zpf_grid[si, ti]:>6.3f}  "
              f"{shd_grid[si, ti]:>7.3f}  {zshd_grid[si, ti]:>8.3f}")

# ── Top 5 by ZPF ───────────────────────────────────────────────────────────────
print(f'\nTop 5 by ZPF:')
print(f"  {'SL':>4}  {'TGT':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
for zpf, pf, shd, zshd, sl_m, tgt_m, n in flat_zpf[:5]:
    print(f"  {sl_m:>4.1f}  {tgt_m:>4.1f}  {n:>7,}  {pf:>6.3f}  {zpf:>6.3f}  {shd:>7.3f}  {zshd:>8.3f}")

# ── Top 5 by ZSh(D) ────────────────────────────────────────────────────────────
flat_zshd = sorted(
    [(zshd_grid[si, ti], zpf_grid[si, ti], pf_grid[si, ti], shd_grid[si, ti],
      SL_VALS[si], TGT_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TGT_VALS))],
    reverse=True
)
print(f'\nTop 5 by ZSh(D):')
print(f"  {'SL':>4}  {'TGT':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
for zshd, zpf, pf, shd, sl_m, tgt_m, n in flat_zshd[:5]:
    print(f"  {sl_m:>4.1f}  {tgt_m:>4.1f}  {n:>7,}  {pf:>6.3f}  {zpf:>6.3f}  {shd:>7.3f}  {zshd:>8.3f}")

# ── Best combo detail (by ZPF) ─────────────────────────────────────────────────
best_zpf, best_pf, best_shd, best_zshd, best_sl, best_tgt, best_n = flat_zpf[0]
pnl, zpnl, yrs, dts = combo_data[(best_sl, best_tgt)]
pct_days, n_days = pct_prof_days(zpnl, dts)
print(f'\nBest combo (ZPF): SL={best_sl}x  TGT={best_tgt}x')
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
best2_zshd, best2_zpf, best2_pf, best2_shd, best2_sl, best2_tgt, best2_n = flat_zshd[0]
print(f'\nBest combo (ZSh(D)): SL={best2_sl}x  TGT={best2_tgt}x  '
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
ax.set_xticks(range(len(TGT_VALS))); ax.set_xticklabels(TGT_VALS, color='#aaa')
ax.set_yticks(range(len(SL_VALS)));  ax.set_yticklabels(sl_labels, color='#aaa')
ax.set_xlabel('TGT Multiplier', color='#aaa', fontsize=11)
ax.set_ylabel('SL Multiplier', color='#aaa', fontsize=11)
ax.set_title('ZPF Heatmap — MA Rejection v1 SHORT  |  30 Stocks · 2015-2025  |  Zerodha',
             color='white', fontsize=13, pad=12)
for si in range(len(SL_VALS)):
    for ti in range(len(TGT_VALS)):
        v = grid_flipped[si, ti]
        mid = (vmin + vmax) / 2
        ax.text(ti, si, f'{v:.3f}', ha='center', va='center',
                fontsize=9, color='black' if abs(v - mid) < (vmax - vmin) * 0.35 else 'white')
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('ZPF', color='#aaa')
cbar.ax.yaxis.set_tick_params(color='#aaa')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#aaa')
plt.tight_layout()
out = os.path.join(OUT_DIR, 'sl_tgt_sweep_v1_short.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f'\nHeatmap saved: {out}')
