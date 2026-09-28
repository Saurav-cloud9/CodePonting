"""
Step 54c (file 2/3) — build candidate market-wide regime features + join onto the trade log.

Per 54_...baseline.md §4 design spec: market-wide scope only (NIFTY/basket), computed
as-of-prior-close for the daily features (no lookahead), same-day-but-pre-signal for
gap_pct and the intraday pseudo-index. Full 10-feature candidate list built here for
reference; the actual 54c screen starts minimal (NIFTY trend 10d + basket dispersion),
per Saurav's call.

Outputs:
  54c_daily_regime_features.csv   — one row per trading day, all features (reference table)
  54c_trade_log_with_features.csv — 54c_trade_log.csv + each trade's correctly-lagged
                                     day's features joined on
"""
import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np

NIFTY_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet'
DS3_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_LOG = os.path.join(SCRIPT_DIR, '54c_trade_log.csv')

# ── NIFTY daily features ──────────────────────────────────────────────────────
nifty = pd.read_parquet(NIFTY_PATH)
nifty['date'] = pd.to_datetime(nifty['datetime']).dt.date
nifty = nifty.sort_values('date').reset_index(drop=True)
nifty['ret_pct'] = nifty['close'].pct_change() * 100
nifty['gap_pct'] = (nifty['open'] / nifty['close'].shift(1) - 1) * 100          # same-day, pre-signal
nifty['nifty_trend_5d']  = nifty['close'].pct_change(5) * 100                    # as-of TODAY's close
nifty['nifty_trend_10d'] = nifty['close'].pct_change(10) * 100
nifty['realized_vol_nifty_10d'] = nifty['ret_pct'].rolling(10).std()
ma50 = nifty['close'].rolling(50).mean()
nifty['dist_from_ma50_nifty'] = (nifty['close'] / ma50 - 1) * 100
# shift the "as-of-today's-close" columns by 1 so they represent PRIOR close, usable at
# tomorrow's signal without lookahead. gap_pct is already same-day-legit as computed.
LAG_COLS_NIFTY = ['nifty_trend_5d', 'nifty_trend_10d', 'realized_vol_nifty_10d', 'dist_from_ma50_nifty']
for c in LAG_COLS_NIFTY:
    nifty[c] = nifty[c].shift(1)

nifty_daily = nifty[['date', 'gap_pct'] + LAG_COLS_NIFTY].copy()

# ── Basket (30-stock) daily features ──────────────────────────────────────────
print('Loading 30-stock daily closes for basket features...')
close_cols = {}
for f in sorted(glob.glob(os.path.join(DS3_DIR, '*.parquet'))):
    symbol = os.path.splitext(os.path.basename(f))[0]
    d = pd.read_parquet(f, columns=['datetime', 'close'])
    d['datetime'] = pd.to_datetime(d['datetime'])
    if d['datetime'].dt.tz is not None:
        d['datetime'] = d['datetime'].dt.tz_localize(None)
    d['date'] = d['datetime'].dt.date
    close_cols[symbol] = d.groupby('date')['close'].last()
close_wide = pd.concat(close_cols, axis=1).mask(lambda x: x <= 0)   # date x 30 stocks
close_wide.index = pd.to_datetime(close_wide.index)
close_wide = close_wide.sort_index()      # §16 fix — concat's date-object index isn't
                                           # guaranteed sorted; unsorted breaks pct_change
ret_wide = close_wide.pct_change() * 100                             # date x 30 stocks, daily %

basket_trend_5d  = (close_wide.pct_change(5)  * 100).mean(axis=1, skipna=True)
basket_trend_10d = (close_wide.pct_change(10) * 100).mean(axis=1, skipna=True)
dispersion       = ret_wide.std(axis=1, skipna=True)
breadth          = (ret_wide > 0).mean(axis=1, skipna=True) * 100
realized_vol_basket_10d = ret_wide.mean(axis=1, skipna=True).rolling(10).std()

basket_daily = pd.DataFrame({
    'date': close_wide.index.date,   # back to plain date objects, matching nifty_daily's dtype
    'basket_trend_5d': basket_trend_5d.values,
    'basket_trend_10d': basket_trend_10d.values,
    'dispersion': dispersion.values,
    'breadth': breadth.values,
    'realized_vol_basket_10d': realized_vol_basket_10d.values,
}).reset_index(drop=True)
# shift ALL basket features by 1 -> prior-day values, no lookahead
for c in ['basket_trend_5d', 'basket_trend_10d', 'dispersion', 'breadth', 'realized_vol_basket_10d']:
    basket_daily[c] = basket_daily[c].shift(1)

# ── Basket intraday pseudo-index (5-min, substitute for missing NIFTY intraday data) ──
print('Building basket 5-min intraday pseudo-index (this is the slow part)...')
intraday_cols = {}
for f in sorted(glob.glob(os.path.join(DS3_DIR, '*.parquet'))):
    symbol = os.path.splitext(os.path.basename(f))[0]
    d = pd.read_parquet(f, columns=['datetime', 'close'])
    d['datetime'] = pd.to_datetime(d['datetime'])
    if d['datetime'].dt.tz is not None:
        d['datetime'] = d['datetime'].dt.tz_localize(None)
    d['date'] = d['datetime'].dt.date
    d = d[d['close'] > 0]
    day_open = d.groupby('date')['close'].transform('first')
    d['intraday_move_pct'] = (d['close'] / day_open - 1) * 100   # cumulative move since today's open
    intraday_cols[symbol] = d.set_index('datetime')['intraday_move_pct']
intraday_wide = pd.concat(intraday_cols, axis=1).sort_index()   # §16 fix
basket_intraday = intraday_wide.mean(axis=1, skipna=True).rename('basket_intraday_move_pct').reset_index()
basket_intraday.columns = ['datetime', 'basket_intraday_move_pct']
basket_intraday = basket_intraday.sort_values('datetime').reset_index(drop=True)

# ── Merge daily reference table ───────────────────────────────────────────────
daily = nifty_daily.merge(basket_daily, on='date', how='outer').sort_values('date').reset_index(drop=True)
daily_out = os.path.join(SCRIPT_DIR, '54c_daily_regime_features.csv')
daily.to_csv(daily_out, index=False)
print(f'\nDaily regime features saved: {daily_out}  ({len(daily)} days)')
print(daily.describe().to_string())

# ── Join onto the trade log ───────────────────────────────────────────────────
trades = pd.read_csv(TRADE_LOG, parse_dates=['signal_dt', 'entry_dt'])
trades['date'] = trades['signal_dt'].dt.date

merged = trades.merge(daily, on='date', how='left')

# day_of_week / time_of_day_bucket — structural, from signal_dt itself, no price data
merged['day_of_week'] = merged['signal_dt'].dt.day_name()
bucket_edges = [pd.Timestamp('09:15').time(), pd.Timestamp('11:00').time(),
                pd.Timestamp('13:00').time(), pd.Timestamp('15:30').time()]
def bucket(t):
    if t < bucket_edges[1]:
        return 'morning'
    elif t < bucket_edges[2]:
        return 'midday'
    return 'afternoon'
merged['time_of_day_bucket'] = merged['signal_dt'].dt.time.map(bucket)

# basket intraday pseudo-index: as-of-or-before the SIGNAL bar (merge_asof, backward)
merged = merged.sort_values('signal_dt')
merged['signal_dt'] = merged['signal_dt'].astype('datetime64[ns]')
basket_intraday['datetime'] = basket_intraday['datetime'].astype('datetime64[ns]')
merged = pd.merge_asof(merged, basket_intraday, left_on='signal_dt', right_on='datetime',
                        direction='backward')
merged = merged.drop(columns=['datetime'])

out = os.path.join(SCRIPT_DIR, '54c_trade_log_with_features.csv')
merged.to_csv(out, index=False)
print(f'\nTrade log + features saved: {out}  ({len(merged)} trades)')
print(f'NaN counts (warmup periods expected):')
print(merged.isna().sum().to_string())

print('\nDone.')
