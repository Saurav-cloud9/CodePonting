"""
fv1_regime_filters_group2to5.py
Tests 14 prev-day features across 4 groups vs GT.
GT = F1 same-day (close > MA50) = +8.95% 4yr CAGR.
ALL features use PREVIOUS DAY values only - no lookahead.
Output: outputs/stats/regime_filters_group2to5.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

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

GT = {
    2022:       {"ret": 12.27, "trades": 10845},
    2023:       {"ret":  9.63, "trades": 12465},
    2024:       {"ret": 12.53, "trades": 11366},
    2025:       {"ret":  6.45, "trades": 10695},
    "4yr_CAGR": {"ret":  8.95, "trades": 45371},
}

GROUPS = {
    "Volatility":      ["VF1", "VF2", "VF3"],
    "Trend Strength":  ["TF1", "TF2", "TF3", "TF4"],
    "Volume":          ["VL1", "VL2"],
    "Market-Wide":     ["MF1", "MF2", "MF3", "MF4", "MF5"],
}
ALL_FILTERS = [f for grp in GROUPS.values() for f in grp]

FILTER_DESCS = {
    "VF1": "prev_atr_ratio < per-stock median  (low vol day)",
    "VF2": "prev_range_ratio < per-stock median (tight range)",
    "VF3": "prev_body_ratio > 0.5              (conviction candle)",
    "TF1": "MA50 slope > 0                     (MA50 rising)",
    "TF2": "prev_MA50 > prev_MA100             (MA50 above MA100)",
    "TF3": "prev_MA50 > prev_MA200             (MA50 above MA200)",
    "TF4": "price_dist_MA50 in [-2%, +5%]      (near MA50)",
    "VL1": "prev_vol_ratio > 1 AND bullish      (high-vol up day)",
    "VL2": "prev_vol_ratio < 1                  (quiet/follow-through)",
    "MF1": "nifty prev_close > nifty prev_MA50  (market uptrend)",
    "MF2": "nifty 1-week return > 0             (market positive)",
    "MF3": "nifty atr_ratio < median            (market calm)",
    "MF4": "mean_stock_vol_ratio >= 1            (portfolio active/busy — NIFTY vol=0)",
    "MF5": "MF1 AND MF2 combo",
}


# ── Feature builders ─────────────────────────────────────────────
def build_stock_features() -> pd.DataFrame:
    frames = []
    for stock in BEST_CFG:
        path = DAILY_DIR / f"{stock}.parquet"
        if not path.exists():
            print(f"  [WARN] Missing: {stock}")
            continue
        df = pd.read_parquet(path)
        df["date"] = pd.to_datetime(df["datetime"]).dt.normalize().dt.tz_localize(None).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        df["ma50"]      = df["close"].rolling(50,  min_periods=50).mean()
        df["ma100"]     = df["close"].rolling(100, min_periods=100).mean()
        df["ma200"]     = df["close"].rolling(200, min_periods=200).mean()
        df["atr14"]     = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
        df["vol_avg20"] = df["volume"].rolling(20, min_periods=20).mean()
        df["ma50_5d"]   = df["ma50"].shift(5)     # ma50 value 5 days ago (before lag)

        df["prev_close"]      = df["close"].shift(1)
        df["prev_open"]       = df["open"].shift(1)
        df["prev_high"]       = df["high"].shift(1)
        df["prev_low"]        = df["low"].shift(1)
        df["prev_volume"]     = df["volume"].shift(1)
        df["prev_ma50"]       = df["ma50"].shift(1)
        df["prev_ma100"]      = df["ma100"].shift(1)
        df["prev_ma200"]      = df["ma200"].shift(1)
        df["prev_atr14"]      = df["atr14"].shift(1)
        df["prev_vol_avg20"]  = df["vol_avg20"].shift(1)
        df["prev_ma50_5d"]    = df["ma50_5d"].shift(1)   # ma50 as of 6 days ago

        df["prev_atr_ratio"]   = df["prev_atr14"] / df["prev_close"]
        df["prev_range_ratio"] = (df["prev_high"] - df["prev_low"]) / df["prev_close"]
        body = (df["prev_close"] - df["prev_open"]).abs()
        rng  = (df["prev_high"] - df["prev_low"]).replace(0, np.nan)
        df["prev_body_ratio"]  = body / rng
        df["prev_vol_ratio"]   = df["prev_volume"] / df["prev_vol_avg20"].replace(0, np.nan)
        df["ma50_slope"]       = df["prev_ma50"] - df["prev_ma50_5d"]
        df["price_dist_ma50"]  = (df["prev_close"] - df["prev_ma50"]) / df["prev_ma50"]

        df["stock"] = stock
        frames.append(df[["stock","date","prev_close","prev_open",
                           "prev_ma50","prev_ma100","prev_ma200",
                           "prev_atr_ratio","prev_range_ratio","prev_body_ratio",
                           "prev_vol_ratio","ma50_slope","price_dist_ma50"]])

    print(f"Stock feature table built for {len(frames)} stocks.")
    return pd.concat(frames, ignore_index=True)


def build_nifty_features() -> pd.DataFrame:
    df = pd.read_parquet(DAILY_DIR / "NIFTY50.parquet")
    df["date"] = pd.to_datetime(df["datetime"]).dt.normalize().dt.tz_localize(None).dt.date
    df = df.sort_values("date").reset_index(drop=True)

    df["ma50"]      = df["close"].rolling(50, min_periods=50).mean()
    df["atr14"]     = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
    df["vol_avg20"] = df["volume"].rolling(20, min_periods=20).mean()
    df["close_5d"]  = df["close"].shift(5)

    df["nifty_prev_close"]     = df["close"].shift(1)
    df["nifty_prev_ma50"]      = df["ma50"].shift(1)
    df["nifty_prev_volume"]    = df["volume"].shift(1)
    df["nifty_prev_vol_avg20"] = df["vol_avg20"].shift(1)
    df["nifty_prev_atr14"]     = df["atr14"].shift(1)
    df["nifty_prev_close_5d"]  = df["close_5d"].shift(1)   # close 6 days ago

    df["nifty_atr_ratio"]   = df["nifty_prev_atr14"] / df["nifty_prev_close"]
    df["nifty_week_return"] = (df["nifty_prev_close"] - df["nifty_prev_close_5d"]) / df["nifty_prev_close_5d"]
    # nifty_vol_ratio dropped — NIFTY50 is an index, volume is always 0

    print("NIFTY50 feature table built.")
    return df[["date","nifty_prev_close","nifty_prev_ma50",
               "nifty_atr_ratio","nifty_week_return"]]


def build_mkt_vol_proxy(sf: pd.DataFrame) -> pd.DataFrame:
    """
    MF4 proxy: NIFTY50 has no volume (index data).
    Use mean prev_vol_ratio across all 29 stocks per date instead.
    A value < 1 means the market is generally quieter than its 20d avg.
    """
    proxy = (sf.groupby("date")["prev_vol_ratio"]
               .mean()
               .reset_index()
               .rename(columns={"prev_vol_ratio": "mkt_vol_ratio"}))
    print(f"Market vol proxy built: {len(proxy)} dates.")
    return proxy


def compute_medians(sf: pd.DataFrame) -> pd.DataFrame:
    return (sf.groupby("stock")[["prev_atr_ratio","prev_range_ratio"]]
              .median()
              .rename(columns={"prev_atr_ratio":"med_atr_ratio",
                               "prev_range_ratio":"med_range_ratio"})
              .reset_index())


def load_best_trades() -> pd.DataFrame:
    trades = pd.read_csv(TRADES_CSV)
    trades.columns = trades.columns.str.strip()
    best_df = pd.DataFrame(list(BEST_CFG.items()), columns=["stock","best_cfg"])
    trades  = trades.merge(best_df, on="stock")
    trades  = trades[trades["atr_config"] == trades["best_cfg"]].copy()
    trades["entry_dt"]   = pd.to_datetime(trades["entry_time"])
    trades["trade_date"] = trades["entry_dt"].dt.normalize().dt.tz_localize(None).dt.date
    trades["year"]       = trades["entry_dt"].dt.year
    print(f"Best-config trades: {len(trades):,}")
    return trades


# ── Filter masks ──────────────────────────────────────────────────
def make_filters(df: pd.DataFrame) -> dict:
    pc   = df["prev_close"];  po   = df["prev_open"]
    m50  = df["prev_ma50"];   m100 = df["prev_ma100"]; m200 = df["prev_ma200"]
    atr  = df["prev_atr_ratio"];  rng  = df["prev_range_ratio"]
    body = df["prev_body_ratio"]; vr   = df["prev_vol_ratio"]
    slp  = df["ma50_slope"];      dist = df["price_dist_ma50"]
    npc  = df["nifty_prev_close"]; nm50 = df["nifty_prev_ma50"]
    natr = df["nifty_atr_ratio"];  nvr  = df["mkt_vol_ratio"]   # portfolio mean vol ratio
    nwr  = df["nifty_week_return"]
    med_atr  = df["med_atr_ratio"]
    med_rng  = df["med_range_ratio"]
    nifty_med_atr = natr.median()

    return {
        "VF1": atr.notna()  & med_atr.notna()  & (atr  < med_atr),
        "VF2": rng.notna()  & med_rng.notna()  & (rng  < med_rng),
        "VF3": body.notna() & (body > 0.5),
        "TF1": slp.notna()  & (slp  > 0),
        "TF2": m50.notna()  & m100.notna() & (m50  > m100),
        "TF3": m50.notna()  & m200.notna() & (m50  > m200),
        "TF4": dist.notna() & (dist >= -0.02) & (dist <= 0.05),
        "VL1": vr.notna()   & (vr > 1) & (pc > po),
        "VL2": vr.notna()   & (vr < 1),
        "MF1": npc.notna()  & nm50.notna()  & (npc > nm50),
        "MF2": nwr.notna()  & (nwr > 0),
        "MF3": natr.notna() & (natr < nifty_med_atr),
        "MF4": nvr.notna()  & (nvr >= 1),
        "MF5": npc.notna()  & nm50.notna() & nwr.notna() & (npc > nm50) & (nwr > 0),
    }


def cagr_pct(yearly_pnl: dict, n_years: int) -> float:
    total = sum(yearly_pnl.values())
    final = INITIAL_CAPITAL + total
    if final <= 0 or n_years == 0:
        return float("nan")
    return ((final / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100


# ── Sweep ─────────────────────────────────────────────────────────
def run_sweep(trades, sf, nf, medians, mkt_vol) -> pd.DataFrame:
    sf2    = sf.merge(medians, on="stock", how="left")
    joined = trades.merge(sf2, left_on=["stock","trade_date"],
                          right_on=["stock","date"], how="left")
    joined = joined.merge(nf,      left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_nifty"))
    joined = joined.merge(mkt_vol, left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_mkvol"))

    filters    = make_filters(joined)
    years      = sorted(joined["year"].unique())
    rows       = []
    yearly_pnl = {f: {} for f in ALL_FILTERS}

    for yr in years:
        yr_mask = joined["year"] == yr
        row = {"Period": str(yr)}
        for fname in ALL_FILTERS:
            fmask = filters[fname].fillna(False)
            sub   = joined[yr_mask & fmask]
            pnl   = sub["pnl"].sum()
            cnt   = len(sub)
            yearly_pnl[fname][yr] = pnl
            row[f"{fname}_PnL"]    = round(pnl, 0)
            row[f"{fname}_Trades"] = cnt
            row[f"{fname}_Ret%"]   = round((pnl / INITIAL_CAPITAL) * 100, 2)
        rows.append(row)

    row4 = {"Period": "4yr_CAGR"}
    for fname in ALL_FILTERS:
        total_pnl = sum(yearly_pnl[fname].values())
        c         = cagr_pct(yearly_pnl[fname], n_years=len(years))
        total_t   = sum(r[f"{fname}_Trades"] for r in rows)
        row4[f"{fname}_PnL"]    = round(total_pnl, 0)
        row4[f"{fname}_Trades"] = total_t
        row4[f"{fname}_Ret%"]   = round(c, 2)
    rows.append(row4)

    return pd.DataFrame(rows)


# ── Print ─────────────────────────────────────────────────────────
def print_table(df: pd.DataFrame):
    W = 18
    for grp_name, grp_filters in GROUPS.items():
        cols = ["GT"] + grp_filters
        print(f"\n  [{grp_name}]")
        print(f"  {'Period':<12}" + "".join(f"{c:>{W}}" for c in cols))
        print(f"  {'-' * (12 + W * len(cols))}")
        for _, r in df.iterrows():
            period  = r["Period"]
            gt_key  = int(period) if period.isdigit() else "4yr_CAGR"
            gt_ret  = GT[gt_key]["ret"]
            gt_t    = GT[gt_key]["trades"]
            gt_sign = "+" if gt_ret >= 0 else ""
            gt_cell = f"{gt_sign}{gt_ret:.2f}% ({gt_t:,})"
            line    = f"  {period:<12}" + f"{gt_cell:>{W}}"
            for fname in grp_filters:
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
    print("Building stock feature table ...")
    sf = build_stock_features()

    print("Building NIFTY50 feature table ...")
    nf = build_nifty_features()

    print("Computing per-stock medians ...")
    med = compute_medians(sf)

    print("Building market volume proxy (replaces NIFTY vol) ...")
    mkt_vol = build_mkt_vol_proxy(sf)

    print("Loading best-config trades ...")
    trades = load_best_trades()

    print("Running sweep ...")
    result = run_sweep(trades, sf, nf, med, mkt_vol)

    out_path = OUT_DIR / "regime_filters_group2to5.csv"
    result.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

    print_table(result)
    print("\nDone.")


if __name__ == "__main__":
    main()
