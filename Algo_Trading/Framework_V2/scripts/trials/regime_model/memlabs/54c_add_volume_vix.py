"""
54c_add_volume_vix.py — adds two new candidate regime features to the existing
54c_daily_regime_features.csv / 54c_trade_log_with_features.csv, additive (existing
10 columns untouched):

  volume_surge     — each stock's own daily total volume / its own trailing 20-day
                      average volume, basket-averaged across the 30 stocks, shifted 1
                      day (no lookahead). Normalized (not raw volume) because raw
                      volume drifts over an 11-year sample (participation growth,
                      float changes) -- non-stationary, would confound with time
                      itself rather than measure "unusual activity."
  india_vix_level  — India VIX daily close, shifted 1 day (prior-close convention,
                      matching nifty_trend/basket_trend/etc.). A market-wide implied-
                      volatility ("fear gauge") state variable, theoretically distinct
                      from realized-vol/dispersion (forward-looking expectation vs
                      backward-looking realized measure) and the most canonical
                      "regime" indicator in finance.
"""
import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np

DS3_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
VIX_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/daily/INDIA_VIX.parquet'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── volume_surge ────────────────────────────────────────────────────────────
print('Building volume_surge (per-stock daily volume / own trailing 20d avg, basket-averaged)...')
vol_cols = {}
for f in sorted(glob.glob(os.path.join(DS3_DIR, '*.parquet'))):
    symbol = os.path.splitext(os.path.basename(f))[0]
    d = pd.read_parquet(f, columns=['datetime', 'volume'])
    d['datetime'] = pd.to_datetime(d['datetime'])
    if d['datetime'].dt.tz is not None:
        d['datetime'] = d['datetime'].dt.tz_localize(None)
    d['date'] = d['datetime'].dt.date
    vol_cols[symbol] = d.groupby('date')['volume'].sum()

daily_vol_wide = pd.concat(vol_cols, axis=1)
daily_vol_wide.index = pd.to_datetime(daily_vol_wide.index)
daily_vol_wide = daily_vol_wide.sort_index()          # §16 rule -- mandatory after concat

trailing_20d_avg = daily_vol_wide.rolling(20).mean()
surge_ratio = daily_vol_wide / trailing_20d_avg        # per-stock, per-day
volume_surge = surge_ratio.mean(axis=1, skipna=True)   # basket-average across 30 stocks

volume_surge_df = pd.DataFrame({
    'date': daily_vol_wide.index.date,
    'volume_surge': volume_surge.shift(1).values,      # lag 1 day, no lookahead
})

# ── india_vix_level ──────────────────────────────────────────────────────────
print('Building india_vix_level (prior-close VIX)...')
vix = pd.read_parquet(VIX_PATH)
vix['date'] = pd.to_datetime(vix['datetime']).dt.date
vix = vix.sort_values('datetime')
n_dup = vix['date'].duplicated(keep=False).sum()
if n_dup:
    print(f'  NOTE: {n_dup} rows share a date with another row (INDIA_VIX.parquet data-quality '
          f'issue, 3 dates in 2015 have two intraday snapshots instead of one clean daily close) '
          f'-- deduping via last-timestamp-of-day, matching this project\'s DS3 close_wide convention.')
vix = vix.groupby('date', as_index=False).last().sort_values('date').reset_index(drop=True)
vix_df = pd.DataFrame({
    'date': vix['date'],
    'india_vix_level': vix['close'].shift(1).values,   # prior close, same convention as trend/dispersion
})

# ── merge into the existing daily reference table ───────────────────────────
daily_ref = pd.read_csv(os.path.join(SCRIPT_DIR, '54c_daily_regime_features.csv'))
daily_ref['date'] = pd.to_datetime(daily_ref['date']).dt.date
daily_ref = daily_ref.merge(volume_surge_df, on='date', how='left').merge(vix_df, on='date', how='left')
daily_ref.to_csv(os.path.join(SCRIPT_DIR, '54c_daily_regime_features.csv'), index=False)
print(f'54c_daily_regime_features.csv: now {daily_ref.shape[1]-1} features, {len(daily_ref)} days')

# ── merge into the trade-log-with-features file ─────────────────────────────
tl = pd.read_csv(os.path.join(SCRIPT_DIR, '54c_trade_log_with_features.csv'))
tl['date'] = pd.to_datetime(tl['date']).dt.date
tl = tl.merge(volume_surge_df, on='date', how='left').merge(vix_df, on='date', how='left')
tl.to_csv(os.path.join(SCRIPT_DIR, '54c_trade_log_with_features.csv'), index=False)
print(f'54c_trade_log_with_features.csv: {tl.shape[1]} columns, {len(tl)} trades')

print('\nSample (last 5 days with both new features non-null):')
print(daily_ref.dropna(subset=['volume_surge', 'india_vix_level']).tail(5)[['date', 'volume_surge', 'india_vix_level']].to_string(index=False))
