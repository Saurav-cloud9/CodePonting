"""
SL x TP grid sweep — ma_long_flip + below-VWAP filter (SHORT on the bullish-bounce candle,
confirmed only in a below-VWAP context)
30 stocks · DS3 (2015-02-02 to 2026-08-31)
Signal : ma_bounce's clean touch (low<=MA20, open>MA20, close>MA20) AND close[i]<VWAP[i] —
         locked 2026-09-05 after comparing below vs above across 3 SL/TP combos: below won
         decisively on every metric (see vwap_decision.md).
Cutoff : live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
Logic  : single-pass (i = k+1 after each trade) — position guard intact
Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF / Sh(D) reference
Exit-mix: SL-hit%/TP-hit%/EOD+%/EOD-% tracked per combo from the start (backtesting_rules.md
         mandatory diagnostic).
Output : sweep_cache_v1_vwap.npz (full 90-cell grid) + exit_breakdown_full.csv (90 rows).
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
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['time'] = df['datetime'].dt.time
    df['year'] = df['datetime'].dt.year
    tp = (df['high'] + df['low'] + df['close']) / 3
    df['cum_tpv'] = df.groupby('date').apply(
        lambda g: (tp.loc[g.index] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol']
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tp_m):
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14 = arrays['ma20'], arrays['atr14']
    hour, date, time_, year = arrays['hour'], arrays['date'], arrays['time'], arrays['year']
    vwap = arrays['vwap']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []; type_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]) or np.isnan(vwap[i]):
            i += 1; continue
        # ma_long_flip: ma_bounce touch + below-VWAP context, SHORT (flip), live-matching cutoff
        if (low[i] <= ma20[i] and open_[i] > ma20[i] and
                close[i] > ma20[i] and close[i] < vwap[i] and time_[i] <= LAST_TOUCH_TIME):
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


# ── Load ───────────────────────────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks (+VWAP)...')
stock_arrays = []
for f in files:
    df = load(f)
    stock_arrays.append({
        'high': df['high'].values, 'low': df['low'].values,
        'open_': df['open'].values, 'close': df['close'].values,
        'ma20': df['ma20'].values, 'atr14': df['atr14'].values,
        'vwap': df['vwap'].values,
        'hour': df['hour'].values, 'date': df['date'].values,
        'time': df['time'].values, 'year': df['year'].values, 'n': len(df),
    })
print(f'Loaded. Running {len(SL_VALS)} x {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combo grid sweep...')

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

cache_path = os.path.join(SCRIPT_DIR, 'sweep_cache_v1_vwap.npz')
np.savez(cache_path, overall_grid=zpf_grid, pf_grid=pf_grid, shd_grid=shd_grid, zshd_grid=zshd_grid, n_grid=n_grid)
print(f'\nGrid cache saved: {cache_path}')

exit_df = pd.DataFrame(exit_rows)
csv_path = os.path.join(SCRIPT_DIR, 'exit_breakdown_full.csv')
exit_df.to_csv(csv_path, index=False)
print(f'Exit breakdown saved: {csv_path}')
exit_df['eod_pct'] = exit_df['eod_plus_pct'] + exit_df['eod_minus_pct']

flat_zpf = sorted(
    [(zpf_grid[si, ti], pf_grid[si, ti], SL_VALS[si], TP_VALS[ti], n_grid[si, ti])
     for si in range(len(SL_VALS)) for ti in range(len(TP_VALS))],
    reverse=True
)
best_zpf, best_pf, best_sl, best_tp, best_n = flat_zpf[0]
raw_row = exit_df[(exit_df['sl'] == best_sl) & (exit_df['tp'] == best_tp)].iloc[0]
print(f'\nRaw #1 by ZPF: SL={best_sl} TP={best_tp}  N={best_n:,}  ZPF={best_zpf:.3f}  EOD%={raw_row.eod_pct:.1f}  '
      f'{"SUSPECT (EOD%>30)" if raw_row.eod_pct > 30 else "OK"}')

healthy = exit_df[exit_df['eod_pct'] <= 30.0].sort_values('zpf', ascending=False)
print('\nHealthy-subset top-5 (EOD% <= 30), CAREFULLY selected from actual data (not assumed):')
print(healthy.head(5)[['sl', 'tp', 'n', 'pf', 'zpf', 'shd', 'zshd', 'eod_pct']].to_string(index=False))

print('\nDone.')
