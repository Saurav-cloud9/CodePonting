"""
fv1_regime_signal_sweep.py
──────────────────────────────────────────────────────────────────
Tests 9 prev-day price-based regime filters vs Ground Truth.
GT = F1 same-day (close > MA50) = +8.95% 4yr CAGR.

ALL filters use PREVIOUS DAY values only — no lookahead.

Filter Legend:
  PF1 : prev_close > prev_MA50
  PF2 : prev_close > prev_MA100
  PF3 : prev_close > prev_MA200
  PF4 : prev_close > prev_open        (bullish candle yesterday)
  PF5 : 1-week return > 0             (5d)
  PF6 : 2-week return > 0             (10d)
  PF7 : 1-month return > 0            (22d)
  PF8 : close / 52w_high > 0.85       (within 15% of peak)
  PF9 : close / 52w_low  > 1.10       (at least 10% above trough)

Outputs:
  outputs/stats/regime_signal_sweep.csv
"""

import pandas as pd
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[1]
DAILY_DIR  = BASE / "data" / "historical" / "daily"
TRADES_CSV = BASE / "outputs" / "trades" / "fv1_all_trades.csv"
OUT_DIR    = BASE / "outputs" / "stats"

INITIAL_CAPITAL = 1_000_000

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

# GT = F1 same-day results (from ma_filter_yearwise_sameday.csv)
GT = {
    2022:      {"ret": 12.27, "trades": 10845},
    2023:      {"ret":  9.63, "trades": 12465},
    2024:      {"ret": 12.53, "trades": 11366},
    2025:      {"ret":  6.45, "trades": 10695},
    "4yr_CAGR":{"ret":  8.95, "trades": 45371},
}

FILTER_DESCS = {
    "PF1": "prev_close > prev_MA50",
    "PF2": "prev_close > prev_MA100",
    "PF3": "prev_close > prev_MA200",
    "PF4": "prev_close > prev_open  (bullish candle)",
    "PF5": "1-week return > 0  (5d)",
    "PF6": "2-week return > 0  (10d)",
    "PF7": "1-month return > 0 (22d)",
    "PF8": "close / 52w_high > 0.85",
    "PF9": "close / 52w_low  > 1.10",
}
FILTER_NAMES = list(FILTER_DESCS.keys())


# ── Step 1: Build prev-day feature table ─────────────────────────
def build_feature_table() -> pd.DataFrame:
    frames = []
    for stock in BEST_CFG:
        path = DAILY_DIR / f"{stock}.parquet"
        if not path.exists():
            print(f"  [WARN] Missing: {stock}")
            continue
        df = pd.read_parquet(path)
        df["date"] = pd.to_datetime(df["datetime"]).dt.normalize().dt.tz_localize(None).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        # Rolling MAs
        df["ma50"]  = df["close"].rolling(50,  min_periods=50).mean()
        df["ma100"] = df["close"].rolling(100, min_periods=100).mean()
        df["ma200"] = df["close"].rolling(200, min_periods=200).mean()

        # 52-week rolling high / low (252 trading days)
        df["rolling_52w_high"] = df["high"].rolling(252, min_periods=1).max()
        df["rolling_52w_low"]  = df["low"].rolling(252,  min_periods=1).min()

        # All prev-day LAG features
        df["prev_close"]     = df["close"].shift(1)
        df["prev_open"]      = df["open"].shift(1)
        df["prev_ma50"]      = df["ma50"].shift(1)
        df["prev_ma100"]     = df["ma100"].shift(1)
        df["prev_ma200"]     = df["ma200"].shift(1)
        df["prev_close_5d"]  = df["close"].shift(5)
        df["prev_close_10d"] = df["close"].shift(10)
        df["prev_close_22d"] = df["close"].shift(22)
        df["prev_52w_high"]  = df["rolling_52w_high"].shift(1)
        df["prev_52w_low"]   = df["rolling_52w_low"].shift(1)

        df["stock"] = stock
        frames.append(df[[
            "stock", "date",
            "prev_close", "prev_open",
            "prev_ma50", "prev_ma100", "prev_ma200",
            "prev_close_5d", "prev_close_10d", "prev_close_22d",
            "prev_52w_high", "prev_52w_low",
        ]])

    print(f"Feature table built for {len(frames)} stocks.")
    return pd.concat(frames, ignore_index=True)


# ── Step 2: Filter masks ──────────────────────────────────────────
def make_filters(df: pd.DataFrame) -> dict:
    pc  = df["prev_close"]
    po  = df["prev_open"]
    m50 = df["prev_ma50"]
    m100= df["prev_ma100"]
    m200= df["prev_ma200"]
    r5  = df["prev_close_5d"]
    r10 = df["prev_close_10d"]
    r22 = df["prev_close_22d"]
    h52 = df["prev_52w_high"]
    l52 = df["prev_52w_low"]

    return {
        "PF1": m50.notna()  & (pc > m50),
        "PF2": m100.notna() & (pc > m100),
        "PF3": m200.notna() & (pc > m200),
        "PF4": po.notna()   & (pc > po),
        "PF5": r5.notna()   & ((pc - r5)  / r5  > 0),
        "PF6": r10.notna()  & ((pc - r10) / r10 > 0),
        "PF7": r22.notna()  & ((pc - r22) / r22 > 0),
        "PF8": h52.notna()  & (pc / h52 > 0.85),
        "PF9": l52.notna()  & (pc / l52 > 1.10),
    }


# ── Step 3: Load best-config trades ──────────────────────────────
def load_best_trades() -> pd.DataFrame:
    trades = pd.read_csv(TRADES_CSV)
    trades.columns = trades.columns.str.strip()
    best_df = pd.DataFrame(list(BEST_CFG.items()), columns=["stock", "best_cfg"])
    trades  = trades.merge(best_df, on="stock")
    trades  = trades[trades["atr_config"] == trades["best_cfg"]].copy()
    trades["entry_dt"]   = pd.to_datetime(trades["entry_time"])
    trades["trade_date"] = trades["entry_dt"].dt.normalize().dt.tz_localize(None).dt.date
    trades["year"]       = trades["entry_dt"].dt.year
    print(f"Best-config trades: {len(trades):,}")
    return trades


def cagr_pct(yearly_pnl: dict, n_years: int) -> float:
    total = sum(yearly_pnl.values())
    final = INITIAL_CAPITAL + total
    if final <= 0 or n_years == 0:
        return float("nan")
    return ((final / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100


# ── Step 4: Run sweep ─────────────────────────────────────────────
def run_sweep(trades: pd.DataFrame, feat: pd.DataFrame) -> pd.DataFrame:
    joined  = trades.merge(feat, left_on=["stock", "trade_date"],
                           right_on=["stock", "date"], how="left")
    filters = make_filters(joined)
    years   = sorted(joined["year"].unique())

    rows       = []
    yearly_pnl = {f: {} for f in FILTER_NAMES}

    for yr in years:
        yr_mask = joined["year"] == yr
        row = {"Period": str(yr)}
        for fname in FILTER_NAMES:
            fmask = filters[fname].fillna(False)
            sub   = joined[yr_mask & fmask]
            pnl   = sub["pnl"].sum()
            cnt   = len(sub)
            yearly_pnl[fname][yr] = pnl
            row[f"{fname}_PnL"]    = round(pnl, 0)
            row[f"{fname}_Trades"] = cnt
            row[f"{fname}_Ret%"]   = round((pnl / INITIAL_CAPITAL) * 100, 2)
        rows.append(row)

    # 4yr cumulative row
    row4 = {"Period": "4yr_CAGR"}
    for fname in FILTER_NAMES:
        total_pnl = sum(yearly_pnl[fname].values())
        c         = cagr_pct(yearly_pnl[fname], n_years=len(years))
        total_t   = sum(r[f"{fname}_Trades"] for r in rows)
        row4[f"{fname}_PnL"]    = round(total_pnl, 0)
        row4[f"{fname}_Trades"] = total_t
        row4[f"{fname}_Ret%"]   = round(c, 2)
    rows.append(row4)

    return pd.DataFrame(rows)


# ── Step 5: Print table ───────────────────────────────────────────
def print_table(df: pd.DataFrame):
    W = 18   # cell width: "+12.27% (10,845)"

    print("\n  Prev-Day Price Filters vs GT  (GT = F1 same-day: close > MA50)")
    print(f"  {'Period':<12}" + "".join(f"{'GT':>{W}}")
          + "".join(f"{f:>{W}}" for f in FILTER_NAMES))
    print(f"  {'-' * (12 + W * (1 + len(FILTER_NAMES)))}")

    for _, r in df.iterrows():
        period  = r["Period"]
        gt_key  = int(period) if period.isdigit() else "4yr_CAGR"
        gt_ret  = GT[gt_key]["ret"]
        gt_t    = GT[gt_key]["trades"]
        gt_sign = "+" if gt_ret >= 0 else ""
        gt_cell = f"{gt_sign}{gt_ret:.2f}% ({gt_t:,})"
        line    = f"  {period:<12}" + f"{gt_cell:>{W}}"

        for fname in FILTER_NAMES:
            ret  = r.get(f"{fname}_Ret%", 0.0)
            t    = int(r.get(f"{fname}_Trades", 0))
            sign = "+" if ret >= 0 else ""
            cell = f"{sign}{ret:.2f}% ({t:,})"
            line += f"{cell:>{W}}"

        print(line)

    print(f"\n  Filter Legend:")
    for fname, desc in FILTER_DESCS.items():
        print(f"    {fname} : {desc}")


# ── Main ──────────────────────────────────────────────────────────
def main():
    print("Building feature table ...")
    feat = build_feature_table()

    print("Loading best-config trades ...")
    trades = load_best_trades()

    print("Running sweep ...")
    result = run_sweep(trades, feat)

    out_path = OUT_DIR / "regime_signal_sweep.csv"
    result.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

    print_table(result)
    print("\nDone.")


if __name__ == "__main__":
    main()
