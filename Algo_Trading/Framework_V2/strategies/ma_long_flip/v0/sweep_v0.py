"""
SL x TP grid sweep — MA-long "flip" (SHORT on the bullish-bounce candle)
30 stocks · DS3 (2015-02-02 to 2026-08-31)
Signal : ma_bounce's clean touch (low<=MA20, open>MA20, close>MA20 — the
         bullish-looking bounce candle), but SHORT instead of LONG — a
         contrarian bet that the bounce is a fakeout/trap (SMC
         "inducement"-adjacent), not genuine continuation.
Motivated by: 3-combo spot check (2026-09-04) showed PF>1.0 across the board
         (1.131-1.147), unlike ma_short_flip (LONG on ma_short's bearish
         touch) which was decisively ruled out (PF<1.0 at every combo tested).
         This is the first full-rigor treatment of this hypothesis.
Cutoff : live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
Logic  : single-pass (i = k+1 after each trade) — position guard intact
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF / Sh(D) reference
Exit-mix: SL-hit%/TP-hit%/EOD+%/EOD-% tracked per combo from the start (per
         backtesting_rules.md's mandatory diagnostic, added 2026-09-04 after
         finding wide-SL/TP combos win on raw ZPF purely via EOD-riding).
Output : sweep_cache_v0.npz (full 90-cell grid) + exit_breakdown_full.csv (90 rows),
         written alongside this script. No pre-instrumentation baseline exists
         for this variant (first time computing it) — nothing to validate against.
"""
import sys, io, glob, os
from datetime import time as _time
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
LAST_TOUCH_TIME   = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_vec_short(entry, exit_px):
    """Vectorized Zerodha charge for SHORT (entry=sell, exit=buy)."""
    brok = np.minimum(0.0003 * entry, 20) + np.minimum(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
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
    """Returns lists: pnl, entry, exit_px, year, date, exit_type."""
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14 = arrays['ma20'], arrays['atr14']
    hour, date, time_, year = arrays['hour'], arrays['date'], arrays['time'], arrays['year']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []; type_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        # ma_bounce clean-touch: wick touches MA from above, body stays above; SHORT (flip)
        if (low[i] <= ma20[i] and open_[i] > ma20[i] and
                close[i] > ma20[i] and time_[i] <= LAST_TOUCH_TIME):
            ei = i + 1
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1; continue
            entry = open_[ei]; atr = atr14[i]
            sl = entry + sl_m * atr   # SHORT: stop above
            tp = entry - tp_m * atr   # SHORT: target below
            signal_date = date[i]
            k = ei; etype = 'EOD'
            for k in range(ei, n):
                if date[k] != signal_date:
                    exit_px = close[k - 1]; etype = 'EOD'; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; etype = 'EOD'; break
                if high[k] >= sl:
                    exit_px = sl; etype = 'SL'; break
                if low[k] <= tp:
                    exit_px = tp; etype = 'TP'; break
            pnl_out.append(entry - exit_px)   # SHORT: profit if exit < entry
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
        'high': df['high'].values, 'low': df['low'].values,
        'open_': df['open'].values, 'close': df['close'].values,
        'ma20': df['ma20'].values, 'atr14': df['atr14'].values,
        'hour': df['hour'].values, 'date': df['date'].values,
        'time': df['time'].values, 'year': df['year'].values, 'n': len(df),
    })
print(f'Loaded. Running {len(SL_VALS)} x {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combo grid sweep...')

# ── Grid sweep ─────────────────────────────────────────────────────────────────
combo_data = {}
pf_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
zpf_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
shd_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
zshd_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
n_grid = np.zeros((len(SL_VALS), len(TP_VALS)), dtype=int)
exit_rows = []

for si, sl_m in enumerate(SL_VALS):
    for ti, tp_m in enumerate(TP_VALS):
        all_pnl = []; all_entry = []; all_exit = []; all_yr = []; all_dt = []; all_type = []
        for arr in stock_arrays:
            p, e, x, y, d, t = run_combo(arr, sl_m, tp_m)
            all_pnl.extend(p); all_entry.extend(e); all_exit.extend(x)
            all_yr.extend(y); all_dt.extend(d); all_type.extend(t)
        pnl = np.array(all_pnl, dtype=float)
        entry = np.array(all_entry, dtype=float)
        exit_ = np.array(all_exit, dtype=float)
        types = np.array(all_type)
        zpnl = pnl - zerodha_vec_short(entry, exit_)
        pf = pf_from_arrays(pnl)
        zpf = zpf_from_arrays(zpnl)
        shd = shd_from_arrays(pnl, all_dt)
        zshd = zshd_from_arrays(zpnl, all_dt)
        pf_grid[si, ti] = pf; zpf_grid[si, ti] = zpf
        shd_grid[si, ti] = shd; zshd_grid[si, ti] = zshd
        n_grid[si, ti] = len(pnl)
        combo_data[(sl_m, tp_m)] = (pnl, zpnl, np.array(all_yr), all_dt)

        ntot = len(pnl)
        sl_pct = round(float((types == 'SL').sum()) / ntot * 100, 1) if ntot else 0.0
        tp_pct = round(float((types == 'TP').sum()) / ntot * 100, 1) if ntot else 0.0
        eod_mask = types == 'EOD'
        eod_plus_pct = round(float((eod_mask & (pnl > 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        eod_minus_pct = round(float((eod_mask & (pnl <= 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        exit_rows.append({'sl': sl_m, 'tp': tp_m, 'n': ntot, 'pf': pf, 'zpf': zpf,
                           'shd': shd, 'zshd': zshd, 'sl_hit_pct': sl_pct, 'tp_hit_pct': tp_pct,
                           'eod_plus_pct': eod_plus_pct, 'eod_minus_pct': eod_minus_pct})
        print(f'  SL={sl_m:.1f} TP={tp_m:.1f}  N={len(pnl):,}  PF={pf:.3f}  ZPF={zpf:.3f}  Sh(D)={shd:.3f}  ZSh(D)={zshd:.3f}  '
              f'SL%={sl_pct:.1f} TP%={tp_pct:.1f} EOD+%={eod_plus_pct:.1f} EOD-%={eod_minus_pct:.1f}')

# ── Save ─────────────────────────────────────────────────────────────────────
cache_path = os.path.join(SCRIPT_DIR, 'sweep_cache_v0.npz')
np.savez(cache_path, overall_grid=zpf_grid, pf_grid=pf_grid, shd_grid=shd_grid, zshd_grid=zshd_grid, n_grid=n_grid)
print(f'\nGrid cache saved: {cache_path}')

exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, 'exit_breakdown_full.csv')
exit_df.to_csv(csv_path, index=False)
print(f'Exit breakdown saved: {csv_path}')
exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']

# ── Top 5 by ZPF (raw) ─────────────────────────────────────────────────────────
flat_zpf = sorted(
    [(zpf_grid[si, ti], pf_grid[si, ti], shd_grid[si, ti], zshd_grid[si, ti],
      SL_VALS[si], TP_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))],
    reverse=True
)
print(f'\nTop 5 by ZPF (raw):')
print(f"  {'SL':>4}  {'TP':>4}  {'N':>7}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}")
for zpf, pf, shd, zshd, sl_m, tp_m, n in flat_zpf[:5]:
    print(f"  {sl_m:>4.1f}  {tp_m:>4.1f}  {n:>7,}  {pf:>6.3f}  {zpf:>6.3f}  {shd:>7.3f}  {zshd:>8.3f}")

best_idx = np.unravel_index(np.argmax(zpf_grid), zpf_grid.shape)
raw_sl, raw_tp = SL_VALS[best_idx[0]], TP_VALS[best_idx[1]]
raw_row = exit_df[(exit_df['sl'] == raw_sl) & (exit_df['tp'] == raw_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={raw_sl} TP={raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')

healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
print('\nHealthy-subset top-5 (EOD% <= 30):')
print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

best_zpf, best_pf, best_shd, best_zshd, best_sl, best_tp, best_n = flat_zpf[0]
pnl, zpnl, yrs, dts = combo_data[(best_sl, best_tp)]
pct_days, n_days = pct_prof_days(zpnl, dts)
print(f'\nBest combo overall (ZPF): SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={len(pnl):,}  Days={n_days:,}  PF={best_pf:.3f}  ZPF={best_zpf:.3f}  '
      f'Sh(D)={best_shd:.3f}  ZSh(D)={best_zshd:.3f}  %ProfDays={pct_days:.1f}%')

print(f'\n{"Year":<6} {"N":>6}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  Flag')
for yr in range(2015, 2027):
    mask = yrs == yr
    if mask.sum() == 0:
        continue
    p_y = pnl[mask]; z_y = zpnl[mask]
    d_y = [d for d, m in zip(dts, mask) if m]
    pf_y = pf_from_arrays(p_y); zpf_y = zpf_from_arrays(z_y)
    shd_y = shd_from_arrays(p_y, d_y); zshd_y = zshd_from_arrays(z_y, d_y)
    flag = 'OK' if zpf_y >= 1.0 else ('YEL' if zpf_y >= 0.9 else 'NO')
    print(f'  {yr}  {mask.sum():>6}  {pf_y:>6.3f}  {zpf_y:>6.3f}  {shd_y:>7.3f}  {zshd_y:>8.3f}  {flag}')

print('\nDone.')
