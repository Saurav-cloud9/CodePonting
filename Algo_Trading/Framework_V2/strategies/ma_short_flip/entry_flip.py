"""
MA-short "flip" hypothesis test — SAME touch condition as ma_short/v1
(high>=MA20, open<MA20, close<MA20 — the bearish-looking rejection candle),
but entering LONG instead of SHORT, on the theory that the rejection is a
fakeout/trap (SMC "inducement"-adjacent idea) rather than genuine continuation.

Motivated by: all 8 alpha/p-value checks on the SHORT version (raw + healthy
combos, ma_short v1/v2_vwap, 6bce v0/v1_vwap) showed statistically significant
NEGATIVE alpha (p<0.0001) vs NIFTY50 daily return — real, consistent
information beyond market-beta exposure, just possibly pointing the wrong way.

RESULT (2026-09-04): hypothesis NOT supported at this combo — see findings.md.
Kept as a single-combo sanity check, not a full 90-combo sweep — the result
was decisive enough (worse than the SHORT version, not better) that the full
sweep wasn't run. Ruled out as a direction to pursue further.

Cutoff : live-matching (backtesting_rules.md) — LAST_TOUCH_TIME=14:45, ENTRY_CUTOFF_TIME=14:50
"""
import pandas as pd, numpy as np, glob
from datetime import time as _time

DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
EOD_HOUR = 15
LAST_TOUCH_TIME = _time(14, 45)
ENTRY_CUTOFF_TIME = _time(14, 50)
SL_M, TP_M = 2.0, 4.5  # same as live-deployed SHORT combo, for direct comparison


def zerodha_long(entry, exit_px):
    """Full Zerodha intraday LONG charges: entry=buy side, exit=sell side —
    mirror of the SHORT formula used throughout this project (STT/stamp swap sides)."""
    brok = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt = exit_px * 0.00025        # STT on sell side (exit)
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = entry * 0.000003       # stamp duty on buy side (entry)
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def run_backtest(sl_m=SL_M, tp_m=TP_M):
    files = sorted(glob.glob(DATA_DIR + '/*.parquet'))
    rows = []
    for f in files:
        df = pd.read_parquet(f)
        df['datetime'] = pd.to_datetime(df['datetime'])
        if df['datetime'].dt.tz is not None:
            df['datetime'] = df['datetime'].dt.tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['time'] = df['datetime'].dt.time
        high = df['high'].values; low = df['low'].values; open_ = df['open'].values; close = df['close'].values
        ma20 = df['ma20'].values; atr = df['atr14'].values; hour = df['hour'].values
        date = df['date'].values; time_ = df['time'].values
        n = len(df)
        i = 0
        while i < n:
            if np.isnan(ma20[i]) or np.isnan(atr[i]):
                i += 1; continue
            # SAME touch condition as MA-short (bearish-looking rejection candle)
            if high[i] >= ma20[i] and open_[i] < ma20[i] and close[i] < ma20[i] and time_[i] <= LAST_TOUCH_TIME:
                ei = i + 1
                if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                    i += 1; continue
                entry = open_[ei]
                sl = entry - sl_m * atr[i]   # LONG: stop BELOW entry
                tp = entry + tp_m * atr[i]   # LONG: target ABOVE entry
                trade_date = date[i]
                k = ei; etype = 'EOD'
                for k in range(ei, n):
                    if date[k] != trade_date:
                        exit_px = close[k - 1]; etype = 'EOD'; break
                    if hour[k] >= EOD_HOUR:
                        exit_px = open_[k]; etype = 'EOD'; break
                    if low[k] <= sl:
                        exit_px = sl; etype = 'SL'; break
                    if high[k] >= tp:
                        exit_px = tp; etype = 'TP'; break
                pnl = exit_px - entry   # LONG: profit if exit > entry
                zpnl = pnl - zerodha_long(entry, exit_px)
                rows.append({'exit_type': etype, 'pnl': pnl, 'zpnl': zpnl, 'date': date[ei]})
                i = k + 1
            else:
                i += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    rdf = run_backtest()
    n = len(rdf)
    gp = rdf[rdf['pnl'] > 0]['pnl'].sum(); gl = -rdf[rdf['pnl'] < 0]['pnl'].sum()
    pf = gp / gl if gl > 0 else 0
    zgp = rdf[rdf['zpnl'] > 0]['zpnl'].sum(); zgl = -rdf[rdf['zpnl'] <= 0]['zpnl'].sum()
    zpf = zgp / zgl if zgl > 0 else 0
    print(f'LONG-flip on MA-short touch, SL={SL_M} TP={TP_M}')
    print(f'N={n:,}  PF={pf:.3f}  ZPF={zpf:.3f}')
    print(rdf['exit_type'].value_counts(normalize=True).round(3) * 100)
