"""
Append Kite 5-min / daily candles for 2026-01-01 .. 2026-07-31 onto DS3 parquets.
Reads staging JSON candle lists produced from kite MCP historical dumps.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytz

IST = pytz.FixedOffset(330)

ROOT = Path(__file__).resolve().parents[1]
DS3 = ROOT / "data" / "historical" / "intraday_5min_DS3"
DAILY = ROOT / "data" / "historical" / "daily"
STAGING = ROOT / "data" / "staging_ds3_2026"

FROM_TS = pd.Timestamp("2026-01-01 00:00:00")
TO_TS = pd.Timestamp("2026-07-31 23:59:59")

SYMBOLS = [
    "ADANIPORTS", "ASHOKLEY", "AXISBANK", "BAJFINANCE", "BANDHANBNK",
    "BHARTIARTL", "CIPLA", "COALINDIA", "DABUR", "DIVISLAB",
    "HDFCBANK", "HINDALCO", "ICICIBANK", "INDUSINDBK", "INFY",
    "ITC", "JSWSTEEL", "NATIONALUM", "NTPC", "ONGC",
    "PNB", "POWERGRID", "RELIANCE", "SBIN", "SUNPHARMA",
    "TATAMOTORS", "TATASTEEL", "TECHM", "VEDL", "WIPRO",
]

# instrument tokens (TATAMOTORS continuous via TMPV after rename/demerger)
TOKENS = {
    "ADANIPORTS": 3861249,
    "ASHOKLEY": 54273,
    "AXISBANK": 1510401,
    "BAJFINANCE": 81153,
    "BANDHANBNK": 579329,
    "BHARTIARTL": 2714625,
    "CIPLA": 177665,
    "COALINDIA": 5215745,
    "DABUR": 197633,
    "DIVISLAB": 2800641,
    "HDFCBANK": 341249,
    "HINDALCO": 348929,
    "ICICIBANK": 1270529,
    "INDUSINDBK": 1346049,
    "INFY": 408065,
    "ITC": 424961,
    "JSWSTEEL": 3001089,
    "NATIONALUM": 1629185,
    "NTPC": 2977281,
    "ONGC": 633601,
    "PNB": 2730497,
    "POWERGRID": 3834113,
    "RELIANCE": 738561,
    "SBIN": 779521,
    "SUNPHARMA": 857857,
    "TATAMOTORS": 884737,  # NSE:TMPV (same ISIN as old TATAMOTORS)
    "TATASTEEL": 895745,
    "TECHM": 3465729,
    "VEDL": 784129,
    "WIPRO": 969473,
    "NIFTY50": 256265,
}

# ~90-day chunks (kite 5min limit ~100 days)
CHUNKS_5MIN = [
    ("2026-01-01 09:15:00", "2026-04-01 15:30:00"),
    ("2026-04-02 09:15:00", "2026-07-01 15:30:00"),
    ("2026-07-02 09:15:00", "2026-07-31 15:30:00"),
]

CHUNK_DAILY = ("2026-01-01 00:00:00", "2026-07-31 23:59:59")


def load_candle_json(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "data" in raw:
        raw = raw["data"]
    if not isinstance(raw, list):
        raise ValueError(f"Unexpected JSON shape in {path}: {type(raw)}")
    return raw


def candles_to_df(candles: list[dict], tz_aware: bool = True) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame(
            columns=["datetime", "open", "high", "low", "close", "volume", "oi"]
        )
    df = pd.DataFrame(candles)
    # kite field is "date"
    if "date" in df.columns and "datetime" not in df.columns:
        df = df.rename(columns={"date": "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"])
    if tz_aware:
        if df["datetime"].dt.tz is None:
            df["datetime"] = df["datetime"].dt.tz_localize(IST)
        else:
            df["datetime"] = df["datetime"].dt.tz_convert(IST)
    else:
        # NIFTY daily existing file is naive
        if df["datetime"].dt.tz is not None:
            df["datetime"] = df["datetime"].dt.tz_convert(IST).dt.tz_localize(None)
        # normalize to midnight for daily
        df["datetime"] = df["datetime"].dt.normalize()

    for c in ("open", "high", "low", "close"):
        df[c] = df[c].astype(float)
    df["volume"] = df["volume"].fillna(0).astype(int)
    if "oi" not in df.columns:
        df["oi"] = 0
    df["oi"] = df["oi"].fillna(0).astype(int)
    df = df[["datetime", "open", "high", "low", "close", "volume", "oi"]]
    df = df.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
    # filter window
    lo = FROM_TS
    hi = TO_TS
    if tz_aware:
        lo = FROM_TS.tz_localize(IST)
        hi = TO_TS.tz_localize(IST)
    df = df[(df["datetime"] >= lo) & (df["datetime"] <= hi)]
    return df.reset_index(drop=True)


def add_ma20_atr14(df: pd.DataFrame) -> pd.DataFrame:
    """Match DS3: ma20 = rolling 20 close mean; atr14 = SMA(TR, 14)."""
    out = df.copy()
    out["ma20"] = out["close"].rolling(20, min_periods=20).mean()
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14"] = tr.rolling(14, min_periods=14).mean()
    return out


def expected_trading_days_approx() -> None:
    """Placeholder — real gap report uses observed dates."""
    pass


def collect_symbol_candles(symbol: str) -> pd.DataFrame:
    files = sorted(STAGING.glob(f"{symbol}_chunk*.json"))
    if not files:
        # also accept single dump
        files = sorted(STAGING.glob(f"{symbol}*.json"))
        files = [f for f in files if f.name != f"{symbol}_report.json"]
    all_c: list[dict] = []
    for f in files:
        all_c.extend(load_candle_json(f))
    return candles_to_df(all_c, tz_aware=True)


def append_stock(symbol: str) -> dict:
    path = DS3 / f"{symbol}.parquet"
    if not path.exists():
        return {"symbol": symbol, "error": f"missing file {path}"}

    existing = pd.read_parquet(path)
    old_rows = len(existing)
    old_last = existing["datetime"].iloc[-1]
    old_first = existing["datetime"].iloc[0]

    new_df = collect_symbol_candles(symbol)
    if new_df.empty:
        return {
            "symbol": symbol,
            "error": "no staging candles",
            "old_rows": old_rows,
            "old_last": str(old_last),
        }

    # only keep bars strictly after existing last
    new_df = new_df[new_df["datetime"] > old_last].copy()
    if new_df.empty:
        return {
            "symbol": symbol,
            "rows_added": 0,
            "note": "all fetched bars already present or not after old_last",
            "old_last": str(old_last),
            "fetch_first": str(collect_symbol_candles(symbol)["datetime"].iloc[0])
            if True
            else None,
            "final_first": str(old_first),
            "final_last": str(old_last),
            "final_rows": old_rows,
        }

    # recompute indicators on concat of tail of existing + new for continuity
    warmup = existing.tail(30).copy()
    # ensure same cols
    for c in ("ma20", "atr14"):
        if c in warmup.columns:
            warmup = warmup.drop(columns=[c])
    combined_calc = pd.concat([warmup, new_df], ignore_index=True)
    combined_calc = add_ma20_atr14(combined_calc)
    # take only the new portion
    new_with_ind = combined_calc.iloc[len(warmup) :].copy()
    new_with_ind = new_with_ind[
        ["datetime", "open", "high", "low", "close", "volume", "oi", "ma20", "atr14"]
    ]

    # existing already has indicators; keep them
    out = pd.concat([existing, new_with_ind], ignore_index=True)
    out = out.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
    out = out.reset_index(drop=True)

    # safety: never drop pre-2026 history
    assert out["datetime"].iloc[0] == old_first or out["datetime"].iloc[0] <= old_first
    assert len(out) >= old_rows

    out.to_parquet(path, index=False)

    # gap analysis: unique trading dates in new range
    dates = pd.to_datetime(new_with_ind["datetime"]).dt.date
    unique_days = sorted(set(dates))
    if len(unique_days) >= 2:
        all_biz = pd.bdate_range(unique_days[0], unique_days[-1])
        missing = [d.date() for d in all_biz if d.date() not in set(unique_days)]
        # filter known market holidays roughly — report all weekdays missing
    else:
        missing = []

    return {
        "symbol": symbol,
        "rows_added": len(new_with_ind),
        "old_rows": old_rows,
        "final_rows": len(out),
        "old_last": str(old_last),
        "new_first": str(new_with_ind["datetime"].iloc[0]),
        "new_last": str(new_with_ind["datetime"].iloc[-1]),
        "final_first": str(out["datetime"].iloc[0]),
        "final_last": str(out["datetime"].iloc[-1]),
        "trading_days_added": len(unique_days),
        "missing_weekdays_in_span": [str(d) for d in missing],
    }


def append_nifty() -> dict:
    path = DAILY / "NIFTY50.parquet"
    existing = pd.read_parquet(path)
    old_rows = len(existing)
    old_last = existing["datetime"].iloc[-1]
    old_first = existing["datetime"].iloc[0]

    files = sorted(STAGING.glob("NIFTY50*.json"))
    candles: list[dict] = []
    for f in files:
        candles.extend(load_candle_json(f))
    new_df = candles_to_df(candles, tz_aware=False)
    if new_df.empty:
        return {"symbol": "NIFTY50", "error": "no staging candles", "old_last": str(old_last)}

    # compare naive
    old_last_naive = pd.Timestamp(old_last)
    if getattr(old_last_naive, "tz", None) is not None:
        old_last_naive = old_last_naive.tz_localize(None)
    new_df = new_df[new_df["datetime"] > old_last_naive].copy()
    if new_df.empty:
        return {
            "symbol": "NIFTY50",
            "rows_added": 0,
            "note": "nothing new to append",
            "old_last": str(old_last),
            "final_rows": old_rows,
        }

    # match existing dtypes
    new_df = new_df[["datetime", "open", "high", "low", "close", "volume", "oi"]]
    out = pd.concat([existing, new_df], ignore_index=True)
    out = out.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
    out = out.reset_index(drop=True)
    out.to_parquet(path, index=False)

    dates = sorted(set(new_df["datetime"].dt.date))
    if len(dates) >= 2:
        all_biz = pd.bdate_range(dates[0], dates[-1])
        missing = [d.date() for d in all_biz if d.date() not in set(dates)]
    else:
        missing = []

    return {
        "symbol": "NIFTY50",
        "rows_added": len(new_df),
        "old_rows": old_rows,
        "final_rows": len(out),
        "old_last": str(old_last),
        "new_first": str(new_df["datetime"].iloc[0]),
        "new_last": str(new_df["datetime"].iloc[-1]),
        "final_first": str(out["datetime"].iloc[0]),
        "final_last": str(out["datetime"].iloc[-1]),
        "trading_days_added": len(dates),
        "missing_weekdays_in_span": [str(d) for d in missing],
    }


def ingest_mcp_file(mcp_path: str, dest_name: str) -> int:
    """Copy/normalize an MCP dump into staging as dest_name."""
    STAGING.mkdir(parents=True, exist_ok=True)
    src = Path(mcp_path)
    candles = load_candle_json(src)
    dest = STAGING / dest_name
    dest.write_text(json.dumps(candles), encoding="utf-8")
    return len(candles)


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "ingest":
        # ingest <mcp_json_path> <dest_name>
        n = ingest_mcp_file(argv[1], argv[2])
        print(f"ingested {n} candles -> {argv[2]}")
        return 0

    if len(argv) >= 1 and argv[0] == "status":
        for sym in SYMBOLS + ["NIFTY50"]:
            files = list(STAGING.glob(f"{sym}*.json"))
            print(f"{sym}: {len(files)} files {[f.name for f in files]}")
        return 0

    if len(argv) >= 1 and argv[0] == "append":
        STAGING.mkdir(parents=True, exist_ok=True)
        reports = []
        for sym in SYMBOLS:
            r = append_stock(sym)
            reports.append(r)
            print(json.dumps(r))
        r = append_nifty()
        reports.append(r)
        print(json.dumps(r))
        report_path = STAGING / "append_report.json"
        report_path.write_text(json.dumps(reports, indent=2), encoding="utf-8")
        print(f"report -> {report_path}")
        return 0

    if len(argv) >= 1 and argv[0] == "print_tokens":
        print(json.dumps(TOKENS, indent=2))
        print("CHUNKS_5MIN", CHUNKS_5MIN)
        return 0

    print("usage: append_ds3_2026_gap.py [ingest|status|append|print_tokens]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
