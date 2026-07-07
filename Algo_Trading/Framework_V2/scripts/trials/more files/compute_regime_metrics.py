"""
Step 1 — Regime metrics measurement
Computes ER, MA20 run-length, VR per stock per day (2022-2025).
Rolling 20-trading-day window of 5-min bars for all three metrics.
Output: Framework_V2/outputs/h5/regime_metrics.csv
"""
import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
OUT_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5"
WINDOW   = 20   # trading days rolling window
VR_Q     = 6    # 6 × 5-min bars = 30-min return

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]


def _er(closes):
    if len(closes) < 2:
        return np.nan
    net  = abs(closes[-1] - closes[0])
    path = np.sum(np.abs(np.diff(closes)))
    return net / path if path > 0 else np.nan


def _run_length(closes, ma):
    sides = np.where(closes > ma, 1, np.where(closes < ma, -1, 0))
    if len(sides) == 0:
        return np.nan
    runs = []
    run  = 1
    for i in range(1, len(sides)):
        if sides[i] == sides[i - 1] and sides[i] != 0:
            run += 1
        else:
            if sides[i - 1] != 0:
                runs.append(run)
            run = 1
    if sides[-1] != 0:
        runs.append(run)
    return float(np.mean(runs)) if runs else np.nan


def _vr(closes, q):
    if len(closes) < q + 2:
        return np.nan
    lc  = np.log(closes.clip(min=1e-9))
    r1  = np.diff(lc)
    rq  = lc[q:] - lc[:-q]
    v1  = np.var(r1, ddof=1)
    vq  = np.var(rq, ddof=1)
    return vq / (q * v1) if v1 > 0 else np.nan


def process_stock(stock):
    path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df   = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date']     = df['datetime'].dt.date

    yr = df['datetime'].dt.year
    df = df[yr.between(2022, 2025)].copy().reset_index(drop=True)

    closes_arr = df['close'].values
    ma20_arr   = df['ma20'].values
    dates_arr  = df['date'].values

    # Build per-day start/end index maps
    dates_uniq = sorted(set(dates_arr))
    day_start  = {}
    day_end    = {}
    for i, d in enumerate(dates_arr):
        if d not in day_start:
            day_start[d] = i
        day_end[d] = i

    records = []
    for di, d in enumerate(dates_uniq):
        w0 = dates_uniq[max(0, di - WINDOW + 1)]
        i0 = day_start[w0]
        i1 = day_end[d]

        w_closes = closes_arr[i0:i1 + 1]
        w_ma20   = ma20_arr[i0:i1 + 1]

        valid = ~np.isnan(w_closes) & ~np.isnan(w_ma20)
        wc = w_closes[valid]
        wm = w_ma20[valid]

        records.append({
            'stock': stock,
            'date':  d,
            'ER':    round(_er(wc), 4)          if len(wc) > 1  else np.nan,
            'run_length_mean': round(_run_length(wc, wm), 2) if len(wc) > 1 else np.nan,
            'VR':    round(_vr(wc, VR_Q), 4)    if len(wc) > VR_Q + 1 else np.nan,
        })

    return pd.DataFrame(records)


# ── Run ────────────────────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, 'regime_metrics.csv')

all_dfs = []
for stock in STOCKS:
    print(f"  {stock}...", end=' ', flush=True)
    df = process_stock(stock)
    all_dfs.append(df)
    print(f"{len(df)} days")

result = pd.concat(all_dfs, ignore_index=True)
result.to_csv(out_path, index=False)

print(f"\nSaved: {out_path}")
print(f"Rows : {len(result):,}  ({result['stock'].nunique()} stocks × {result['date'].nunique()} unique dates)")
print(f"\nSample stats (all stocks, all years):")
print(result[['ER','run_length_mean','VR']].describe().round(3).to_string())