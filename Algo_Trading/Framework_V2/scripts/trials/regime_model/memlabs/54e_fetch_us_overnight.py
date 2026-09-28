"""
54e_fetch_us_overnight.py — builds `us_overnight_return`: the most recently completed
US session's (S&P 500, ^GSPC) close-to-close return, as known before that Indian
trading day's open.

Alignment logic (the part that actually matters here): for each India trading date T,
find the most recent US trading date STRICTLY BEFORE T (not just T-1 calendar day --
weekends/holidays on either side make simple date-shifting wrong) and use THAT
session's close-to-close return. This directly answers "what does a trader already
know by T's 9:15am open" -- no additional shift(1) needed on top of this (a further
shift would double-lag it).

Outputs: adds `us_overnight_return` to 54c_daily_regime_features.csv and
54c_trade_log_with_features.csv (additive, existing columns untouched).
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
import yfinance as yf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── fetch S&P 500 ────────────────────────────────────────────────────────────
print('Fetching ^GSPC (S&P 500) daily data...')
sp500 = yf.download('^GSPC', start='2014-12-01', end='2026-09-19', progress=False)
sp500.columns = sp500.columns.get_level_values(0)  # flatten multiindex from yfinance
sp500 = sp500.reset_index()[['Date', 'Close']].rename(columns={'Date': 'us_date', 'Close': 'us_close'})
sp500['us_date'] = pd.to_datetime(sp500['us_date'])
sp500 = sp500.sort_values('us_date').reset_index(drop=True)
sp500['us_ret_pct'] = sp500['us_close'].pct_change() * 100
print(f'  {len(sp500)} US trading days, {sp500["us_date"].min().date()} -> {sp500["us_date"].max().date()}')

# ── India trading calendar (from the existing daily feature reference table) ──
daily_ref = pd.read_csv(os.path.join(SCRIPT_DIR, '54c_daily_regime_features.csv'))
daily_ref['date'] = pd.to_datetime(daily_ref['date'])
india_dates = daily_ref[['date']].drop_duplicates().sort_values('date').reset_index(drop=True)
print(f'  {len(india_dates)} India trading days, {india_dates["date"].min().date()} -> {india_dates["date"].max().date()}')

# ── for each India date, find the most recent US date STRICTLY BEFORE it ──────
india_dates['date'] = india_dates['date'].astype('datetime64[ns]')
sp500['us_date'] = sp500['us_date'].astype('datetime64[ns]')
merged = pd.merge_asof(india_dates, sp500, left_on='date', right_on='us_date',
                        direction='backward', allow_exact_matches=False)
merged['us_overnight_return'] = merged['us_ret_pct']

# sanity check on alignment: print a few rows
print('\nSample alignment (India date -> most recent prior US date used):')
print(merged[['date', 'us_date', 'us_overnight_return']].head(5).to_string(index=False))
print('...')
print(merged[['date', 'us_date', 'us_overnight_return']].tail(5).to_string(index=False))

out = merged[['date', 'us_overnight_return']].copy()
out['date'] = out['date'].dt.date

# ── merge into daily reference table ───────────────────────────────────────
daily_ref['date'] = daily_ref['date'].dt.date
daily_ref = daily_ref.merge(out, on='date', how='left')
daily_ref.to_csv(os.path.join(SCRIPT_DIR, '54c_daily_regime_features.csv'), index=False)
print(f'\n54c_daily_regime_features.csv: now {daily_ref.shape[1]-1} features, {len(daily_ref)} days, '
      f'{daily_ref["us_overnight_return"].isna().sum()} NaN (warmup)')

# ── merge into trade-log-with-features ─────────────────────────────────────
tl = pd.read_csv(os.path.join(SCRIPT_DIR, '54c_trade_log_with_features.csv'))
tl['date'] = pd.to_datetime(tl['date']).dt.date
before_n = len(tl)
tl = tl.merge(out, on='date', how='left')
assert len(tl) == before_n, f'ROW COUNT CHANGED: {before_n} -> {len(tl)} -- merge key had duplicates, STOP'
tl.to_csv(os.path.join(SCRIPT_DIR, '54c_trade_log_with_features.csv'), index=False)
print(f'54c_trade_log_with_features.csv: {tl.shape[1]} columns, {len(tl)} trades (row count verified unchanged)')
