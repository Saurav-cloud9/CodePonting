import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
import glob
import os
from datetime import time as _time

# 6BCEL (6-Bar Close Extreme LOW) — SHORT — 90-combo SL/TP sweep
# Signal: close[i] == lowest close of last 6 bars (i-5 to i inclusive) — mirror-opposite
#         trigger of the locked 6BCEH-Short (#04/#05 here), same SHORT direction.
#         This is a genuine breakdown-continuation bet (price just made a fresh low,
#         bet the decline continues) — unlike 6BCEH-Short, which is a reversal bet
#         (price just made a fresh high, bet it fails). New, untested. Priority #1
#         per claude.ai review 2026-09-08 (aligns with the project's repeatedly-
#         confirmed structural short bias).
# Entry:  SHORT at open[i+1], same day
# Cutoff: live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
# Exit:   date change → hour>=15 → SL → TP
# Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF + Sh(D) reference
# Sharpe: daily (x sqrt(252))
# Output: 08_6bcel_short_sweep_cache.npz (full 90-cell grid) + 08_6bcel_short_exit_breakdown.csv
# No pre-instrumentation baseline exists for this variant (first time computing it) —
# nothing to validate against.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
WINDOW   = 6
LAST_TOUCH_TIME   = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_charge(entry, exit_px):
    """SHORT: entry=sell, exit=buy — STT on entry, stamp duty on exit."""
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
            if np.any(np.isnan(window)) or close[i] > np.min(window):
                i += 1
                continue
            ei = i + 1
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1
                continue
            entry_px   = open_[ei]
            if np.isnan(entry_px):  # DS3 data gap on the entry bar (e.g. INFY 2015-04-24)
                i += 1
                continue
            sl         = entry_px + sl_m  * atr[i]   # SHORT: stop above
            tp        = entry_px - tp_m * atr[i]     # SHORT: target below
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

            pnl  = entry_px - exit_px   # SHORT: profit if exit < entry
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


# ── MAIN ──────────────────────────────────────────────────────────────────────
print('Strategy: 6BCEL SHORT — close[i] == min(close[i-5..i])  (breakdown continuation)')
print('Entry: SHORT open[i+1], same day')
print('Cutoff: live-matching LAST_TOUCH<=14:45, ENTRY_CUTOFF<=14:50')
print('Data: DS3 30 stocks 2015-2026\n')
print('Loading stocks...')
stocks = load_stocks()
print(f'Loaded {len(stocks)} stocks. Running {len(SL_VALS)} x {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combos...\n')

results = {}
exit_rows = []
for sl in SL_VALS:
    for tp in TP_VALS:
        pnl, zpnl, dates, types = run_combo(stocks, sl, tp)
        n, pf, zpf, shd, zshd, pct = compute_metrics(pnl, zpnl, dates)
        results[(sl, tp)] = (n, pf, zpf, shd, zshd, pct)
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

overall_grid = np.zeros((len(SL_VALS), len(TP_VALS)))
pf_grid      = np.zeros((len(SL_VALS), len(TP_VALS)))
n_grid       = np.zeros((len(SL_VALS), len(TP_VALS)), dtype=int)
for si, sl in enumerate(SL_VALS):
    for ti, tp in enumerate(TP_VALS):
        n, pf, zpf, shd, zshd, pct = results[(sl, tp)]
        overall_grid[si, ti] = zpf; pf_grid[si, ti] = pf; n_grid[si, ti] = n
cache_path = os.path.join(SCRIPT_DIR, '08_6bcel_short_sweep_cache.npz')
np.savez(cache_path, overall_grid=overall_grid, pf_grid=pf_grid, n_grid=n_grid)
print(f'\nGrid cache saved: {cache_path}')

exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, '08_6bcel_short_exit_breakdown.csv')
exit_df.to_csv(csv_path, index=False)
print(f'Exit breakdown saved: {csv_path}')
exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']

print()
print('ZPF Grid (rows=SL, cols=TP):')
print('  SL\\TP ' + ''.join(f'  {t:4.1f}' for t in TP_VALS))
for sl in SL_VALS:
    print(f'  {sl:5.1f} ' + ''.join(f' {results[(sl,tp)][2]:5.3f}' for tp in TP_VALS))

ranked_zpf = sorted(results.items(), key=lambda x: x[1][2], reverse=True)
hdr2 = f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}'
print('\nTop 5 by ZPF:')
print(hdr2)
for (sl, tp), (n, pf, zpf, shd, zshd, pct) in ranked_zpf[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}')

healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
raw_sl, raw_tp = ranked_zpf[0][0]
raw_row = exit_df[(exit_df['sl'] == raw_sl) & (exit_df['tp'] == raw_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={raw_sl} TP={raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')
print('\nHealthy-subset top-5 (EOD% <= 30):')
print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

print('\nDone.')
