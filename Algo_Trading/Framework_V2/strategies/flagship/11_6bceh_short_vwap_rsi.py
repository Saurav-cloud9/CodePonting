import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
import glob
import os
from datetime import time as _time

# 6BCEH-Short + below-VWAP + RSI>threshold — the one lead worth chasing from the
# recovered claude.ai session (smc/03_backtest_results.md section 3): "6BCE+VWAP+
# RSI>54" was the only strategy there that ever crossed ZPF>1.0 with a real trade
# count — but only on an 8-stock CURATED universe (1.1232); the full 30-stock
# universe (this project's standard) only reached 0.9975, still just under
# viability. That result also predates this project's own NaN-guard, cutoff-
# formula, and charge-formula fixes, and used a narrower/coarser SL/TP grid — not
# directly comparable. This script reproduces it fresh, full 30-stock DS3, this
# project's own 10x9 grid, charges, cutoffs, and NaN guard.
#
# Base signal (identical to the locked 6BCEH-Short + VWAP, strategies/6bce/v1_vwap/):
#   Signal: close[i] == highest close of last 6 bars (i-5..i)
#   Filter 1: close[i] < VWAP[i]  (strict; ties excluded) — bearish context
#   Filter 2 (NEW): RSI(14, Wilder) on close, computed on bar i, > RSI_THRESH
#   Entry:  SHORT at open[i+1], same day
# Cutoff: live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
# Exit:   date change -> hour>=15 -> SL -> TP
#
# Two-step process (per Saurav's own plan, discussed pre-6BCEH/6BCEL detour):
#   Step A: fix SL/TP at the already-locked VWAP-only combo (4.5/3.0), sweep RSI
#           threshold 50-80 step 2 (same granularity as the recovered doc's own
#           FVG RSI sweep) to find the best threshold on THIS project's own data.
#   Step B: at that best threshold, re-run the FULL 90-combo SL/TP sweep — RSI
#           filtering removes a lot of trades and can shift the optimum, so the
#           VWAP-only locked combo isn't assumed to still be best.
#   Step C: healthy-subset diagnostic on the Step B grid (full rigor going in,
#           given this is the strongest lead in the recovered dataset).

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
WINDOW   = 6
RSI_PERIOD = 14
LAST_TOUCH_TIME   = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)

SL_VALS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
RSI_VALS = [50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80]

LOCKED_VWAP_ONLY_SL = 4.5
LOCKED_VWAP_ONLY_TP = 3.0


def zerodha_charge(entry, exit_px):
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def add_vwap(df):
    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3.0
    df['cum_tpv'] = df.groupby('date', sort=False).apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date', sort=False)['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol']
    return df


def add_rsi_wilder(df, period=RSI_PERIOD):
    """RSI(period, Wilder smoothing) on close — continuous series, no daily reset
    (standard RSI convention, matches how ma20/atr14 are computed in DS3)."""
    df = df.copy()
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0  # no losses in the lookback -> RSI=100
    return df


def load_stocks():
    stocks = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet'))):
        df = pd.read_parquet(f)
        df['datetime'] = pd.to_datetime(df['datetime'])
        if df['datetime'].dt.tz is not None:
            df['datetime'] = df['datetime'].dt.tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'volume', 'atr14']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['time'] = df['datetime'].dt.time
        df = add_vwap(df)
        df = add_rsi_wilder(df)
        stocks.append({
            'open':  df['open'].values,
            'high':  df['high'].values,
            'low':   df['low'].values,
            'close': df['close'].values,
            'atr14': df['atr14'].values,
            'vwap':  df['vwap'].values,
            'rsi':   df['rsi'].values,
            'hour':  df['hour'].values,
            'date':  df['date'].values,
            'time':  df['time'].values,
            'n':     len(df),
        })
    return stocks


def run_combo(stocks, sl_m, tp_m, rsi_thresh):
    all_pnl   = []
    all_zpnl  = []
    all_dates = []
    all_types = []

    for s in stocks:
        close = s['close']; high = s['high']; low  = s['low']
        open_ = s['open'];  atr  = s['atr14']; vwap = s['vwap']; rsi = s['rsi']
        hour  = s['hour'];  date = s['date'];  time_ = s['time'];  n = s['n']

        i = WINDOW - 1
        while i < n:
            if (np.isnan(atr[i]) or np.isnan(vwap[i]) or np.isnan(rsi[i])
                    or time_[i] > LAST_TOUCH_TIME):
                i += 1
                continue
            window = close[i - WINDOW + 1: i + 1]
            if np.any(np.isnan(window)) or close[i] < np.max(window):
                i += 1
                continue
            if not (close[i] < vwap[i]):
                i += 1
                continue
            if not (rsi[i] > rsi_thresh):
                i += 1
                continue
            ei = i + 1
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1
                continue
            entry_px = open_[ei]
            if np.isnan(entry_px):
                i += 1
                continue
            sl = entry_px + sl_m * atr[i]
            tp = entry_px - tp_m * atr[i]
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


# ── MAIN ──────────────────────────────────────────────────────────────────────
print('Strategy: 6BCEH-Short + below-VWAP + RSI(14,Wilder)>thresh')
print('Data: DS3 30 stocks 2015-2026\n')
print('Loading stocks (+ VWAP + RSI)...')
stocks = load_stocks()
print(f'Loaded {len(stocks)} stocks.\n')

print('=' * 80)
print(f'STEP A: RSI threshold sweep at LOCKED VWAP-only combo SL={LOCKED_VWAP_ONLY_SL}/TP={LOCKED_VWAP_ONLY_TP}')
print('=' * 80)
step_a = {}
for rt in RSI_VALS:
    pnl, zpnl, dates, types = run_combo(stocks, LOCKED_VWAP_ONLY_SL, LOCKED_VWAP_ONLY_TP, rt)
    n, pf, zpf, shd, zshd, pct = compute_metrics(pnl, zpnl, dates)
    step_a[rt] = (n, pf, zpf, shd, zshd, pct)
    print(f'  RSI>{rt:2d}  N={n:>7,}  PF={pf:6.3f}  ZPF={zpf:6.3f}  Sh(D)={shd:7.3f}  ZSh(D)={zshd:8.3f}  %ProfDays={pct:5.1f}')

best_rsi = max(step_a.items(), key=lambda x: x[1][2])[0]
print(f'\nBest RSI threshold by ZPF: RSI>{best_rsi}  (ZPF={step_a[best_rsi][2]:.3f})')

print()
print('=' * 80)
print(f'STEP B: full 90-combo SL/TP sweep at RSI>{best_rsi}')
print('=' * 80)
results = {}
exit_rows = []
for sl in SL_VALS:
    for tp in TP_VALS:
        pnl, zpnl, dates, types = run_combo(stocks, sl, tp, best_rsi)
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

exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, f'11_6bceh_short_vwap_rsi{best_rsi}_exit_breakdown.csv')
exit_df.to_csv(csv_path, index=False)
print(f'\nExit breakdown saved: {csv_path}')
exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']

ranked_zpf = sorted(results.items(), key=lambda x: x[1][2], reverse=True)
hdr2 = f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}'
print('\nTop 10 by ZPF (raw):')
print(hdr2)
for (sl, tp), (n, pf, zpf, shd, zshd, pct) in ranked_zpf[:10]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}')

healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
raw_sl, raw_tp = ranked_zpf[0][0]
raw_row = exit_df[(exit_df['sl'] == raw_sl) & (exit_df['tp'] == raw_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={raw_sl} TP={raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')
print('\nHealthy-subset top-10 (EOD% <= 30):')
print(healthy.head(10)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

print(f'\nViability check: need ZPF>1.0 AND ZSh(D)>0')
print(f'  Raw #1: SL={raw_sl}/{raw_tp}  ZPF={raw_row.zpf:.3f}  ZSh(D)={raw_row.zshd:.3f}  -> '
      f'{"PASS" if raw_row.zpf > 1.0 and raw_row.zshd > 0 else "FAIL"}')

print('\nDone.')
