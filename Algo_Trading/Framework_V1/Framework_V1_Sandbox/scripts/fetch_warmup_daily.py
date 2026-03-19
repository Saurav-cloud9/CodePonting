"""
fetch_warmup_daily.py
=====================
Fetch pre-DS3 daily OHLCV warmup data via yfinance for each stock.

Purpose:
  MA200 needs 200 trading days of daily history before DS3 starts (2015-02-02).
  Fetches warmup bars and prepends them to data/historical/daily/{STOCK}.parquet.

Logic per stock:
  1. Read DS3 earliest date from existing daily parquet (datetime column)
  2. Count back (200 + 10 buffer = 210) NSE business days -> fetch_start
  3. Fetch daily OHLCV from yfinance: fetch_start -> ds3_start - 1 day
  4. P2 consistency check (gap, price diff, duplicates)
  5. Prepend to existing parquet (DS3-derived rows take priority on duplicates)

Skips BANDHANBNK (listed 2018 -- no pre-DS3 daily data available).
Skips stocks where daily parquet already starts pre-2015 (resume-aware).

Usage:
    python fetch_warmup_daily.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# ─── Paths ────────────────────────────────────────────────────────────────────

SANDBOX_DIR = Path(__file__).resolve().parent.parent
FV1_DIR     = SANDBOX_DIR.parent
DAILY_DIR   = FV1_DIR / "data" / "historical" / "daily"
TOKEN_FILE  = FV1_DIR / "data" / "historical" / "ds3_tokens_chunks.json"

SKIP_STOCKS = {"BANDHANBNK"}   # listed 2018 -- no pre-2015 data

# Yahoo Finance symbol suffix for NSE
YF_SUFFIX = ".NS"

# Stocks with non-standard Yahoo Finance symbols
YF_OVERRIDES = {
    "VI": "IDEA.NS",         # Vodafone Idea
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def yf_symbol(stock: str) -> str:
    return YF_OVERRIDES.get(stock, f"{stock}{YF_SUFFIX}")


def business_days_back(ref_date: pd.Timestamp, n: int) -> pd.Timestamp:
    """
    Approximate: step back n weekdays from ref_date.
    NSE holidays are not accounted for -- we add 10 extra buffer days
    in the caller to compensate. yfinance returns only actual trading days.
    """
    result = np.busday_offset(
        ref_date.date(),
        -n,
        roll='forward',
    )
    return pd.Timestamp(result)


def fetch_yfinance(stock: str, fetch_start: pd.Timestamp, fetch_end: pd.Timestamp) -> pd.DataFrame:
    """Fetch daily OHLCV from yfinance and return normalized DataFrame."""
    sym = yf_symbol(stock)
    raw = yf.download(
        sym,
        start=fetch_start.strftime('%Y-%m-%d'),
        end=(fetch_end + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),  # end is exclusive
        auto_adjust=True,
        progress=False,
    )
    if raw.empty:
        return pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

    # Flatten MultiIndex columns if present
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [col[0].lower() for col in raw.columns]
    else:
        raw.columns = [c.lower() for c in raw.columns]

    raw = raw.reset_index()
    raw = raw.rename(columns={'date': 'datetime', 'Date': 'datetime'})
    raw['datetime'] = pd.to_datetime(raw['datetime']).dt.tz_localize(None).dt.normalize()

    df = raw[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
    df['open']   = df['open'].astype('float64')
    df['high']   = df['high'].astype('float64')
    df['low']    = df['low'].astype('float64')
    df['close']  = df['close'].astype('float64')
    df['volume'] = df['volume'].astype('int64')
    return df.sort_values('datetime').reset_index(drop=True)


def consistency_check(stock: str, new_df: pd.DataFrame, existing: pd.DataFrame) -> bool:
    """
    P2 checks:
      1. Gap between new_end and ds3_start <= 5 calendar days
      2. Price diff at boundary < 0.5% (overlapping dates if any)
      3. Duplicate detection

    Returns True if OK, False if any check fails (aborts write).
    """
    new_end     = new_df['datetime'].max().date()
    exist_start = pd.to_datetime(existing['datetime']).min().date()

    gap_days = (pd.Timestamp(exist_start) - pd.Timestamp(new_end)).days
    gap_ok   = 1 <= gap_days <= 5

    # Price check on any overlapping dates
    overlap = pd.merge(
        new_df[['datetime', 'close']].tail(10),
        existing[['datetime', 'close']].head(10),
        on='datetime', suffixes=('_new', '_exist'),
    )
    if len(overlap) > 0:
        overlap['pct_diff'] = (
            (overlap['close_new'] - overlap['close_exist'])
            / overlap['close_exist'] * 100
        ).abs()
        max_diff = overlap['pct_diff'].max()
    else:
        max_diff = 0.0

    price_ok = max_diff <= 0.5
    status = "OK" if (gap_ok and price_ok) else "FAIL"

    print(
        f"  {stock:<15} yf_end={new_end}  ds3_start={exist_start}  "
        f"gap={gap_days}d({'OK' if gap_ok else 'FAIL'})  "
        f"price_diff={max_diff:.2f}%({'OK' if price_ok else 'FAIL'})  "
        f"-> {status}"
    )

    if not gap_ok:
        print(f"  [ABORT] {stock}: gap={gap_days}d is outside 1-5 day window.")
        return False
    if not price_ok:
        print(f"  [ABORT] {stock}: price mismatch {max_diff:.2f}% > 0.5%.")
        return False
    return True


def prepend_and_write(stock: str, new_df: pd.DataFrame, existing: pd.DataFrame, out_path: Path):
    """Combine new (warmup) + existing (DS3-derived), dedup, write."""
    combined = pd.concat([new_df, existing], ignore_index=True)
    n_before  = len(combined)
    combined  = combined.drop_duplicates(subset=['datetime'], keep='last')  # keep DS3-derived
    n_dupes   = n_before - len(combined)
    combined  = combined.sort_values('datetime').reset_index(drop=True)
    combined.to_parquet(out_path, index=False)
    print(
        f"  {stock:<15} wrote {len(combined)} rows total  "
        f"(+{len(new_df)} yf warmup, {n_dupes} dupes removed)"
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Load token map (for stock list only)
    with open(TOKEN_FILE) as f:
        meta = json.load(f)
    tokens = meta['tokens']   # {STOCK: instrument_token}

    # Collect stocks to process
    stocks_todo = []
    print("\n=== State Check ===")
    print(f"{'Stock':<15} {'DS3 Start':<13} {'Action'}")
    print("-" * 50)

    for stock in sorted(tokens.keys()):
        if stock in SKIP_STOCKS:
            print(f"{stock:<15} {'(skipped)':<13} BANDHANBNK -- no pre-2015 data")
            continue

        parquet_path = DAILY_DIR / f"{stock}.parquet"
        if not parquet_path.exists():
            print(f"{stock:<15} {'(missing)':<13} SKIP -- parquet not found")
            continue

        df = pd.read_parquet(parquet_path)
        earliest = pd.to_datetime(df['datetime']).min().date()

        if earliest.year < 2015:
            print(f"{stock:<15} {str(earliest):<13} SKIP -- already has pre-2015 data")
            continue

        # Need warmup
        stocks_todo.append((stock, pd.Timestamp(earliest)))
        print(f"{stock:<15} {str(earliest):<13} FETCH warmup needed")

    if not stocks_todo:
        print("\nAll stocks already have warmup data -- nothing to do.")
        return

    print(f"\n{len(stocks_todo)} stocks need warmup fetch.")

    # Determine fetch parameters
    MA_PERIOD  = 200
    BUFFER     = 10
    LOOKBACK   = MA_PERIOD + BUFFER   # 210 weekdays

    print(f"\nLookback: {MA_PERIOD} (MA200) + {BUFFER} (buffer) = {LOOKBACK} weekdays")
    print(f"\nFetch plan:")
    for stock, ds3_start in stocks_todo:
        fetch_start = business_days_back(ds3_start, LOOKBACK)
        fetch_end   = ds3_start - pd.Timedelta(days=1)
        print(f"  {stock:<15} {fetch_start.date()} -> {fetch_end.date()}")

    print(f"\nEstimated runtime: ~{len(stocks_todo) * 2}s (yfinance, no auth needed)")
    print()

    all_ok = True
    fetched = {}

    print("=== P1: Fetch (yfinance) ===")
    for stock, ds3_start in stocks_todo:
        fetch_start = business_days_back(ds3_start, LOOKBACK)
        fetch_end   = ds3_start - pd.Timedelta(days=1)

        try:
            yf_df = fetch_yfinance(stock, fetch_start, fetch_end)
            if yf_df.empty:
                print(f"  {stock:<15} [WARN] 0 rows returned -- skipping")
                continue
            fetched[stock] = yf_df
            print(
                f"  {stock:<15} {len(yf_df):>4} rows  "
                f"{yf_df['datetime'].min().date()} -> {yf_df['datetime'].max().date()}  OK"
            )
        except Exception as e:
            print(f"  {stock:<15} [ERROR] {e}")
            all_ok = False

        time.sleep(0.3)  # polite rate limiting

    if not fetched:
        print("\n[ERROR] No data fetched. Exiting.")
        sys.exit(1)

    print(f"\n=== P2: Consistency Check ===")
    print(f"{'Stock':<15} {'yf_end':<12} {'ds3_start':<12} {'gap':<16} {'price_diff':<16} {'status'}")
    print("-" * 80)

    p2_pass = []
    for stock, yf_df in fetched.items():
        parquet_path = DAILY_DIR / f"{stock}.parquet"
        existing = pd.read_parquet(parquet_path)
        ok = consistency_check(stock, yf_df, existing)
        if ok:
            p2_pass.append(stock)
        else:
            all_ok = False

    if len(p2_pass) < len(fetched):
        print(f"\n[STOP] P2 failed for {len(fetched) - len(p2_pass)} stocks. Not writing any files.")
        sys.exit(1)

    print(f"\n=== Write ===")
    for stock in p2_pass:
        parquet_path = DAILY_DIR / f"{stock}.parquet"
        existing = pd.read_parquet(parquet_path)
        prepend_and_write(stock, fetched[stock], existing, parquet_path)

    if all_ok:
        print(f"\n=== All {len(p2_pass)} stocks written. P3 (feature rebuild) next. ===")
    else:
        print(f"\n=== Completed with some warnings/errors -- review above before running P3. ===")


if __name__ == '__main__':
    main()
