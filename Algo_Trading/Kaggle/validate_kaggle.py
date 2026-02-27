# -*- coding: utf-8 -*-
"""
Kaggle dataset1 vs Source A (Framework_V1 intraday_5min) validation.
Compares RELIANCE, HDFCBANK, TATAMOTORS, SBIN, BHARTIARTL for Jan-Mar 2022.
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

SOURCE_A = Path("c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V1/data/historical/intraday_5min")
SOURCE_B = Path("c:/Users/Saurav/CodePonting/Algo_Trading/Kaggle/dataset1")

STOCKS = ["RELIANCE", "HDFCBANK", "TATAMOTORS", "SBIN", "BHARTIARTL"]

START = "2022-01-01"
END   = "2022-03-31 23:59:59"

PRICE_TOL  = 0.05   # 0.05% tolerance on OHLC
VOL_TOL    = 1.0    # 1% tolerance on volume (resampling rounding)

# ── loaders ────────────────────────────────────────────────────────────────────

def load_source_a(stock: str) -> pd.DataFrame:
    """Load Source A 5-min parquet; datetime is a column, index is integer."""
    path = SOURCE_A / f"{stock}.parquet"
    df = pd.read_parquet(path)
    # Move datetime column to index
    df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None)
    df = df.set_index("datetime")
    df.columns = df.columns.str.lower()
    df = df[["open", "high", "low", "close", "volume"]]
    return df.loc[START:END].sort_index()


def load_source_b(stock: str) -> pd.DataFrame:
    """Load Source B 1-min CSV and resample to 5-min."""
    path = SOURCE_B / f"{stock}_minute.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.set_index("date")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.columns = df.columns.str.lower()
    df = df[["open", "high", "low", "close", "volume"]]
    df = df.loc[START:END].sort_index()
    # Resample 1-min to 5-min OHLCV
    df5 = df.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["open"])
    return df5


def pct_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b != 0, np.abs((a - b) / b) * 100, np.nan)


# ── main ───────────────────────────────────────────────────────────────────────

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", "{:.2f}".format)

summary = {}

for stock in STOCKS:
    print(f"\n{'='*70}")
    print(f"  {stock}")
    print(f"{'='*70}")

    # -- load sources ----------------------------------------------------------
    try:
        a = load_source_a(stock)
    except FileNotFoundError:
        print(f"  [!] Source A missing: {stock}.parquet")
        summary[stock] = "MISSING_A"
        continue

    try:
        b = load_source_b(stock)
    except FileNotFoundError:
        print(f"  [!] Source B missing: {stock}_minute.csv")
        summary[stock] = "MISSING_B"
        continue

    print(f"\n  Source A (5-min bars) : {len(a)} rows  | {a.index.min()} -> {a.index.max()}")
    print(f"  Source B (5-min resam): {len(b)} rows  | {b.index.min()} -> {b.index.max()}")

    # -- align on common timestamps -------------------------------------------
    common = a.index.intersection(b.index)
    a_only = a.index.difference(b.index)
    b_only = b.index.difference(a.index)
    print(f"\n  Common timestamps     : {len(common)}")
    print(f"  Only in A (missing B) : {len(a_only)}")
    print(f"  Only in B (missing A) : {len(b_only)}")

    if len(common) == 0:
        print("  [!] No overlapping timestamps -- cannot compare!")
        summary[stock] = "NO_OVERLAP"
        continue

    a_c = a.loc[common]
    b_c = b.loc[common]

    # -- side-by-side sample (first 10 common rows) ---------------------------
    print(f"\n  {'--- Side-by-side sample (first 10 common rows) ---':^60}")
    print(f"  {'datetime':<22} {'A_open':>8} {'B_open':>8} {'A_high':>8} {'B_high':>8} {'A_low':>8} {'B_low':>8} {'A_close':>8} {'B_close':>8}")
    print(f"  {'-'*22} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for ts in common[:10]:
        ar = a_c.loc[ts]
        br = b_c.loc[ts]
        print(f"  {str(ts):<22} {ar['open']:>8.2f} {br['open']:>8.2f} "
              f"{ar['high']:>8.2f} {br['high']:>8.2f} "
              f"{ar['low']:>8.2f} {br['low']:>8.2f} "
              f"{ar['close']:>8.2f} {br['close']:>8.2f}")

    # also show volume separately
    print(f"\n  {'--- Volume sample ---':^60}")
    print(f"  {'datetime':<22} {'A_volume':>12} {'B_volume':>12} {'diff_%':>8}")
    print(f"  {'-'*22} {'-'*12} {'-'*12} {'-'*8}")
    for ts in common[:10]:
        av = a_c.loc[ts, "volume"]
        bv = b_c.loc[ts, "volume"]
        d  = abs(av - bv) / bv * 100 if bv != 0 else float("nan")
        print(f"  {str(ts):<22} {av:>12,.0f} {bv:>12,.0f} {d:>8.2f}%")

    # -- mismatch analysis ----------------------------------------------------
    cols  = ["open", "high", "low", "close"]
    tols  = {c: PRICE_TOL for c in cols}
    tols["volume"] = VOL_TOL

    print(f"\n  --- Mismatch counts (price tol={PRICE_TOL}%, vol tol={VOL_TOL}%) ---")
    any_bad = False
    for col in cols + ["volume"]:
        diff  = pct_diff(a_c[col].values, b_c[col].values)
        bad   = int(np.nansum(diff > tols[col]))
        total = len(common)
        pct   = bad / total * 100
        flag  = "[!!]" if bad > 0 else "[ ok]"
        print(f"  {flag} {col:8s}: {bad:>5}/{total} rows differ  ({pct:.1f}%)")
        if bad > 0:
            any_bad = True

    # -- verdict ---------------------------------------------------------------
    missing_pct = len(a_only) / len(a) * 100 if len(a) else 0
    if not any_bad and missing_pct < 5:
        verdict = "MATCH"
    else:
        verdict = "MISMATCH"
    summary[stock] = verdict
    print(f"\n  Verdict: {verdict}")

# ── final summary ──────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("  FINAL SUMMARY  (Jan-Mar 2022, Source A 5-min vs Source B resampled)")
print(f"{'='*70}")
icons = {
    "MATCH":      "MATCH      [OK]",
    "MISMATCH":   "MISMATCH   [!!]",
    "MISSING_A":  "MISSING SOURCE A [??]",
    "MISSING_B":  "MISSING SOURCE B [??]",
    "NO_OVERLAP": "NO OVERLAP [??]",
}
for stock, verdict in summary.items():
    print(f"  {stock:12s} -> {icons.get(verdict, verdict)}")
print()
