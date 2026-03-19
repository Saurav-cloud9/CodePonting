"""
build_daily_from_ds3.py
=======================
Resample DS3 5-min intraday bars → daily OHLCV for each stock.
Overwrites data/historical/daily/{STOCK}.parquet with full 2015-2025 history.

After build, verifies that feature computation produces zero nulls for
2015-2020 by running build_stock_features() from sb_regime_optuna logic
and printing a year × null count table.

Usage:
    python scripts/build_daily_from_ds3.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import sys

# ── Paths ──────────────────────────────────────────────────────────────────
SANDBOX_DIR = Path(__file__).resolve().parent.parent
FV1_DIR     = SANDBOX_DIR.parent
DS3_DIR     = FV1_DIR / "data" / "historical" / "intraday_5min_DS3"
DAILY_DIR   = FV1_DIR / "data" / "historical" / "daily"

STOCKS = [
    "ADANIPORTS", "ASHOKLEY",   "AXISBANK",   "BANDHANBNK", "BHARTIARTL",
    "CIPLA",      "COALINDIA",  "DABUR",       "DIVISLAB",  "HDFCBANK",
    "HINDALCO",   "ICICIBANK",  "INDUSINDBK", "INFY",       "ITC",
    "JSWSTEEL",   "NATIONALUM", "NTPC",       "ONGC",       "PNB",
    "POWERGRID",  "RELIANCE",   "SBIN",       "SUNPHARMA",  "TATAMOTORS",
    "TATASTEEL",  "TECHM",      "VEDL",       "VI",         "WIPRO",
]


# ── Step 1: Resample 5-min → daily ─────────────────────────────────────────

def build_daily(stock: str) -> pd.DataFrame:
    path = DS3_DIR / f"{stock}.parquet"
    df = pd.read_parquet(path)

    # Strip timezone → naive IST wall-clock
    df["datetime"] = pd.to_datetime(
        df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    df = df.sort_values("datetime").reset_index(drop=True)
    df["date"] = df["datetime"].dt.date

    daily = (
        df.groupby("date")
        .agg(
            open   = ("open",   "first"),
            high   = ("high",   "max"),
            low    = ("low",    "min"),
            close  = ("close",  "last"),
            volume = ("volume", "sum"),
        )
        .reset_index()
    )
    daily["datetime"] = pd.to_datetime(daily["date"])
    daily = daily[["datetime", "open", "high", "low", "close", "volume"]]
    return daily


print("=" * 60)
print("  build_daily_from_ds3.py -- Resample DS3 -> Daily OHLCV")
print("=" * 60)
print(f"\nSource : {DS3_DIR}")
print(f"Output : {DAILY_DIR}\n")

ok = 0
for stock in STOCKS:
    src = DS3_DIR / f"{stock}.parquet"
    if not src.exists():
        print(f"  [SKIP] {stock} — DS3 file not found")
        continue
    daily = build_daily(stock)
    out   = DAILY_DIR / f"{stock}.parquet"
    daily.to_parquet(out, index=False)
    yr_min = daily["datetime"].dt.year.min()
    yr_max = daily["datetime"].dt.year.max()
    print(f"  {stock:<15}  {len(daily):>5} days  ({yr_min}-{yr_max})  -> {out.name}")
    ok += 1

print(f"\nDone: {ok}/{len(STOCKS)} stocks written.\n")


# ── Step 2: Verify — run build_stock_features() logic, check nulls ─────────

print("=" * 60)
print("  VERIFICATION — Null check on rebuilt feature table")
print("=" * 60)

frames = []
for stock in STOCKS:
    path = DAILY_DIR / f"{stock}.parquet"
    if not path.exists():
        continue

    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["datetime"]).dt.normalize().dt.tz_localize(None).dt.date
    df = df.sort_values("date").reset_index(drop=True)

    df["ma50"]      = df["close"].rolling(50,  min_periods=50).mean()
    df["ma100"]     = df["close"].rolling(100, min_periods=100).mean()
    df["ma200"]     = df["close"].rolling(200, min_periods=200).mean()
    df["atr14"]     = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
    df["vol_avg20"] = df["volume"].rolling(20, min_periods=20).mean()
    df["ma50_5d"]   = df["ma50"].shift(5)
    df["r52w_high"] = df["high"].rolling(252, min_periods=1).max()
    df["r52w_low"]  = df["low"].rolling(252,  min_periods=1).min()

    prev_close  = df["close"].shift(1)
    prev_open   = df["open"].shift(1)
    prev_high   = df["high"].shift(1)
    prev_low    = df["low"].shift(1)
    prev_vol    = df["volume"].shift(1)
    prev_ma50   = df["ma50"].shift(1)
    prev_ma100  = df["ma100"].shift(1)
    prev_ma200  = df["ma200"].shift(1)
    prev_atr14  = df["atr14"].shift(1)
    prev_va20   = df["vol_avg20"].shift(1)
    prev_ma50_5 = df["ma50_5d"].shift(1)

    df["p_close"]       = prev_close
    df["p_ma50"]        = prev_ma50
    df["p_ma100"]       = prev_ma100
    df["p_ma200"]       = prev_ma200
    df["p_atr_ratio"]   = prev_atr14 / prev_close
    df["p_range_ratio"] = (prev_high - prev_low) / prev_close
    body_sz = (prev_close - prev_open).abs()
    rng_sz  = (prev_high - prev_low).replace(0, np.nan)
    df["p_body_ratio"]  = body_sz / rng_sz
    df["p_vol_ratio"]   = prev_vol / prev_va20.replace(0, np.nan)
    df["ma50_slope"]    = prev_ma50 - prev_ma50_5
    df["dist_ma50"]     = (prev_close - prev_ma50) / prev_ma50

    df["year"] = pd.to_datetime(df["date"]).dt.year
    frames.append(df[["year", "p_close", "p_ma50", "p_ma100", "p_ma200",
                       "p_atr_ratio", "p_range_ratio", "p_body_ratio",
                       "p_vol_ratio", "ma50_slope", "dist_ma50"]])

all_df = pd.concat(frames, ignore_index=True)
feat_cols = [c for c in all_df.columns if c != "year"]

print("\nYear × feature null count (should be 0 for 2015+ except early warm-up):\n")
null_tbl = all_df.groupby("year")[feat_cols].apply(lambda g: g.isnull().sum())
print(null_tbl.to_string())

# Summary per year
print("\nYear-level summary (any nulls?):")
null_any = null_tbl.sum(axis=1)
for yr, cnt in null_any.items():
    status = "OK" if cnt == 0 else f"WARN: {cnt} nulls"
    print(f"  {yr}: {status}")

print("\nDone.")
