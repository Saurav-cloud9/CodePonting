"""
SL x TP grid sweep — SMC Liquidity Sweep — V3: Swing HIGH + LONG entry (contrarian)
30 stocks · DS3 parquets, 2015-02-02 through last month-end (DS3 grows monthly —
current/in-progress month excluded; verify actual max date before assuming stale)

Part of the 4-variant matrix (2026-09-07): {swing low, swing high} x {long, short}.
Completes the matrix — swing HIGH trigger (same as V2) but CONTRARIAN entry: LONG
instead of the intuitive SHORT. Betting AGAINST the reversal-down signal, mirroring
ma_short_flip's own role in the flagship family (contrarian on the bearish touch) —
ma_short_flip was decisively RULED OUT (worse on every metric), so this is the cell
predicted to be the weakest of the 4 by the flagship-family parallel discussed
2026-09-07, not the one expected to show promise.

Signal (conditions 1-4 identical to V2 — only condition 5's direction differs):
  1. Swing High — N=2 fractal, confirmed at bar j+2.
  2. Distance   — sweep within 50 bars of the swing high's confirmation bar.
  3. Sweep      — wick rises ABOVE swing_high_level, candle CLOSES back BELOW it.
  4. Confirm    — the very next candle also closes below swing_high_level.
  5. Entry      — LONG (not short) at the open of the candle after confirmation.

Cutoffs (backtesting_rules.md §2): LAST_SWEEP_TIME=14:40, ENTRY_CUTOFF_TIME=14:50.
Exit: standard project priority — date change -> hour>=15 -> SL -> TP, LONG-mirrored
SL/TP: ATR-based, sized off the SWEEP candle's own ATR14 (the signal-trigger bar)
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF / Sh(D) reference
Exit-mix: SL%/TP%/EOD+%/EOD-% tracked per combo (backtesting_rules.md §9, mandatory)
"""
import sys, io, glob, os
from datetime import time as _time
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
N_FRACTAL = 2
MAX_DISTANCE = 50
LAST_SWEEP_TIME = _time(14, 40)
ENTRY_CUTOFF_TIME = _time(14, 50)

SL_VALS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_charge_long(entry, exit_px):
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = exit_px * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = entry * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def find_swing_high_tracker(high, n):
    is_swing = np.zeros(n, dtype=bool)
    for j in range(N_FRACTAL, n - N_FRACTAL):
        window = high[j - N_FRACTAL: j + N_FRACTAL + 1]
        if np.isnan(window).any():
            continue
        if high[j] == window.max() and (window == high[j]).sum() == 1:
            is_swing[j] = True

    level = np.full(n, np.nan)
    confirm_idx = np.full(n, -1, dtype=int)
    last_level, last_confirm = np.nan, -1
    for i in range(n):
        confirm_at = i - N_FRACTAL
        if confirm_at >= 0 and is_swing[confirm_at]:
            last_level = high[confirm_at]
            last_confirm = i
        level[i] = last_level
        confirm_idx[i] = last_confirm
    return level, confirm_idx


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
        n = len(df)
        level, confirm_idx = find_swing_high_tracker(df['high'].values, n)
        stocks.append({
            'symbol': os.path.basename(f).replace('.parquet', ''),
            'open': df['open'].values, 'high': df['high'].values,
            'low': df['low'].values, 'close': df['close'].values,
            'atr14': df['atr14'].values, 'hour': df['hour'].values,
            'date': df['date'].values, 'time': df['time'].values,
            'swing_level': level, 'swing_confirm_idx': confirm_idx,
            'n': n,
        })
    return stocks


def run_combo(stocks, sl_m, tp_m):
    all_pnl, all_zpnl, all_dates, all_types = [], [], [], []

    for s in stocks:
        close, high, low, open_ = s['close'], s['high'], s['low'], s['open']
        atr, hour, date, time_ = s['atr14'], s['hour'], s['date'], s['time']
        swing_level, swing_confirm_idx = s['swing_level'], s['swing_confirm_idx']
        n = s['n']

        i = N_FRACTAL
        while i < n:
            lvl = swing_level[i]
            cidx = swing_confirm_idx[i]
            if (np.isnan(lvl) or np.isnan(atr[i]) or cidx < 0
                    or (i - cidx) > MAX_DISTANCE or time_[i] > LAST_SWEEP_TIME):
                i += 1; continue
            # Conditions 1-4 identical to V2 (swing high, distance, sweep, confirm)
            if not (high[i] > lvl and close[i] < lvl):
                i += 1; continue
            ci = i + 1
            if ci >= n or date[ci] != date[i] or close[ci] >= lvl:
                i += 1; continue
            ei = ci + 1
            if ei >= n or date[ei] != date[ci] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1; continue

            # Condition 5 — CONTRARIAN: LONG instead of SHORT, same trigger
            entry_px = open_[ei]
            sig_atr = atr[i]
            sl = entry_px - sl_m * sig_atr   # LONG: stop below
            tp = entry_px + tp_m * sig_atr   # LONG: target above
            trade_date = date[ci]
            etype = 'EOD'; exit_px = None
            k = ei
            for k in range(ei, n):
                if date[k] != trade_date:
                    exit_px = close[k - 1]; etype = 'EOD'; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; etype = 'EOD'; break
                if low[k] <= sl:
                    exit_px = sl; etype = 'SL'; break
                if high[k] >= tp:
                    exit_px = tp; etype = 'TP'; break
            else:
                exit_px = close[n - 1]; etype = 'EOD'

            pnl = exit_px - entry_px   # LONG: profit if exit > entry
            zpnl = pnl - zerodha_charge_long(entry_px, exit_px)
            all_pnl.append(pnl); all_zpnl.append(zpnl)
            all_dates.append(exit_px and date[k]); all_types.append(etype)
            i = k + 1

    return all_pnl, all_zpnl, all_dates, all_types


def compute_metrics(pnl_list, zpnl_list, date_list):
    if not pnl_list:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0
    pnl = np.array(pnl_list); zpnl = np.array(zpnl_list)
    gp = pnl[pnl > 0].sum(); gl = abs(pnl[pnl < 0].sum())
    zgp = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
    pf = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zgp / zgl, 3) if zgl > 0 else 0.0
    daily = (pd.DataFrame({'pnl': pnl, 'zpnl': zpnl, 'date': date_list})
               .groupby('date')[['pnl', 'zpnl']].sum())
    shd = round((daily['pnl'].mean() / daily['pnl'].std()) * np.sqrt(252), 3) if daily['pnl'].std() > 0 else 0.0
    zshd = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0
    pct = round((daily['zpnl'] > 0).sum() / len(daily) * 100, 1)
    return len(pnl), pf, zpf, shd, zshd, pct


if __name__ == '__main__':
    print('Strategy: SMC Liquidity Sweep — V3: Swing HIGH + LONG entry (contrarian)')
    print('Entry: LONG open[entry_bar], sweep -> confirm -> entry (3-candle chain)')
    print(f'Cutoffs: LAST_SWEEP_TIME<={LAST_SWEEP_TIME}, ENTRY_CUTOFF<={ENTRY_CUTOFF_TIME}')
    print('Data: DS3 30 stocks, 2015-02-02 through last month-end\n')
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
            sl_pct = round(float((types_arr == 'SL').sum()) / ntot * 100, 1) if ntot else 0.0
            tp_pct = round(float((types_arr == 'TP').sum()) / ntot * 100, 1) if ntot else 0.0
            eod_mask = types_arr == 'EOD'
            eod_plus_pct = round(float((eod_mask & (pnl_arr > 0)).sum()) / ntot * 100, 1) if ntot else 0.0
            eod_minus_pct = round(float((eod_mask & (pnl_arr <= 0)).sum()) / ntot * 100, 1) if ntot else 0.0
            exit_rows.append({'sl': sl, 'tp': tp, 'n': ntot, 'pf': pf, 'zpf': zpf,
                               'shd': shd, 'zshd': zshd, 'sl_hit_pct': sl_pct, 'tp_hit_pct': tp_pct,
                               'eod_plus_pct': eod_plus_pct, 'eod_minus_pct': eod_minus_pct})
            print(f'  SL={sl:.1f} TP={tp:.1f}  N={n:,}  PF={pf:.3f}  ZPF={zpf:.3f}  Sh(D)={shd:.3f}  ZSh(D)={zshd:.3f}  '
                  f'SL%={sl_pct:.1f} TP%={tp_pct:.1f} EOD+%={eod_plus_pct:.1f} EOD-%={eod_minus_pct:.1f}')

    exit_df = pd.DataFrame(exit_rows)
    exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']
    csv_path = os.path.join(SCRIPT_DIR, '04_liquidity_v3_swinghigh_long_exit_breakdown.csv')
    exit_df.to_csv(csv_path, index=False)
    print(f'\nExit breakdown saved: {csv_path}')

    print()
    print('ZPF Grid (rows=SL, cols=TP):')
    print('  SL\\TP ' + ''.join(f'  {t:4.1f}' for t in TP_VALS))
    for sl in SL_VALS:
        print(f'  {sl:5.1f} ' + ''.join(f' {results[(sl,tp)][2]:5.3f}' for tp in TP_VALS))

    ranked_zpf = sorted(results.items(), key=lambda x: x[1][2], reverse=True)
    print('\nTop 5 by ZPF:')
    print(f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}')
    for (sl, tp), (n, pf, zpf, shd, zshd, pct) in ranked_zpf[:5]:
        print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}')

    healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
    raw_sl, raw_tp = ranked_zpf[0][0]
    raw_row = exit_df[(exit_df['sl'] == raw_sl) & (exit_df['tp'] == raw_tp)].iloc[0]
    print(f'\nRaw #1 by ZPF: SL={raw_sl} TP={raw_tp}  ZPF={raw_row.zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
          f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')
    print('\nHealthy-subset top-5 (EOD% <= 30):')
    if len(healthy) > 0:
        print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))
    else:
        print('  (none — every combo has EOD% > 30)')
