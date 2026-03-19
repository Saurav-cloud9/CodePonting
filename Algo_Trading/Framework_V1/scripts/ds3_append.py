"""
DS3 Append Script — Patch Dec 31, 2025 from Upstox intraday_5min parquets
For each stock:
  1. Compare Dec 30 candles between DS3 (Kite) and Upstox source
  2. If match → append Dec 31 Upstox candles to DS3 parquet
  3. If mismatch → flag and skip
"""
import sys, io
from pathlib import Path
import pandas as pd
import pytz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IST        = pytz.FixedOffset(330)
SCRIPT_DIR = Path(__file__).parent
FV1_DIR    = SCRIPT_DIR.parent
DS3_DIR    = FV1_DIR / 'data/historical/intraday_5min_DS3'
SRC_DIR    = FV1_DIR / 'data/historical/intraday_5min'

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BANDHANBNK','BHARTIARTL',
    'CIPLA','COALINDIA','DABUR','DIVISLAB','HDFCBANK',
    'HINDALCO','ICICIBANK','INDUSINDBK','INFY','ITC',
    'JSWSTEEL','NATIONALUM','NTPC','ONGC','PNB',
    'POWERGRID','RELIANCE','SBIN','SUNPHARMA','TATAMOTORS',
    'TATASTEEL','TECHM','VEDL','VI','WIPRO',
]

DEC30     = pd.Timestamp('2025-12-30', tz=IST).date()
DEC31     = pd.Timestamp('2025-12-31', tz=IST).date()
CLOSE_TOL = 0.5   # % tolerance for Dec-30 close price comparison

mismatches = []
appended   = []
no_dec31   = []
no_src     = []

for stock in STOCKS:
    ds3_path = DS3_DIR / f'{stock}.parquet'
    src_path = SRC_DIR / f'{stock}.parquet'

    if not src_path.exists():
        print(f'  SKIP  {stock}: source parquet not found')
        no_src.append(stock)
        continue

    # Load parquets
    df_ds3 = pd.read_parquet(ds3_path)
    df_src = pd.read_parquet(src_path)

    # Normalise datetimes to IST
    for df in (df_ds3, df_src):
        if df['datetime'].dt.tz is None:
            df['datetime'] = df['datetime'].dt.tz_localize(IST)
        else:
            df['datetime'] = df['datetime'].dt.tz_convert(IST)

    # Slice Dec 30 and Dec 31
    ds3_d30 = df_ds3[df_ds3['datetime'].dt.date == DEC30].copy()
    src_d30 = df_src[df_src['datetime'].dt.date == DEC30].copy()
    src_d31 = df_src[df_src['datetime'].dt.date == DEC31].copy()

    # Dec 31 existence check
    if len(src_d31) == 0:
        print(f'  NOTE  {stock}: no Dec-31 data in Upstox source — skipping')
        no_dec31.append(stock)
        continue

    # Dec 30 candle count check
    if len(ds3_d30) == 0 or len(src_d30) == 0:
        reason = (f'Dec-30 candle count: DS3={len(ds3_d30)} '
                  f'Upstox={len(src_d30)}')
        print(f'  FLAG  {stock}: {reason}')
        mismatches.append({'stock': stock, 'reason': reason})
        continue

    # Compare Dec 30 close prices on common timestamps
    ds3_d30 = ds3_d30.set_index('datetime')
    src_d30 = src_d30.set_index('datetime')
    common  = ds3_d30.index.intersection(src_d30.index)

    if len(common) == 0:
        reason = 'no common timestamps on Dec-30'
        print(f'  FLAG  {stock}: {reason}')
        mismatches.append({'stock': stock, 'reason': reason})
        continue

    close_ds3 = ds3_d30.loc[common, 'close']
    close_src = src_d30.loc[common, 'close']
    pct_diff  = ((close_ds3 - close_src).abs() / close_src * 100)
    max_pct   = pct_diff.max()
    mean_pct  = pct_diff.mean()

    if max_pct > CLOSE_TOL:
        reason = (f'Dec-30 close mismatch: max={max_pct:.2f}% '
                  f'mean={mean_pct:.2f}% (tol={CLOSE_TOL}%)')
        print(f'  FLAG  {stock}: {reason}')
        mismatches.append({'stock': stock, 'reason': reason,
                           'max_pct_diff': round(max_pct, 4),
                           'mean_pct_diff': round(mean_pct, 4)})
        continue

    # Append Dec 31
    for col in ['open','high','low','close']:
        src_d31[col] = src_d31[col].astype('float64')
    for col in ['volume','oi']:
        if col in src_d31.columns:
            src_d31[col] = src_d31[col].astype('int64')
        else:
            src_d31[col] = 0

    COLS    = ['datetime','open','high','low','close','volume','oi']
    df_ds3  = df_ds3.reset_index(drop=True)
    df_new  = pd.concat(
        [df_ds3[COLS], src_d31.reset_index()[COLS]],
        ignore_index=True
    )
    df_new = (df_new
              .sort_values('datetime')
              .drop_duplicates(subset='datetime')
              .reset_index(drop=True))

    df_new.to_parquet(ds3_path, index=False)
    print(f'  OK    {stock}: +{len(src_d31)} Dec-31 candles appended '
          f'(Dec-30 max diff={max_pct:.3f}% mean={mean_pct:.3f}%) '
          f'| total now {len(df_new):,}')
    appended.append(stock)

# Summary
print(f'\n{"="*60}')
print(f'SUMMARY')
print(f'  Appended Dec-31 : {len(appended)}/{len(STOCKS)} stocks')
print(f'  Flagged mismatch: {len(mismatches)}')
print(f'  No Dec-31 in src: {len(no_dec31)}')
print(f'  Source missing  : {len(no_src)}')

if mismatches:
    print(f'\nMISMATCHES — Dec-30 price check failed (NOT updated):')
    for m in mismatches:
        print(f'  {m["stock"]}: {m["reason"]}')

if no_dec31:
    print(f'\nNO DEC-31 DATA in Upstox source: {no_dec31}')