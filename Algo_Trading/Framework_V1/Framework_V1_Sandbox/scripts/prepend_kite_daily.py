"""
prepend_kite_daily.py
=====================
Usage:
    python prepend_kite_daily.py STOCK '[ {"date":"...","open":...}, ... ]'

Parses Kite daily OHLCV JSON, standardises columns, then prepends
to data/historical/daily/{STOCK}.parquet.
Runs P4 consistency checks (gaps, price mismatch, duplicates) before writing.
"""

import sys, json
import pandas as pd
from pathlib import Path

SANDBOX_DIR = Path(__file__).resolve().parent.parent
FV1_DIR     = SANDBOX_DIR.parent
DAILY_DIR   = FV1_DIR / "data" / "historical" / "daily"

def parse_kite(raw: list) -> pd.DataFrame:
    rows = []
    for r in raw:
        rows.append({
            "datetime": pd.to_datetime(r["date"]).tz_localize(None).normalize(),
            "open":   float(r["open"]),
            "high":   float(r["high"]),
            "low":    float(r["low"]),
            "close":  float(r["close"]),
            "volume": int(r["volume"]),
        })
    return pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)


def main():
    if len(sys.argv) < 3:
        print("Usage: prepend_kite_daily.py STOCK '<json>'")
        sys.exit(1)

    stock    = sys.argv[1]
    raw_json = json.loads(sys.argv[2])
    kite_df  = parse_kite(raw_json)

    out_path = DAILY_DIR / f"{stock}.parquet"
    if not out_path.exists():
        # New stock entirely — just write
        kite_df.to_parquet(out_path, index=False)
        print(f"[NEW] {stock}: wrote {len(kite_df)} rows "
              f"({kite_df['datetime'].min().date()} -> {kite_df['datetime'].max().date()})")
        return

    existing = pd.read_parquet(out_path)
    existing["datetime"] = pd.to_datetime(existing["datetime"]).dt.normalize()
    existing = existing.sort_values("datetime").reset_index(drop=True)

    kite_end   = kite_df["datetime"].max().date()
    exist_start = existing["datetime"].min().date()

    # ── P4-1: Gap check ──────────────────────────────────────────────────
    # Expect kite_end to be 1-3 trading days before exist_start
    import datetime
    gap_days = (pd.Timestamp(exist_start) - pd.Timestamp(kite_end)).days
    gap_flag = "OK" if 1 <= gap_days <= 5 else f"WARN gap={gap_days}d"

    # ── P4-2: Price consistency at join boundary ──────────────────────────
    # Compare last 5 Kite rows vs first 5 existing rows on overlapping dates
    overlap = pd.merge(
        kite_df[["datetime", "close"]].tail(10),
        existing[["datetime", "close"]].head(10),
        on="datetime", suffixes=("_kite", "_exist")
    )
    if len(overlap) > 0:
        overlap["pct_diff"] = ((overlap["close_kite"] - overlap["close_exist"])
                                / overlap["close_exist"] * 100).abs()
        max_diff = overlap["pct_diff"].max()
        price_flag = f"OK (max {max_diff:.2f}%)" if max_diff <= 0.5 else f"WARN {max_diff:.2f}% diff"
    else:
        max_diff   = 0.0
        price_flag = "no overlap"

    # ── P4-3: Duplicate removal ───────────────────────────────────────────
    combined = pd.concat([kite_df, existing], ignore_index=True)
    n_before  = len(combined)
    combined  = combined.drop_duplicates(subset=["datetime"], keep="last")  # keep DS3-derived
    n_dupes   = n_before - len(combined)
    combined  = combined.sort_values("datetime").reset_index(drop=True)

    # ── P4 summary ───────────────────────────────────────────────────────
    print(f"{stock:<15} kite_end={kite_end}  ds3_start={exist_start}  "
          f"gap={gap_flag}  price={price_flag}  dupes={n_dupes}  "
          f"total={len(combined)} rows")

    if max_diff > 0.5:
        print(f"  [ABORT] Price mismatch > 0.5% — NOT writing. Investigate first.")
        sys.exit(2)

    combined.to_parquet(out_path, index=False)


if __name__ == "__main__":
    main()
