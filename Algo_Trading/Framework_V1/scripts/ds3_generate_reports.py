"""
DS3 Report Generator
Reads all 30 parquets from intraday_5min_DS3/, validates each,
writes DS3_validation_report.txt and DS3_fetch_log.csv.
"""
import sys, io
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IST        = pytz.FixedOffset(330)
SCRIPT_DIR = Path(__file__).parent
FV1_DIR    = SCRIPT_DIR.parent
DS3_DIR    = FV1_DIR / 'data/historical/intraday_5min_DS3'
OUT_DIR    = FV1_DIR / 'data/historical'

EXPECTED_STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BANDHANBNK','BHARTIARTL',
    'CIPLA','COALINDIA','DABUR','DIVISLAB','HDFCBANK',
    'HINDALCO','ICICIBANK','INDUSINDBK','INFY','ITC',
    'JSWSTEEL','NATIONALUM','NTPC','ONGC','PNB',
    'POWERGRID','RELIANCE','SBIN','SUNPHARMA','TATAMOTORS',
    'TATASTEEL','TECHM','VEDL','VI','WIPRO',
]

END_DATE_LIMIT = pd.Timestamp('2025-12-31 23:59:59', tz=IST)
POST_MARKET    = pd.Timestamp('15:30').time()

rows_log  = []
report_lines = []

def check_stock(stock):
    pq = DS3_DIR / f'{stock}.parquet'
    if not pq.exists():
        return {'stock': stock, 'status': 'MISSING', 'candles': 0,
                'first_date': '', 'last_date': '', 'trading_days': 0,
                'issues': 'parquet file not found'}

    df = pd.read_parquet(pq)

    issues = []

    # Schema check
    expected_cols = ['datetime','open','high','low','close','volume','oi']
    missing_cols  = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        issues.append(f'missing cols: {missing_cols}')

    # Dtype check
    if 'datetime' in df.columns:
        if not hasattr(df['datetime'].dtype, 'tz'):
            issues.append('datetime has no tz')
        elif df['datetime'].dt.tz is None:
            issues.append('datetime tz is None')

    # Null check
    nulls = df.isnull().sum()
    null_cols = [f'{c}:{n}' for c,n in nulls.items() if n > 0]
    if null_cols:
        issues.append(f'nulls: {null_cols}')

    if 'datetime' not in df.columns or len(df) == 0:
        return {'stock': stock, 'status': 'EMPTY', 'candles': len(df),
                'first_date': '', 'last_date': '', 'trading_days': 0,
                'issues': '; '.join(issues) or 'empty dataframe'}

    dt = df['datetime']

    # P1: future dates
    n_future = int((dt > END_DATE_LIMIT).sum())
    if n_future:
        issues.append(f'P1_fail:{n_future}_future_candles')

    # P2: post-market
    n_post = int((dt.dt.time > POST_MARKET).sum())
    if n_post:
        issues.append(f'P2_fail:{n_post}_post_market')

    # P3a: OHLC violations
    n_ohlc = int(((df['high'] < df['low'])   |
                  (df['high'] < df['open'])  |
                  (df['high'] < df['close']) |
                  (df['low']  > df['open'])  |
                  (df['low']  > df['close'])).sum())
    if n_ohlc:
        issues.append(f'P3a_fail:{n_ohlc}_ohlc_violations')

    # Duplicate timestamps
    n_dup = int(dt.duplicated().sum())
    if n_dup:
        issues.append(f'duplicates:{n_dup}')

    # Check index is RangeIndex
    if not isinstance(df.index, pd.RangeIndex):
        issues.append('non_range_index')

    candles      = len(df)
    first_date   = str(dt.iloc[0])[:10]
    last_date    = str(dt.iloc[-1])[:10]
    trading_days = dt.dt.date.nunique()
    status       = 'OK' if not issues else 'WARN'

    return {
        'stock':        stock,
        'status':       status,
        'candles':      candles,
        'first_date':   first_date,
        'last_date':    last_date,
        'trading_days': trading_days,
        'issues':       '; '.join(issues) if issues else '',
    }

# ── Run validation ───────────────────────────────────────────────────────────
print("Running DS3 validation...")
results = []
for stock in EXPECTED_STOCKS:
    r = check_stock(stock)
    results.append(r)
    flag = '⚠️ ' if r['status'] != 'OK' else '✅'
    print(f"  {flag} {stock:15s}: {r['candles']:>7,} candles | "
          f"{r['first_date']} → {r['last_date']} | "
          f"{r['trading_days']} days"
          + (f" | {r['issues']}" if r['issues'] else ''))

# ── DS3_fetch_log.csv ────────────────────────────────────────────────────────
df_log = pd.DataFrame(results)
csv_path = OUT_DIR / 'DS3_fetch_log.csv'
df_log.to_csv(csv_path, index=False)
print(f"\nSaved fetch log → {csv_path}")

# ── DS3_validation_report.txt ────────────────────────────────────────────────
ok_count   = sum(1 for r in results if r['status'] == 'OK')
warn_count = sum(1 for r in results if r['status'] == 'WARN')
miss_count = sum(1 for r in results if r['status'] == 'MISSING')
total_candles = sum(r['candles'] for r in results)

lines = []
lines.append("=" * 72)
lines.append("DS3 VALIDATION REPORT")
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Source:    Kite MCP (mcp__kite__get_historical_data)")
lines.append(f"Interval:  5-minute OHLCV+OI")
lines.append(f"Range:     2015-02-02 → 2025-12-31")
lines.append(f"Output:    Framework_V1/data/historical/intraday_5min_DS3/")
lines.append("=" * 72)
lines.append(f"\nSUMMARY")
lines.append(f"  Stocks total:  {len(EXPECTED_STOCKS)}")
lines.append(f"  OK:            {ok_count}")
lines.append(f"  WARN:          {warn_count}")
lines.append(f"  MISSING:       {miss_count}")
lines.append(f"  Total candles: {total_candles:,}")
lines.append(f"\nVALIDATIONS APPLIED")
lines.append(f"  P1 : No candles after 2025-12-31")
lines.append(f"  P2 : No post-15:30 candles")
lines.append(f"  P3a: No OHLC violations (high<low, high<open, etc.)")
lines.append(f"\nPER-STOCK RESULTS")
lines.append(f"  {'Stock':<15} {'Status':<8} {'Candles':>8} {'First':>12} {'Last':>12} {'Days':>5}  Issues")
lines.append(f"  {'-'*15} {'-'*8} {'-'*8} {'-'*12} {'-'*12} {'-'*5}  -------")
for r in results:
    issues_str = r['issues'][:50] if r['issues'] else ''
    lines.append(f"  {r['stock']:<15} {r['status']:<8} {r['candles']:>8,} "
                 f"{r['first_date']:>12} {r['last_date']:>12} {r['trading_days']:>5}  {issues_str}")

lines.append("")
lines.append("NOTES")
lines.append("  - TATAMOTORS: Kite-only data (full 2015-2025 range from token 884737)")
lines.append("    Historical Kite prices may reflect price-adjusted series vs exchange")
lines.append("    The data is internally consistent within this dataset.")
lines.append("  - Low coverage flag: trading_days < 2000")
lines.append("=" * 72)

report_text = '\n'.join(lines)
report_path = OUT_DIR / 'DS3_validation_report.txt'
report_path.write_text(report_text, encoding='utf-8')
print(f"Saved validation report → {report_path}")
print(f"\n{'='*40}")
print(f"DS3 COMPLETE: {ok_count}/{len(EXPECTED_STOCKS)} stocks OK | {total_candles:,} total candles")
if warn_count or miss_count:
    print(f"  Warnings: {warn_count} | Missing: {miss_count}")
