import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
import glob
import os
from datetime import time as _time

# 6BCE (6-Bar Close Extreme) — SHORT — 90-combo SL/TP sweep
# Signal: close[i] == highest close of last 6 bars (i-5 to i inclusive)
# Entry:  SHORT at open[i+1], same day
# Cutoff: live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
#         (rerun 2026-09-04, replacing the pre-refinement crude hour>=15 check)
# Exit:   date change → hour≥15 → SL → TP
# Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF + Sh(D) reference
# Sharpe: daily (×√252)
# Output: sweep_cache_v0.npz (full 90-cell grid) + sweep_v0_results.md (top-5)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
WINDOW   = 6
LAST_TOUCH_TIME   = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_charge(entry, exit_px):
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_stocks():
    stocks = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet'))):
        df = pd.read_parquet(f)
        df['datetime'] = pd.to_datetime(df['datetime'])
        if df['datetime'].dt.tz is not None:
            df['datetime'] = df['datetime'].dt.tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'atr14']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['time'] = df['datetime'].dt.time
        stocks.append({
            'open':  df['open'].values,
            'high':  df['high'].values,
            'low':   df['low'].values,
            'close': df['close'].values,
            'atr14': df['atr14'].values,
            'hour':  df['hour'].values,
            'date':  df['date'].values,
            'time':  df['time'].values,
            'n':     len(df),
        })
    return stocks


def run_combo(stocks, sl_m, tp_m):
    all_pnl   = []
    all_zpnl  = []
    all_dates = []
    all_types = []

    for s in stocks:
        close = s['close']; high = s['high']; low  = s['low']
        open_ = s['open'];  atr  = s['atr14']
        hour  = s['hour'];  date = s['date'];  time_ = s['time'];  n = s['n']

        i = WINDOW - 1
        while i < n:
            if np.isnan(atr[i]) or time_[i] > LAST_TOUCH_TIME:
                i += 1
                continue
            window = close[i - WINDOW + 1: i + 1]
            if np.any(np.isnan(window)) or close[i] < np.max(window):
                i += 1
                continue
            ei = i + 1
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1
                continue
            entry_px   = open_[ei]
            sl         = entry_px + sl_m  * atr[i]
            tp        = entry_px - tp_m * atr[i]
            trade_date = date[i]
            k = ei
            exit_px = entry_px
            exit_dt = trade_date
            etype = 'EOD'
            while k < n:
                if date[k] != trade_date:
                    exit_px = close[k - 1]; exit_dt = date[k - 1]; etype = 'EOD'; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; exit_dt = date[k]; etype = 'EOD'; break
                if high[k] >= sl:
                    exit_px = sl; exit_dt = date[k]; etype = 'SL'; break
                if low[k] <= tp:
                    exit_px = tp; exit_dt = date[k]; etype = 'TP'; break
                k += 1
            else:
                exit_px = close[k - 1]; exit_dt = date[k - 1]; etype = 'EOD'

            pnl  = entry_px - exit_px
            zpnl = pnl - zerodha_charge(entry_px, exit_px)
            all_pnl.append(pnl)
            all_zpnl.append(zpnl)
            all_dates.append(exit_dt)
            all_types.append(etype)
            i = k + 1

    return all_pnl, all_zpnl, all_dates, all_types


def compute_metrics(pnl_list, zpnl_list, date_list):
    if not pnl_list:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0
    pnl  = np.array(pnl_list)
    zpnl = np.array(zpnl_list)
    gp   = pnl[pnl > 0].sum();   gl  = abs(pnl[pnl < 0].sum())
    zgp  = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
    pf   = round(gp  / gl,  3) if gl  > 0 else 0.0
    zpf  = round(zgp / zgl, 3) if zgl > 0 else 0.0
    daily = (pd.DataFrame({'pnl': pnl, 'zpnl': zpnl, 'date': date_list})
               .groupby('date')[['pnl', 'zpnl']].sum())
    shd  = round((daily['pnl'].mean()  / daily['pnl'].std())  * np.sqrt(252), 3) if daily['pnl'].std()  > 0 else 0.0
    zshd = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0
    pct  = round((daily['zpnl'] > 0).sum() / len(daily) * 100, 1)
    return len(pnl), pf, zpf, shd, zshd, pct


def year_metrics(pnl_list, zpnl_list, date_list):
    df = pd.DataFrame({'pnl': pnl_list, 'zpnl': zpnl_list, 'date': date_list})
    df['year'] = pd.to_datetime(df['date']).dt.year
    rows = []
    for yr, g in df.groupby('year'):
        pnl  = g['pnl'].values;  zpnl = g['zpnl'].values
        gp   = pnl[pnl > 0].sum();   gl  = abs(pnl[pnl < 0].sum())
        zgp  = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
        pf   = round(gp  / gl,  3) if gl  > 0 else 0.0
        zpf  = round(zgp / zgl, 3) if zgl > 0 else 0.0
        daily = g.groupby('date')[['pnl', 'zpnl']].sum()
        nd   = len(daily)
        shd  = round((daily['pnl'].mean()  / daily['pnl'].std())  * np.sqrt(252), 3) if daily['pnl'].std()  > 0 else 0.0
        zshd = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0
        pct  = round((daily['zpnl'] > 0).sum() / nd * 100, 1) if nd > 0 else 0.0
        flag = 'OK' if zpf >= 1.0 else ('YEL' if zpf >= 0.90 else 'NO')
        rows.append({'Year': yr, 'N': len(g), 'Days': nd,
                     'PF': pf, 'ZPF': zpf, 'Sh(D)': shd, 'ZSh(D)': zshd,
                     '%ProfDays': pct, '': flag})
    return rows


def consistency_score(pnl_list, zpnl_list, date_list, lam=1.0):
    rows = year_metrics(pnl_list, zpnl_list, date_list)
    if len(rows) < 2:
        return 0.0
    ys = np.array([r['ZSh(D)'] for r in rows], dtype=float)
    return round(float(ys.mean() - lam * ys.std(ddof=0)), 3)


# ── MAIN ──────────────────────────────────────────────────────────────────────
print('Strategy: 6BCE SHORT — close[i] == max(close[i-5..i])')
print('Entry: SHORT open[i+1], same day')
print('Cutoff: live-matching LAST_TOUCH<=14:45, ENTRY_CUTOFF<=14:50')
print('Data: DS3 30 stocks 2015-2025\n')
print('Loading stocks...')
stocks = load_stocks()
print(f'Loaded {len(stocks)} stocks. Running {len(SL_VALS)} × {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combos...\n')

results = {}
trade_cache = {}
exit_rows = []
for sl in SL_VALS:
    for tp in TP_VALS:
        pnl, zpnl, dates, types = run_combo(stocks, sl, tp)
        n, pf, zpf, shd, zshd, pct = compute_metrics(pnl, zpnl, dates)
        ndays = len(set(dates)) if dates else 0
        cs = consistency_score(pnl, zpnl, dates)
        results[(sl, tp)] = (n, ndays, pf, zpf, shd, zshd, pct, cs)
        trade_cache[(sl, tp)] = (pnl, zpnl, dates)
        pnl_arr = np.array(pnl); types_arr = np.array(types)
        ntot = len(pnl)
        sl_pct  = round(float((types_arr == 'SL').sum()) / ntot * 100, 1) if ntot else 0.0
        tp_pct  = round(float((types_arr == 'TP').sum()) / ntot * 100, 1) if ntot else 0.0
        eod_mask = types_arr == 'EOD'
        eod_plus_pct  = round(float((eod_mask & (pnl_arr > 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        eod_minus_pct = round(float((eod_mask & (pnl_arr <= 0)).sum()) / ntot * 100, 1) if ntot else 0.0
        exit_rows.append({'sl': sl, 'tp': tp, 'n': ntot, 'pf': pf, 'zpf': zpf,
                           'shd': shd, 'zshd': zshd, 'sl_hit_pct': sl_pct, 'tp_hit_pct': tp_pct,
                           'eod_plus_pct': eod_plus_pct, 'eod_minus_pct': eod_minus_pct})
        print(f'  SL={sl:.1f} TP={tp:.1f}  N={n:,}  PF={pf:.3f}  ZPF={zpf:.3f}  Sh(D)={shd:.3f}  ZSh(D)={zshd:.3f}  '
              f'SL%={sl_pct:.1f} TP%={tp_pct:.1f} EOD+%={eod_plus_pct:.1f} EOD-%={eod_minus_pct:.1f}')

# ── Save raw grid cache ─────────────────────────────────────────────────────
overall_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
pf_grid      = np.zeros((len(SL_VALS), len(TP_VALS)))
shd_grid     = np.zeros((len(SL_VALS), len(TP_VALS)))
zshd_grid    = np.zeros((len(SL_VALS), len(TP_VALS)))
n_grid       = np.zeros((len(SL_VALS), len(TP_VALS)), dtype=int)
for si, sl in enumerate(SL_VALS):
    for ti, tp in enumerate(TP_VALS):
        n, ndays, pf, zpf, shd, zshd, pct, cs = results[(sl, tp)]
        overall_grid[si, ti] = zpf; pf_grid[si, ti] = pf
        shd_grid[si, ti] = shd; zshd_grid[si, ti] = zshd; n_grid[si, ti] = n
cache_path = os.path.join(SCRIPT_DIR, 'sweep_cache_v0.npz')
np.savez(cache_path, overall_grid=overall_grid, pf_grid=pf_grid, shd_grid=shd_grid,
         zshd_grid=zshd_grid, n_grid=n_grid)
print(f'\nGrid cache saved: {cache_path}')

baseline_path = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/strategies/_baseline_2026-09-04/6bce_v0_sweep_cache.npz'
if os.path.exists(baseline_path):
    bl = np.load(baseline_path)
    mismatches = []
    if not np.allclose(bl['overall_grid'], overall_grid, atol=1e-6):
        mismatches.append('ZPF grid')
    if not np.allclose(bl['pf_grid'], pf_grid, atol=1e-6):
        mismatches.append('PF grid')
    if not np.array_equal(bl['n_grid'], n_grid):
        mismatches.append('N grid')
    if mismatches:
        print(f'\n⚠️  VALIDATION FAILED against baseline — mismatched: {mismatches}.')
    else:
        print('\n✅ Validation OK — PF/ZPF/N grids match pre-instrumentation baseline exactly.')
else:
    print(f'\n⚠️  No baseline found at {baseline_path} — skipping validation.')

exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, 'exit_breakdown_full.csv')
exit_df.to_csv(csv_path, index=False)
print(f'Exit breakdown saved: {csv_path}')
exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']

print()
print('ZPF Grid (rows=SL, cols=TP):')
print('  SL\\TP ' + ''.join(f'  {t:4.1f}' for t in TP_VALS))
for sl in SL_VALS:
    print(f'  {sl:5.1f} ' + ''.join(f' {results[(sl,tp)][3]:5.3f}' for tp in TP_VALS))

print()
ranked_zpf  = sorted(results.items(), key=lambda x: x[1][3], reverse=True)
ranked_zshd = sorted(results.items(), key=lambda x: x[1][5], reverse=True)
ranked_cs   = sorted(results.items(), key=lambda x: x[1][7], reverse=True)

hdr2 = f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}  {"ConsScr":>8}'
print('Top 5 by ZPF:')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_zpf[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
raw_sl, raw_tp = ranked_zpf[0][0]
raw_row = exit_df[(exit_df['sl'] == raw_sl) & (exit_df['tp'] == raw_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={raw_sl} TP={raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')
print('\nHealthy-subset top-5 (EOD% <= 30):')
print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

print()
print('Top 5 by ZSh(D):')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_zshd[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

print()
print('Top 5 by Consistency Score:')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_cs[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

print()
(best_sl, best_tp) = ranked_zpf[0][0]
best_n, best_ndays, best_pf, best_zpf, best_shd, best_zshd, best_pct, best_cs = results[(best_sl, best_tp)]
print(f'Best combo by ZPF: SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={best_n:,}  Days={best_ndays}  PF={best_pf}  ZPF={best_zpf}  '
      f'Sh(D)={best_shd}  ZSh(D)={best_zshd}  ProfDays={best_pct}%  ConsScr={best_cs}')
