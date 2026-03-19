"""
run_step5_ds3_full.py — Step 5: Full DS3 Backtest 2015-2025
============================================================
Runs the Step 3.2 winner config (Extreme-2, SL=A, PG+CP+AF) on the full
DS3 dataset (2015-2025, 11 years), with and without the Trial #2827 regime
filter (PF9 + TF4, OR gate).

No year filter applied before computing indicators — full 11-year history.
Does NOT touch optuna_study.db, best_params.json, or any cached parquet.

Output: year-by-year raw PnL + 11yr CAGR for both baseline and filtered.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import time
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path

SANDBOX_DIR = Path(__file__).resolve().parents[1]
FV1_DIR     = SANDBOX_DIR.parent
DS3_DIR     = FV1_DIR / "data" / "historical" / "intraday_5min_DS3"
DAILY_DIR   = FV1_DIR / "data" / "historical" / "daily"
OUT_DIR     = SANDBOX_DIR / "outputs" / "optuna"
BEST_JSON   = OUT_DIR / "best_params.json"

sys.path.insert(0, str(SANDBOX_DIR))
from core.indicators import add_intraday_indicators, add_atr

# ── Constants (winner config) ────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
YEARS           = 11     # 2015-2025
NUM_STOCKS      = 30
ATR_MULT_STOP   = 2.5
RR_TARGET       = 4.5 / 2.5
RISK_PER_TRADE  = 0.01
VOL_MULT        = 1.2
LOOKAHEAD       = 3
_TICK           = 0.05
_EOD_INT        = 1500
_CUTOFF_INT     = 1430
_AUCTION_INT    = 945

STOCKS = [
    "ADANIPORTS", "ASHOKLEY",   "AXISBANK",   "BANDHANBNK", "BHARTIARTL",
    "CIPLA",      "COALINDIA",  "DABUR",       "DIVISLAB",   "HDFCBANK",
    "HINDALCO",   "ICICIBANK",  "INDUSINDBK",  "INFY",       "ITC",
    "JSWSTEEL",   "NATIONALUM", "NTPC",         "ONGC",       "PNB",
    "POWERGRID",  "RELIANCE",   "SBIN",         "SUNPHARMA",  "TATAMOTORS",
    "TATASTEEL",  "TECHM",      "VEDL",         "WIPRO",
]

ALL_FILTERS = [
    "PF1","PF2","PF3","PF4","PF5","PF6","PF7","PF8","PF9","PF10",
    "VF1","VF2","VF3",
    "TF1","TF2","TF3","TF4","TF5",
    "VL1","VL2",
    "MF1","MF2","MF3","MF4","MF5","MF6","MF7",
    "SF1",
]

ALL_YEARS = list(range(2015, 2026))


# ── Step 1: Build all trades (2015-2025, no year filter) ─────────────────────
def build_all_trades() -> pd.DataFrame:
    print("Building winner trades (full DS3, 2015-2025) ...")
    all_trades = []
    stock_files = sorted(f for f in DS3_DIR.glob("*.parquet") if f.stem in set(STOCKS))
    print(f"  {len(stock_files)} stock files found.")

    for path in stock_files:
        stock = path.stem

        df = pd.read_parquet(path)
        df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
        df = df.sort_values("datetime").reset_index(drop=True)

        # Market hours only — NO year filter
        _t = df["datetime"].dt.time
        df = df[_t.between(pd.Timestamp("09:15").time(),
                           pd.Timestamp("15:30").time())].reset_index(drop=True)

        df = add_intraday_indicators(df)
        df = add_atr(df)

        if df.empty:
            continue

        dti      = pd.DatetimeIndex(df["datetime"])
        date_int = (dti.year * 10000 + dti.month * 100 + dti.day).to_numpy()
        time_int = (dti.hour * 100 + dti.minute).to_numpy()
        open_arr  = df["open"].to_numpy(dtype=float)
        high_arr  = df["high"].to_numpy(dtype=float)
        low_arr   = df["low"].to_numpy(dtype=float)
        close_arr = df["close"].to_numpy(dtype=float)
        atr_arr   = df["atr_14"].to_numpy(dtype=float)
        ma20_arr  = df["ma20"].to_numpy(dtype=float)
        avg_vol   = df["avg_volume"].to_numpy(dtype=float)
        vol_arr   = df["volume"].to_numpy(dtype=float)
        dt_arr    = df["datetime"].to_numpy()
        n         = len(df)

        # Signal generation (AF=True, EC=False 14:30)
        signal_map = {}
        for i in range(0, n - 3):
            if np.isnan(ma20_arr[i]):
                continue
            if not np.isnan(avg_vol[i]) and vol_arr[i] < avg_vol[i] * VOL_MULT:
                continue
            if low_arr[i] <= ma20_arr[i]:
                ma_touch = ma20_arr[i]
                for j in range(i, min(i + LOOKAHEAD + 1, n)):
                    if close_arr[j] > ma_touch:
                        nxt = j + 1
                        if nxt >= n:
                            break
                        t_nxt = time_int[nxt]
                        if t_nxt >= _CUTOFF_INT:
                            break
                        if t_nxt < _AUCTION_INT:
                            break
                        if nxt not in signal_map:
                            signal_map[nxt] = open_arr[nxt]
                        break

        if not signal_map:
            continue

        cash      = INITIAL_CAPITAL
        positions = []

        for i in range(n):
            op  = open_arr[i];  hi  = high_arr[i]
            lo  = low_arr[i];   cl  = close_arr[i]
            atr = atr_arr[i];   d   = date_int[i];  t   = time_int[i]

            if i in signal_map and not positions:
                entry = signal_map[i] + _TICK
                sd    = atr * ATR_MULT_STOP
                if sd <= 0 or np.isnan(sd):
                    sd = entry * 0.01
                eq          = cash
                risk_amt    = eq * RISK_PER_TRADE
                per_stk_cap = eq / NUM_STOCKS
                qty = max(min(int(per_stk_cap / entry), int(risk_amt / sd)), 1)
                positions.append([i, d, entry, qty,
                                   entry - sd, entry + sd * RR_TARGET, dt_arr[i]])

            if not positions:
                continue

            is_bull = cl > op
            kept    = []
            for pos in positions:
                if pos[0] == i:
                    kept.append(pos)
                    continue
                if d == pos[1] and t >= _EOD_INT:
                    exit_p = op
                else:
                    stop = pos[4]; target = pos[5]; exit_p = None
                    if is_bull:
                        if lo <= stop:      exit_p = stop - _TICK
                        elif hi >= target:  exit_p = target
                    else:
                        if hi >= target:    exit_p = target
                        elif lo <= stop:    exit_p = stop - _TICK
                if exit_p is not None:
                    raw_pnl = (exit_p - pos[2]) * pos[3]
                    cash   += raw_pnl
                    entry_dt = pd.Timestamp(pos[6])
                    all_trades.append({
                        "stock"      : stock,
                        "entry_time" : entry_dt,
                        "trade_date" : entry_dt.date(),
                        "year"       : entry_dt.year,
                        "raw_pnl"    : raw_pnl,
                    })
                else:
                    kept.append(pos)
            positions = kept

    df_out = pd.DataFrame(all_trades)
    print(f"  Done: {len(df_out):,} trades across {df_out['stock'].nunique()} stocks "
          f"({df_out['year'].min()}-{df_out['year'].max()})")
    return df_out


# ── Step 2: Build feature table (stock + NIFTY daily, all years) ─────────────
def build_features(trades: pd.DataFrame) -> pd.DataFrame:
    print("Building stock features (all years) ...")
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

        prev_close = df["close"].shift(1);  prev_open  = df["open"].shift(1)
        prev_high  = df["high"].shift(1);   prev_low   = df["low"].shift(1)
        prev_vol   = df["volume"].shift(1); prev_ma50  = df["ma50"].shift(1)
        prev_ma100 = df["ma100"].shift(1);  prev_ma200 = df["ma200"].shift(1)
        prev_atr14 = df["atr14"].shift(1);  prev_va20  = df["vol_avg20"].shift(1)
        prev_ma50_5= df["ma50_5d"].shift(1)
        prev_52h   = df["r52w_high"].shift(1)
        prev_52l   = df["r52w_low"].shift(1)

        df["p_close"] = prev_close; df["p_open"]  = prev_open
        df["p_ma50"]  = prev_ma50;  df["p_ma100"] = prev_ma100
        df["p_ma200"] = prev_ma200
        df["p_r52w_high"] = prev_52h; df["p_r52w_low"] = prev_52l
        df["p_close_5d"]  = df["close"].shift(5)
        df["p_close_10d"] = df["close"].shift(10)
        df["p_close_22d"] = df["close"].shift(22)

        df["p_atr_ratio"]   = prev_atr14 / prev_close
        df["p_range_ratio"] = (prev_high - prev_low) / prev_close
        body_sz = (prev_close - prev_open).abs()
        rng_sz  = (prev_high - prev_low).replace(0, np.nan)
        df["p_body_ratio"]  = body_sz / rng_sz
        df["p_vol_ratio"]   = prev_vol / prev_va20.replace(0, np.nan)
        df["ma50_slope"]    = prev_ma50 - prev_ma50_5
        df["dist_ma50"]     = (prev_close - prev_ma50) / prev_ma50
        df["stock"] = stock
        frames.append(df[["stock","date","p_close","p_open","p_ma50","p_ma100","p_ma200",
                           "p_atr_ratio","p_range_ratio","p_body_ratio","p_vol_ratio",
                           "ma50_slope","dist_ma50","p_close_5d","p_close_10d","p_close_22d",
                           "p_r52w_high","p_r52w_low"]])

    sf = pd.concat(frames, ignore_index=True)
    print(f"  Stock features: {len(sf):,} rows across {sf['stock'].nunique()} stocks.")

    print("Building NIFTY50 features (all years) ...")
    ndf = pd.read_parquet(DAILY_DIR / "NIFTY50.parquet")
    ndf["date"] = pd.to_datetime(ndf["datetime"]).dt.normalize().dt.tz_localize(None).dt.date
    ndf = ndf.sort_values("date").reset_index(drop=True)
    ndf["ma50"]     = ndf["close"].rolling(50, min_periods=50).mean()
    ndf["atr14"]    = (ndf["high"] - ndf["low"]).rolling(14, min_periods=14).mean()
    ndf["close_5d"] = ndf["close"].shift(5)
    ndf["n_close"]    = ndf["close"].shift(1)
    ndf["n_ma50"]     = ndf["ma50"].shift(1)
    ndf["n_atr14"]    = ndf["atr14"].shift(1)
    ndf["n_close_6d"] = ndf["close_5d"].shift(1)
    ndf["n_atr_ratio"] = ndf["n_atr14"] / ndf["n_close"]
    ndf["n_week_ret"]  = (ndf["n_close"] - ndf["n_close_6d"]) / ndf["n_close_6d"]
    nf = ndf[["date","n_close","n_ma50","n_atr_ratio","n_week_ret"]]

    medians  = (sf.groupby("stock")[["p_atr_ratio","p_range_ratio"]]
                  .median()
                  .rename(columns={"p_atr_ratio":"med_atr","p_range_ratio":"med_rng"})
                  .reset_index())
    mkt_vol  = (sf.groupby("date")["p_vol_ratio"]
                  .mean().reset_index()
                  .rename(columns={"p_vol_ratio":"mkt_vr"}))
    nifty_med_atr = float(nf["n_atr_ratio"].median())

    sf2    = sf.merge(medians, on="stock", how="left")
    master = trades.merge(sf2, left_on=["stock","trade_date"],
                          right_on=["stock","date"], how="left")
    master = master.merge(nf, left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_nif"))
    master = master.merge(mkt_vol, left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_mkv"))
    master["nmed_atr"] = nifty_med_atr

    keep = ["raw_pnl", "year",
            "p_close","p_open","p_ma50","p_ma100","p_ma200",
            "p_atr_ratio","p_range_ratio","p_body_ratio",
            "p_vol_ratio","ma50_slope","dist_ma50",
            "p_close_5d","p_close_10d","p_close_22d",
            "p_r52w_high","p_r52w_low",
            "med_atr","med_rng",
            "n_close","n_ma50","n_atr_ratio","n_week_ret","nmed_atr","mkt_vr"]
    master = master[keep].copy().reset_index(drop=True)
    print(f"  Master table: {len(master):,} rows.")
    return master


# ── Step 3: Filter mask (copied from sb_regime_optuna.py) ────────────────────
def get_filter_mask(fname, df, natural, t):
    pc   = df["p_close"];   po   = df["p_open"]
    m50  = df["p_ma50"];    m100 = df["p_ma100"];  m200 = df["p_ma200"]
    atr  = df["p_atr_ratio"]; rng_ = df["p_range_ratio"]
    body = df["p_body_ratio"]; vr  = df["p_vol_ratio"]
    slp  = df["ma50_slope"];  dist = df["dist_ma50"]
    r5   = df["p_close_5d"]; r10  = df["p_close_10d"]; r22 = df["p_close_22d"]
    h52  = df["p_r52w_high"]; l52 = df["p_r52w_low"]
    ma   = df["med_atr"];    mr   = df["med_rng"]
    nc   = df["n_close"];    nm   = df["n_ma50"]
    na   = df["n_atr_ratio"]; nw  = df["n_week_ret"]
    nmd  = df["nmed_atr"];   mv   = df["mkt_vr"]

    if   fname == "PF1":  valid, cond = m50.notna(),                      pc > m50
    elif fname == "PF2":  valid, cond = m100.notna(),                     pc > m100
    elif fname == "PF3":  valid, cond = m200.notna(),                     pc > m200
    elif fname == "PF4":  valid, cond = po.notna() & pc.notna(),          pc > po
    elif fname == "PF5":  valid, cond = r5.notna() & pc.notna(),          pc > r5
    elif fname == "PF6":  valid, cond = r10.notna() & pc.notna(),         pc > r10
    elif fname == "PF7":  valid, cond = r22.notna() & pc.notna(),         pc > r22
    elif fname == "PF8":
        ratio = pc / h52.replace(0, np.nan)
        valid, cond = h52.notna() & pc.notna(),                           ratio > t["PF8"]
    elif fname == "PF9":
        ratio = pc / l52.replace(0, np.nan)
        valid, cond = l52.notna() & pc.notna(),                           ratio > t["PF9"]
    elif fname == "VF1":  valid, cond = atr.notna() & ma.notna(),         atr < ma
    elif fname == "VF2":  valid, cond = rng_.notna() & mr.notna(),        rng_ < mr
    elif fname == "VF3":  valid, cond = body.notna(),                     body > t["VF3"]
    elif fname == "TF1":  valid, cond = slp.notna(),                      slp > 0
    elif fname == "TF2":  valid, cond = m50.notna() & m100.notna(),       m50 > m100
    elif fname == "TF3":  valid, cond = m50.notna() & m200.notna(),       m50 > m200
    elif fname == "TF4":
        valid, cond = (dist.notna(),
                       (dist >= t["TF4_lo"]) & (dist <= t["TF4_hi"]))
    elif fname == "VL1":
        valid, cond = (vr.notna() & po.notna() & pc.notna(),
                       (vr > t["VL1"]) & (pc > po))
    elif fname == "VL2":  valid, cond = vr.notna(),                       vr < 1
    elif fname == "MF1":  valid, cond = nc.notna() & nm.notna(),          nc > nm
    elif fname == "MF2":  valid, cond = nw.notna(),                       nw > 0
    elif fname == "MF3":  valid, cond = na.notna() & nmd.notna(),         na < nmd
    elif fname == "MF4":  valid, cond = mv.notna(),                       mv >= t["MF4"]
    elif fname == "MF5":
        valid = nc.notna() & nm.notna() & nw.notna()
        cond  = (nc > nm) & (nw > 0)
    elif fname == "PF10": valid, cond = po.notna() & pc.notna(),          pc > po
    elif fname == "MF6":  valid, cond = na.notna(),                       na > t["MF6"]
    elif fname == "TF5":  valid, cond = slp.notna(),                      slp > t["TF5"]
    elif fname == "MF7":  valid, cond = nw.notna(),                       nw > t["MF7"]
    elif fname == "SF1":  valid, cond = nc.notna() & nm.notna(),          nc > nm
    else: raise ValueError(f"Unknown filter: {fname}")

    if natural:
        return (valid & cond.fillna(False)).fillna(False)
    else:
        return (valid & (~cond.fillna(True))).fillna(False)


# ── Step 4: Apply Trial #2827 filter (PF9 + TF4, OR) ────────────────────────
def apply_best_params(master: pd.DataFrame, params: dict) -> pd.DataFrame:
    t = {
        "PF8"   : params["thresh_PF8"],
        "PF9"   : params["thresh_PF9"],
        "VF3"   : params["thresh_VF3"],
        "TF4_lo": params["thresh_TF4_lo"],
        "TF4_hi": params["thresh_TF4_hi"],
        "MF4"   : params["thresh_MF4"],
        "VL1"   : params["thresh_VL1_vol"],
        "MF6"   : params["thresh_MF6"],
        "TF5"   : params["thresh_TF5"],
        "MF7"   : params["thresh_MF7"],
    }
    gate = params["gate_logic"]  # OR
    masks = []
    active = []
    for fname in ALL_FILTERS:
        if params.get(f"use_{fname}", False):
            active.append(fname)
            nat = params.get(f"dir_{fname}", True)
            masks.append(get_filter_mask(fname, master, natural=nat, t=t))

    if not masks:
        return master
    combined = masks[0].copy()
    for m in masks[1:]:
        combined = combined | m if gate == "OR" else combined & m
    return master[combined]


# ── Step 5: Print results table ───────────────────────────────────────────────
def print_results(label: str, sub: pd.DataFrame, n_years: int):
    total_pnl = sub["raw_pnl"].sum()
    final_eq  = INITIAL_CAPITAL + total_pnl
    if final_eq <= 0:
        cagr = float("-inf")
    else:
        cagr = ((final_eq / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100
    n_trades = len(sub)
    n_wins   = int((sub["raw_pnl"] > 0).sum())
    win_pct  = n_wins / n_trades * 100 if n_trades else 0

    print(f"\n{'='*62}")
    print(f"  {label}")
    print(f"{'='*62}")
    print(f"  Total Trades  : {n_trades:,}")
    print(f"  Win Rate      : {win_pct:.1f}%")
    print(f"  Initial Eq    : Rs {INITIAL_CAPITAL:,}")
    print(f"  Final Eq      : Rs {final_eq:,.0f}")
    print(f"  {n_years}yr CAGR     : {cagr:+.2f}%")
    print(f"\n  {'YEAR':<6}  {'Trades':>7}  {'Raw PnL (Rs)':>15}  {'Return %':>9}  {'Cum Equity':>14}")
    print(f"  {'-'*6}  {'-'*7}  {'-'*15}  {'-'*9}  {'-'*14}")
    running = INITIAL_CAPITAL
    for yr in ALL_YEARS:
        yr_df  = sub[sub["year"] == yr]
        yr_pnl = float(yr_df["raw_pnl"].sum())
        yr_ret = yr_pnl / running * 100 if running > 0 else 0.0
        running += yr_pnl
        trades_yr = len(yr_df)
        print(f"  {yr}    {trades_yr:>7,}  {yr_pnl:>+15,.0f}  {yr_ret:>+8.2f}%  Rs {running:>11,.0f}")


# ── MAIN ─────────────────────────────────────────────────────────────────────
print("=" * 62)
print("  STEP 5 — Full DS3 Backtest 2015-2025")
print("=" * 62)

t0 = time.time()

# Load best params
with open(BEST_JSON) as f:
    best = json.load(f)
raw_params = best["raw_params"]
print(f"\nLoaded Trial #{best['trial']} params: "
      f"filters={best['active_filters']}, gate={best['gate_logic']}")

# Build trades
trades = build_all_trades()

# Sanity: check 2022-2025 range matches expected ~28,085
t2225 = trades[trades["year"].between(2022, 2025)]
print(f"\nSanity (2022-2025 subset): {len(t2225):,} trades  "
      f"(expected ≈ 28,085)")

# Build features
print()
master = build_features(trades)

elapsed = time.time() - t0
print(f"\nData + features built in {elapsed:.1f}s")

# ── Baseline (no filter) ─────────────────────────────────────────────────────
print_results("BASELINE — No Regime Filter (2015-2025)", master, YEARS)

# ── Trial #2827 filter (PF9 + TF4, OR) ───────────────────────────────────────
filtered = apply_best_params(master, raw_params)
label = (f"REGIME FILTER — Trial #{best['trial']}  "
         f"({'+'.join(best['active_filters'])}, {best['gate_logic']} gate)")
print_results(label, filtered, YEARS)

print(f"\n  Total run time: {time.time()-t0:.1f}s")
print("=" * 62)
