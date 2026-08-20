"""
fv1_ma_filter_yearwise.py
──────────────────────────────────────────────────────────────────
Year-wise PnL / trade count / CAGR for all 8 MA filter combos.
Produces TWO versions:
  - LAG    : filter uses PREVIOUS day close vs previous day MA
  - SAMEDAY: filter uses SAME day close vs same day MA

Outputs:
  outputs/stats/ma_filter_yearwise_lag.csv
  outputs/stats/ma_filter_yearwise_sameday.csv

Verification check: confirms Jan-Feb 2022 trades are included
(i.e., warmup gap is now resolved).
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[1]
DAILY_DIR  = BASE / "data" / "historical" / "daily"
TRADES_CSV = BASE / "outputs" / "trades" / "fv1_all_trades.csv"
OUT_DIR    = BASE / "outputs" / "stats"

# ── Best config per stock ────────────────────────────────────────
BEST_CFG = {
    "ADANIPORTS":"Extreme-2", "ASHOKLEY":"Extreme-4",  "AXISBANK":"Extreme-2",
    "BANDHANBNK":"Extreme-2", "BHARTIARTL":"Extreme-1","CIPLA":"Extreme-2",
    "COALINDIA":"Extreme-1",  "DABUR":"Extreme-3",     "DIVISLAB":"Extreme-4",
    "HDFCBANK":"Extreme-4",   "HINDALCO":"Extreme-4",  "ICICIBANK":"Extreme-4",
    "INDUSINDBK":"Extreme-4", "INFY":"Extreme-2",      "ITC":"Extreme-1",
    "JSWSTEEL":"Extreme-4",   "NATIONALUM":"Extreme-2","NTPC":"Extreme-2",
    "ONGC":"Extreme-2",       "PNB":"Extreme-2",       "POWERGRID":"Extreme-3",
    "RELIANCE":"Extreme-2",   "SBIN":"Extreme-1",      "SUNPHARMA":"Extreme-4",
    "TATAMOTORS":"Extreme-1", "TATASTEEL":"Extreme-2", "TECHM":"Extreme-2",
    "VEDL":"Extreme-4",       "WIPRO":"Extreme-1",
}

# ── Filter legend (printed once per table, not used in col names) ─
FILTER_LEGEND = {
    "F0": "No filter (baseline)",
    "F1": "close > MA50",
    "F2": "close > MA100",
    "F3": "close > MA200",
    "F4": "close > MA50 AND MA100",
    "F5": "close > MA50 AND MA200",
    "F6": "close > MA100 AND MA200",
    "F7": "close > MA50 AND MA100 AND MA200",
}
FILTERS = ["F0","F1","F2","F3","F4","F5","F6","F7"]

# ── Filter definitions ───────────────────────────────────────────
# Each filter returns a boolean Series given the joined DataFrame.
# Two flavours: _lag (prev day) and _sd (same day).

def make_filters(df, flavour="lag"):
    """Return dict of filter_name -> boolean mask."""
    if flavour == "lag":
        c   = df["prev_close"]
        m50 = df["prev_ma50"]
        m100= df["prev_ma100"]
        m200= df["prev_ma200"]
    else:  # sameday
        c   = df["close_d"]
        m50 = df["ma50"]
        m100= df["ma100"]
        m200= df["ma200"]

    valid = df["has_ma200"]   # trade date has full MA window

    return {
        "F0": pd.Series(True,  index=df.index),
        "F1": valid & (c > m50),
        "F2": valid & (c > m100),
        "F3": valid & (c > m200),
        "F4": valid & (c > m50)  & (c > m100),
        "F5": valid & (c > m50)  & (c > m200),
        "F6": valid & (c > m100) & (c > m200),
        "F7": valid & (c > m50)  & (c > m100) & (c > m200),
    }

# ── CAGR helper ──────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000   # Rs 10L notional baseline

def cagr(pnl_series_by_year: dict, n_years: int) -> float:
    """Simple CAGR over cumulative PnL from a flat capital base."""
    total_pnl = sum(pnl_series_by_year.values())
    final      = INITIAL_CAPITAL + total_pnl
    if final <= 0 or n_years == 0:
        return float("nan")
    return ((final / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100

# ── Step 1: Build daily MA table ─────────────────────────────────
def build_ma_table() -> pd.DataFrame:
    """
    Read all 29 stock daily parquets, compute MA50/100/200,
    then lag by 1 day to get prev_close / prev_maXX.
    Returns one big DataFrame with columns:
        stock, date, close_d, ma50, ma100, ma200,
        prev_close, prev_ma50, prev_ma100, prev_ma200,
        has_ma200 (bool: window row >= 200)
    """
    frames = []
    for stock in BEST_CFG:
        path = DAILY_DIR / f"{stock}.parquet"
        if not path.exists():
            print(f"  [WARN] Missing daily parquet: {stock}")
            continue
        df = pd.read_parquet(path)

        # Normalise datetime to date
        df["date"] = pd.to_datetime(df["datetime"]).dt.normalize().dt.tz_localize(None).dt.date

        df = df.sort_values("date").reset_index(drop=True)

        # Compute rolling MAs on close
        df["ma50"]  = df["close"].rolling(50,  min_periods=50).mean()
        df["ma100"] = df["close"].rolling(100, min_periods=100).mean()
        df["ma200"] = df["close"].rolling(200, min_periods=200).mean()

        # LAG versions (previous day)
        df["prev_close"] = df["close"].shift(1)
        df["prev_ma50"]  = df["ma50"].shift(1)
        df["prev_ma100"] = df["ma100"].shift(1)
        df["prev_ma200"] = df["ma200"].shift(1)

        # Flag rows where full 200-day window exists (same-day)
        df["has_ma200"]  = df["ma200"].notna()

        df["stock"]   = stock
        df["close_d"] = df["close"]   # alias for clarity

        frames.append(df[[
            "stock","date","close_d",
            "ma50","ma100","ma200",
            "prev_close","prev_ma50","prev_ma100","prev_ma200",
            "has_ma200",
        ]])

    print(f"Daily MA table built for {len(frames)} stocks.")
    return pd.concat(frames, ignore_index=True)


# ── Step 2: Load & filter trades to best config ──────────────────
def load_best_trades() -> pd.DataFrame:
    trades = pd.read_csv(TRADES_CSV)
    trades.columns = trades.columns.str.strip()

    # Keep only best config per stock
    best_df = pd.DataFrame(list(BEST_CFG.items()), columns=["stock","best_cfg"])
    trades = trades.merge(best_df, on="stock")
    trades = trades[trades["atr_config"] == trades["best_cfg"]].copy()

    # Extract trade_date (date only, no tz)
    trades["entry_dt"] = pd.to_datetime(trades["entry_time"])
    trades["trade_date"] = trades["entry_dt"].dt.normalize().dt.tz_localize(None).dt.date
    trades["year"] = trades["entry_dt"].dt.year

    print(f"Best-config trades: {len(trades):,}  |  "
          f"years: {sorted(trades['year'].unique())}")
    return trades


# ── Step 3: Run analysis ─────────────────────────────────────────
def run_analysis(trades: pd.DataFrame, ma_table: pd.DataFrame, flavour: str) -> pd.DataFrame:
    """
    flavour = 'lag' or 'sameday'
    Returns a DataFrame: rows = year/4yr | cols = F0..F7
    with sub-cols: pnl, trades, ret%
    """
    # Join on stock + trade_date
    joined = trades.merge(ma_table, left_on=["stock","trade_date"],
                          right_on=["stock","date"], how="left")

    # Any unmatched rows -> no MA data (shouldn't happen post-fix)
    unmatched = joined["has_ma200"].isna().sum()
    if unmatched:
        print(f"  [WARN] {flavour}: {unmatched} trades have no daily MA row (no filter applied).")
        joined["has_ma200"] = joined["has_ma200"].fillna(False)

    filters = make_filters(joined, flavour=flavour)
    years   = sorted(joined["year"].unique())

    rows = []
    yearly_pnl = {f: {} for f in filters}

    for yr in years:
        yr_mask = joined["year"] == yr
        row = {"Period": str(yr)}
        for fname, fmask in filters.items():
            sub = joined[yr_mask & fmask]
            pnl = sub["pnl"].sum()
            cnt = len(sub)
            yearly_pnl[fname][yr] = pnl
            row[f"{fname}_PnL"]    = round(pnl, 0)
            row[f"{fname}_Trades"] = cnt
        rows.append(row)

    # 4yr cumulative row
    row4 = {"Period": "4yr_CAGR"}
    for fname in filters:
        total_pnl = sum(yearly_pnl[fname].values())
        c = cagr(yearly_pnl[fname], n_years=len(years))
        total_t = sum(r[f"{fname}_Trades"] for r in rows if r["Period"].isdigit())
        row4[f"{fname}_PnL"]    = round(total_pnl, 0)
        row4[f"{fname}_Trades"] = total_t
        row4[f"{fname}_Ret%"]   = round(c, 2)
    rows.append(row4)

    # Add per-year Ret% (annual return vs flat capital)
    for r in rows:
        if r["Period"].isdigit():
            for fname in filters:
                pnl = r[f"{fname}_PnL"]
                r[f"{fname}_Ret%"] = round((pnl / INITIAL_CAPITAL) * 100, 2)

    return pd.DataFrame(rows)


# ── Step 4: Pretty-print summary ────────────────────────────────
def print_summary(df: pd.DataFrame, flavour: str):
    lag_note = "(prev day close vs prev day MA)" if flavour == "lag" else "(same day close vs same day MA)"
    print(f"\n  {flavour.upper()} {lag_note}")

    W = 9   # column width per filter cell (e.g. "-10.29%")
    header = f"{'Period':<12}" + "".join(f"{f:>{W}}" for f in FILTERS)
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for _, r in df.iterrows():
        line = f"  {r['Period']:<12}"
        for f in FILTERS:
            val = r.get(f"{f}_Ret%", 0)
            line += f"{val:>{W-1}.2f}%"
        print(line)


# ── Warmup verification ───────────────────────────────────────────
def verify_warmup(trades: pd.DataFrame, ma_table: pd.DataFrame):
    """Confirm Jan-Feb 2022 trades now have valid MA window."""
    early = trades[
        (trades["year"] == 2022) &
        (trades["trade_date"] < pd.Timestamp("2022-03-01").date())
    ]
    if early.empty:
        print("\n[VERIFY] No Jan-Feb 2022 trades found in best-config set.")
        return

    joined = early.merge(ma_table, left_on=["stock","trade_date"],
                         right_on=["stock","date"], how="left")
    has_window = joined["has_ma200"].fillna(False)
    print(f"\n[VERIFY] Jan-Feb 2022 best-config trades : {len(early):,}")
    print(f"         With valid MA200 window          : {has_window.sum():,}")
    print(f"         Missing MA window (excluded)     : {(~has_window).sum():,}")
    if (~has_window).sum() == 0:
        print("         STATUS: WARMUP GAP FULLY RESOLVED")
    else:
        print("         STATUS: WARNING -- some trades still outside window")


# ── Main ─────────────────────────────────────────────────────────
def main():
    print("Building daily MA table ...")
    ma_table = build_ma_table()

    print("\nLoading best-config trades ...")
    trades = load_best_trades()

    verify_warmup(trades, ma_table)

    for flavour in ("lag", "sameday"):
        print(f"\nRunning {flavour} analysis ...")
        result = run_analysis(trades, ma_table, flavour)

        out_path = OUT_DIR / f"ma_filter_yearwise_{flavour}.csv"
        result.to_csv(out_path, index=False)
        print(f"Saved: {out_path}")

        print_summary(result, flavour)

    print("\nDone.")


if __name__ == "__main__":
    main()
