"""
Fetch BTCUSDT daily klines from Binance public REST API (no auth).
Paginates from 2017-08-17 to today, 1000 rows per call.
Saves: BTCUSDT_1d_binance.csv (date, open, high, low, close, volume)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

OUT_DIR = Path(__file__).resolve().parent
OUT_CSV = OUT_DIR / "BTCUSDT_1d_binance.csv"

BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"
LIMIT = 1000
# Binance BTCUSDT spot listing / earliest reliable daily history
START_MS = int(datetime(2017, 8, 17, tzinfo=timezone.utc).timestamp() * 1000)


def fetch_all_klines(start_ms: int = START_MS) -> list[list]:
    rows: list[list] = []
    cursor = start_ms
    session = requests.Session()

    while True:
        params = {
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "startTime": cursor,
            "limit": LIMIT,
        }
        resp = session.get(BINANCE_URL, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()

        if not batch:
            break

        rows.extend(batch)
        last_open_ms = int(batch[-1][0])
        # Next page starts after last candle open time
        next_cursor = last_open_ms + 1

        print(
            f"  fetched {len(batch):4d} rows "
            f"(total={len(rows):5d}) "
            f"last_open={datetime.fromtimestamp(last_open_ms / 1000, tz=timezone.utc).date()}"
        )

        if len(batch) < LIMIT:
            break
        if next_cursor <= cursor:
            raise RuntimeError(
                f"Pagination stuck: cursor did not advance (cursor={cursor}, next={next_cursor})"
            )
        cursor = next_cursor
        time.sleep(0.15)  # be polite to the public endpoint

    return rows


def klines_to_df(rows: list[list]) -> pd.DataFrame:
    # Binance kline: [open_time, open, high, low, close, volume, close_time, ...]
    records = []
    for r in rows:
        open_ms = int(r[0])
        records.append(
            {
                "date": datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc).strftime(
                    "%Y-%m-%d"
                ),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            }
        )
    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def main() -> None:
    print(f"Fetching {SYMBOL} {INTERVAL} from Binance (start_ms={START_MS})...")
    rows = fetch_all_klines()
    if not rows:
        raise RuntimeError("Binance returned zero klines — aborting without writing CSV.")

    df = klines_to_df(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nSaved {len(df)} rows -> {OUT_CSV}")
    print(f"Date range: {df['date'].iloc[0]} -> {df['date'].iloc[-1]}")
    print(df.head(3).to_string(index=False))
    print("...")
    print(df.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
