"""
fv1_prepend_2021_daily.py
─────────────────────────
Downloads daily OHLCV for all 29 NSE F&O stocks for 2021
and PREPENDS to existing Framework_V1/data/historical/daily/*.parquet
so MA50/100/200 have warm-up days before Jan 2022 backtest start.

Schema matched to existing parquets:
  datetime  → datetime64[ns, +05:30] (column, not index)
  open, high, low, close → float64
  volume → int64
  oi → int64 (all zeros for daily data)
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import pytz

# ── Config ──────────────────────────────────────────────────────────────────
STOCKS = [
    "ADANIPORTS", "ASHOKLEY", "AXISBANK", "BANDHANBNK", "BHARTIARTL",
    "CIPLA", "COALINDIA", "DABUR", "DIVISLAB", "HDFCBANK", "HINDALCO",
    "ICICIBANK", "INDUSINDBK", "INFY", "ITC", "JSWSTEEL", "NATIONALUM",
    "NTPC", "ONGC", "PNB", "POWERGRID", "RELIANCE", "SBIN", "SUNPHARMA",
    "TATAMOTORS", "TATASTEEL", "TECHM", "VEDL", "WIPRO",
]

DAILY_DIR = Path(__file__).resolve().parents[1] / "data" / "historical" / "daily"
START = "2021-01-01"
END   = "2021-12-31"
IST   = pytz.FixedOffset(330)   # +05:30, matches existing parquet timezone

# ── Helpers ──────────────────────────────────────────────────────────────────
def download_2021(stock: str) -> pd.DataFrame | None:
    """Download daily OHLCV from yfinance and return schema-matched DataFrame."""
    ticker = f"{stock}.NS"
    try:
        raw = yf.Ticker(ticker).history(
            start=START, end=END,
            interval="1d",
            auto_adjust=True,
        )
    except Exception as e:
        print(f"  [ERROR] Download failed for {stock}: {e}")
        return None

    if raw.empty:
        print(f"  [WARN]  No data returned for {stock}")
        return None

    # yfinance returns DatetimeIndex (possibly tz-aware)
    raw = raw.reset_index()

    # Identify the date column (could be 'Date' or 'Datetime')
    date_col = "Date" if "Date" in raw.columns else "Datetime"

    df = pd.DataFrame()

    # Normalise datetime → date-only at midnight IST
    dates = pd.to_datetime(raw[date_col])
    if dates.dt.tz is None:
        dates = dates.dt.tz_localize(IST)
    else:
        dates = dates.dt.tz_convert(IST)
    # Keep only the date portion (midnight IST), matching existing parquet format
    df["datetime"] = dates.dt.normalize()

    df["open"]   = raw["Open"].astype("float64")
    df["high"]   = raw["High"].astype("float64")
    df["low"]    = raw["Low"].astype("float64")
    df["close"]  = raw["Close"].astype("float64")
    df["volume"] = raw["Volume"].astype("int64")
    df["oi"]     = 0

    df = df.sort_values("datetime").reset_index(drop=True)
    return df


def prepend_to_parquet(stock: str, buf_df: pd.DataFrame) -> None:
    """Prepend buf_df to existing parquet, dedup, sort, save."""
    path = DAILY_DIR / f"{stock}.parquet"
    if not path.exists():
        print(f"  [WARN]  Parquet not found, saving buffer only: {path}")
        buf_df.to_parquet(path, index=False)
        return

    existing = pd.read_parquet(path)

    # Ensure existing datetime is tz-aware IST
    if existing["datetime"].dt.tz is None:
        existing["datetime"] = existing["datetime"].dt.tz_localize(IST)
    else:
        existing["datetime"] = existing["datetime"].dt.tz_convert(IST)

    combined = pd.concat([buf_df, existing], ignore_index=True)
    combined = combined.drop_duplicates(subset="datetime", keep="last")  # keep existing on overlap
    combined = combined.sort_values("datetime").reset_index(drop=True)

    combined.to_parquet(path, index=False)
    print(f"  [OK]    {stock}: {len(buf_df)} rows prepended → total {len(combined)} rows")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Daily parquet dir : {DAILY_DIR}")
    print(f"Buffer period     : {START} to {END}")
    print(f"Stocks            : {len(STOCKS)}\n")

    failed = []
    for stock in STOCKS:
        print(f"Processing {stock} ...")
        buf = download_2021(stock)
        if buf is None or buf.empty:
            failed.append(stock)
            continue
        prepend_to_parquet(stock, buf)

    print("\n── Summary ──────────────────────────────────────────")
    if failed:
        print(f"FAILED ({len(failed)}): {', '.join(failed)}")
    else:
        print("All 29 stocks processed successfully.")

    # ── Verification: HDFCBANK ──
    print("\n── Verification: HDFCBANK ──────────────────────────")
    vdf = pd.read_parquet(DAILY_DIR / "HDFCBANK.parquet")
    print(f"Total rows: {len(vdf)}")
    print("\nFirst 3 rows:")
    print(vdf.head(3).to_string(index=False))
    print("\nLast 3 rows:")
    print(vdf.tail(3).to_string(index=False))
    print(f"\nEarliest date : {vdf['datetime'].min()}")
    print(f"Latest date   : {vdf['datetime'].max()}")

    # Gap check: no missing trading days around Dec 2021 / Jan 2022 boundary
    boundary = vdf[
        (vdf["datetime"] >= "2021-12-01") &
        (vdf["datetime"] <= "2022-02-28")
    ]
    print(f"\nRows in Dec 2021 – Feb 2022 window: {len(boundary)}")
    print(boundary[["datetime", "close"]].to_string(index=False))


if __name__ == "__main__":
    main()
