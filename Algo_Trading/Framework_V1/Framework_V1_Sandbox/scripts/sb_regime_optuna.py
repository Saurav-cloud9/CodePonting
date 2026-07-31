"""
sb_regime_optuna.py — Sandbox Step 4: Regime Filter Optuna
══════════════════════════════════════════════════════════════════════════════
Mirrors fv1/research/regime_detection/optuna/regime_optuna.py structure.
Extended to 28 params and built on DS3 data with slippage-adjusted trades.

Context:
  Baseline   : Step 3.2 winner  (SL=A, PG=True, CP=True, AF=True)
  Slippage   : entry +0.05 tick, SL exit -0.05 tick
  Raw CAGR   : TBD (2015-2025 baseline — full DS3)
  Trades     : TBD (full DS3 2015-2025)
  Data       : DS3, 29 stocks, 2015-2025, Extreme-2  (sl=2.5 ATR, tp=4.5 ATR)

Param space (28 filters total = 23 original + 5 new):
  Original 23  :  PF1..PF9, VF1..VF3, TF1..TF4, VL1..VL2, MF1..MF5
  New 5:
    P24  use_PF10 : prev day bullish candle  (p_close > p_open, no threshold)
    P25  use_MF6  : nifty ATR ratio          thresh_MF6: 0.005–0.030
    P26  use_TF5  : MA50 slope               thresh_TF5: -0.010–0.020
    P27  use_MF7  : nifty week return        thresh_MF7: -0.030–0.030
    P28  use_SF1  : NIFTY50 > NIFTY50_MA50  dir_SF1
                   NOTE: sector index parquets unavailable — NIFTY50 used
                   as universal sector proxy; refine when sector data added.

Warm-up phase (28 trials):
  One trial per filter, solo active (all others False).
  Injected via study.enqueue_trial() BEFORE the main TPE run.
  If the study DB already exists, only the missing warm-up trials are enqueued
  so resuming is safe and idempotent.

Gate logic : AND  OR  (both in search space — fv1 tested OR-only)
Objective  : maximize raw_pnl CAGR
             penalty −50 if trade_count < 20,000
Trials     : 3,000 (28 warm-up + 2,972 TPE, resumable)
Sampler    : TPESampler(seed=42, multivariate=True)
Pruner     : MedianPruner(n_startup_trials=50)

Sanity checks at startup:
  1. Baseline raw CAGR  ≈ −8.62%  (DS3-native)
  2. Baseline trade count ≈ 77,028  (DS3 full 2015-2025)

Success criteria:
  Primary : raw CAGR > −8.62%  (beat DS3 slippage-adjusted baseline)
  Secondary : raw CAGR > +2.69%  (beat old fv1 Optuna best)
  Stretch   : net_pnl_kite CAGR positive

Outputs  (Framework_V1_Sandbox/outputs/optuna/):
  best_params.json    top20_trials.csv    optuna_study.db

Run:
  py -X utf8 Framework_V1_Sandbox/scripts/sb_regime_optuna.py
  Safe to interrupt and resume — delete optuna_study.db to start fresh.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path

import optuna
from optuna.samplers import TPESampler
from optuna.pruners  import MedianPruner

optuna.logging.set_verbosity(optuna.logging.WARNING)


# ══════════════════════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════════════════════

SANDBOX_DIR   = Path(__file__).resolve().parents[1]   # Framework_V1_Sandbox/
FV1_DIR       = SANDBOX_DIR.parent                    # Framework_V1/
DS3_DIR       = FV1_DIR / "data" / "historical" / "intraday_5min_DS3"
DAILY_DIR     = FV1_DIR / "data" / "historical" / "daily"
OUT_DIR     = SANDBOX_DIR / "outputs" / "optuna"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRADES_PKT = OUT_DIR / "sb_winner_trades.parquet"
MASTER_PKT = OUT_DIR / "master_features.parquet"
DB_PATH    = OUT_DIR / "optuna_study.db"
BEST_JSON  = OUT_DIR / "best_params.json"
TOP20_CSV  = OUT_DIR / "top20_trials.csv"


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

INITIAL_CAPITAL = 1_000_000
MIN_TRADES      = 40_000      # penalty applied below this (scaled for 11yr dataset)
TRADE_PENALTY   = 50.0
N_TRIALS        = 3_000

STOCKS = [
    "ADANIPORTS", "ASHOKLEY",   "AXISBANK",   "BANDHANBNK", "BHARTIARTL",
    "CIPLA",      "COALINDIA",  "DABUR",      "DIVISLAB",   "HDFCBANK",
    "HINDALCO",   "ICICIBANK",  "INDUSINDBK", "INFY",       "ITC",
    "JSWSTEEL",   "NATIONALUM", "NTPC",       "ONGC",       "PNB",
    "POWERGRID",  "RELIANCE",   "SBIN",       "SUNPHARMA",  "TATAMOTORS",
    "TATASTEEL",  "TECHM",      "VEDL",       "WIPRO",
]   # 29 stocks (VI excluded)

# Winner config — Extreme-2, SL=A, PG=True, CP=True, AF=True, EC=False
ATR_MULT_STOP  = 2.5
RR_TARGET      = 4.5 / 2.5    # 1.8
RISK_PER_TRADE = 0.01
NUM_STOCKS     = 30            # capital denominator (30, not 29)
VOL_MULT       = 1.2
LOOKAHEAD      = 3
_TICK          = 0.05
_EOD_INT       = 1500          # 15:00 as HHMM int
_CUTOFF_INT    = 1430          # 14:30 — EC=False
_AUCTION_INT   = 945           # 09:45 — AF=True

# 23 original + 5 new = 28 total filters
ALL_FILTERS = [
    # Price (10)
    "PF1", "PF2", "PF3", "PF4", "PF5", "PF6", "PF7", "PF8", "PF9", "PF10",
    # Volatility (3)
    "VF1", "VF2", "VF3",
    # Trend (5)
    "TF1", "TF2", "TF3", "TF4", "TF5",
    # Volume character (2)
    "VL1", "VL2",
    # Market-wide / NIFTY (7)
    "MF1", "MF2", "MF3", "MF4", "MF5", "MF6", "MF7",
    # Sector proxy (1)
    "SF1",
]  # 28 filters

# Default threshold values used in warm-up and eval_params_full defaults
_DEFAULT_THRESHOLDS = {
    "PF8"   : 0.85,
    "PF9"   : 1.10,
    "VF3"   : 0.50,
    "TF4_lo": -0.02,
    "TF4_hi":  0.05,
    "MF4"   :  1.00,
    "VL1"   :  1.00,
    "MF6"   :  0.015,
    "TF5"   :  0.005,
    "MF7"   :  0.00,
}


# ══════════════════════════════════════════════════════════════════════════════
# STEP 0  —  Generate (or load) winner trades from DS3
# ══════════════════════════════════════════════════════════════════════════════

def _compute_charges(entry, exit_price, qty, broker):
    """Round-trip NSE intraday charges. Mirrors portfolio.py exactly."""
    buy_val   = entry      * qty
    sell_val  = exit_price * qty
    bkr_rate  = 0.0005 if broker == "upstox" else 0.0003
    brokerage = min(buy_val * bkr_rate, 20.0) + min(sell_val * bkr_rate, 20.0)
    stt       = sell_val * 0.00025
    exchange  = (buy_val + sell_val) * 0.0000345
    sebi      = (buy_val + sell_val) * 0.000001
    gst       = (brokerage + exchange + sebi) * 0.18
    stamp     = buy_val * 0.00003
    return brokerage + stt + exchange + sebi + gst + stamp


def build_winner_trades() -> pd.DataFrame:
    """
    Run the Step 3.2 winner config on full DS3 data (2015-2025) and return
    a DataFrame with one row per closed trade:
      stock, entry_time, trade_date, year, raw_pnl, net_pnl_upstox, net_pnl_kite

    Uses intraday_5min_DS3 with no year filter — full 2015-2025 history.
    MA20/ATR computed on full dataset (no artificial cold-start truncation).

    Timezone note: DS3 stores tz-aware timestamps (IST +05:30).
    We strip tz via strftime to preserve the IST wall-clock value.
    """
    import sys
    sys.path.insert(0, str(SANDBOX_DIR))
    from core.indicators import add_intraday_indicators, add_atr

    print("Building winner trades from intraday_5min_DS3 data ...")
    all_trades = []

    stock_files = sorted(
        f for f in DS3_DIR.glob("*.parquet")
        if f.stem in set(STOCKS)
    )

    for path in stock_files:
        stock = path.stem

        # ── Load & tz-strip (IST wall-clock preserved via strftime) ────────
        df = pd.read_parquet(path)
        df["datetime"] = pd.to_datetime(
            df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
        )
        df = df.sort_values("datetime").reset_index(drop=True)

        _t = df["datetime"].dt.time
        df = df[_t.between(
            pd.Timestamp("09:15").time(),
            pd.Timestamp("15:30").time()
        )].reset_index(drop=True)

        # ── Indicators ────────────────────────────────────────────────────
        df = add_intraday_indicators(df)
        df = add_atr(df)

        if df.empty:
            continue

        # ── Convert to numpy arrays ────────────────────────────────────────
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

        # ── Signal generation (AF=True, EC=False 14:30) ───────────────────
        signal_map = {}   # bar_idx -> entry_open_price
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

        # ── Run winner backtest (SL=A, PG=True, CP=True + slippage) ──────
        cash      = INITIAL_CAPITAL
        positions = []
        # pos layout: [entry_idx, entry_date, entry_price, qty, stop, target]

        for i in range(n):
            op  = open_arr[i]
            hi  = high_arr[i]
            lo  = low_arr[i]
            cl  = close_arr[i]
            atr = atr_arr[i]
            d   = date_int[i]
            t   = time_int[i]

            # Entry (PG=True: skip if occupied)
            if i in signal_map and not positions:
                raw_entry = signal_map[i]
                entry     = raw_entry + _TICK    # slippage: +1 tick
                sd        = atr * ATR_MULT_STOP
                if sd <= 0 or np.isnan(sd):
                    sd = entry * 0.01

                eq          = cash   # CP=True: compound on current cash
                risk_amt    = eq * RISK_PER_TRADE
                per_stk_cap = eq / NUM_STOCKS
                qty         = max(min(int(per_stk_cap / entry),
                                      int(risk_amt / sd)), 1)

                positions.append([
                    i,                          # 0 entry_idx
                    d,                          # 1 entry_date
                    entry,                      # 2 entry_price (after slip)
                    qty,                        # 3 qty
                    entry - sd,                 # 4 stop (SL=A: fixed)
                    entry + sd * RR_TARGET,     # 5 target
                    dt_arr[i],                  # 6 entry_time (numpy datetime)
                ])

            if not positions:
                continue

            is_bull = cl > op
            kept    = []

            for pos in positions:
                if pos[0] == i:   # skip entry candle
                    kept.append(pos)
                    continue

                # EOD forced close (same day, at/after 15:00)
                if d == pos[1] and t >= _EOD_INT:
                    exit_p = op
                    reason = "time"
                else:
                    stop   = pos[4]
                    target = pos[5]
                    exit_p = None
                    if is_bull:
                        if lo <= stop:      exit_p = stop - _TICK   # SL slip
                        elif hi >= target:  exit_p = target
                    else:
                        if hi >= target:    exit_p = target
                        elif lo <= stop:    exit_p = stop - _TICK   # SL slip
                    reason = "exit"

                if exit_p is not None or (d == pos[1] and t >= _EOD_INT):
                    # EOD case: exit_p set above
                    if exit_p is None:
                        exit_p = op   # shouldn't reach, guard only
                    raw_pnl  = (exit_p - pos[2]) * pos[3]
                    cash    += raw_pnl
                    charges_u = _compute_charges(pos[2], exit_p, pos[3], "upstox")
                    charges_k = _compute_charges(pos[2], exit_p, pos[3], "kite")
                    entry_dt  = pd.Timestamp(pos[6])
                    all_trades.append({
                        "stock"          : stock,
                        "entry_time"     : entry_dt,
                        "trade_date"     : entry_dt.date(),
                        "year"           : entry_dt.year,
                        "raw_pnl"        : raw_pnl,
                        "net_pnl_upstox" : raw_pnl - charges_u,
                        "net_pnl_kite"   : raw_pnl - charges_k,
                    })
                else:
                    kept.append(pos)

            positions = kept

    trades_df = pd.DataFrame(all_trades)
    print(f"  Trades generated: {len(trades_df):,}  across {trades_df['stock'].nunique()} stocks")
    return trades_df


def get_winner_trades() -> pd.DataFrame:
    """Load trades from cache, or build and cache."""
    if TRADES_PKT.exists():
        print(f"Loading cached trades ({TRADES_PKT.name}) ...")
        df = pd.read_parquet(TRADES_PKT)
        print(f"  {len(df):,} trades loaded.")
        return df
    print("Building winner trades (first run only) ...")
    df = build_winner_trades()
    df.to_parquet(TRADES_PKT, index=False)
    print(f"  Saved: {TRADES_PKT}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1  —  Build master feature table
# ══════════════════════════════════════════════════════════════════════════════

def build_stock_features() -> pd.DataFrame:
    """
    Compute all prev-day feature columns for each of the 29 stocks.
    Uses fv1 daily parquets — same source as fv1 regime_optuna.py.
    """
    frames = []
    for stock in STOCKS:
        path = DAILY_DIR / f"{stock}.parquet"
        if not path.exists():
            print(f"  [WARN] Daily parquet missing: {stock}")
            continue

        df = pd.read_parquet(path)
        df["date"] = (pd.to_datetime(df["datetime"])
                        .dt.normalize().dt.tz_localize(None).dt.date)
        df = df.sort_values("date").reset_index(drop=True)

        # ── Rolling indicators (current-day) ──────────────────────────────
        df["ma50"]      = df["close"].rolling(50,  min_periods=50).mean()
        df["ma100"]     = df["close"].rolling(100, min_periods=100).mean()
        df["ma200"]     = df["close"].rolling(200, min_periods=200).mean()
        df["atr14"]     = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
        df["vol_avg20"] = df["volume"].rolling(20, min_periods=20).mean()
        df["ma50_5d"]   = df["ma50"].shift(5)
        df["r52w_high"] = df["high"].rolling(252, min_periods=1).max()
        df["r52w_low"]  = df["low"].rolling(252,  min_periods=1).min()

        # ── Prev-day raw prices / indicators ─────────────────────────────
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
        prev_52h    = df["r52w_high"].shift(1)
        prev_52l    = df["r52w_low"].shift(1)

        df["p_close"]     = prev_close
        df["p_open"]      = prev_open
        df["p_ma50"]      = prev_ma50
        df["p_ma100"]     = prev_ma100
        df["p_ma200"]     = prev_ma200
        df["p_r52w_high"] = prev_52h
        df["p_r52w_low"]  = prev_52l

        df["p_close_5d"]  = df["close"].shift(5)
        df["p_close_10d"] = df["close"].shift(10)
        df["p_close_22d"] = df["close"].shift(22)

        # ── Derived prev-day features ─────────────────────────────────────
        df["p_atr_ratio"]   = prev_atr14 / prev_close
        df["p_range_ratio"] = (prev_high - prev_low) / prev_close
        body_sz = (prev_close - prev_open).abs()
        rng_sz  = (prev_high - prev_low).replace(0, np.nan)
        df["p_body_ratio"]  = body_sz / rng_sz
        df["p_vol_ratio"]   = prev_vol / prev_va20.replace(0, np.nan)
        df["ma50_slope"]    = prev_ma50 - prev_ma50_5   # TF1 / TF5
        df["dist_ma50"]     = (prev_close - prev_ma50) / prev_ma50

        df["stock"] = stock
        frames.append(df[[
            "stock", "date",
            "p_close", "p_open",
            "p_ma50", "p_ma100", "p_ma200",
            "p_atr_ratio", "p_range_ratio", "p_body_ratio",
            "p_vol_ratio", "ma50_slope", "dist_ma50",
            "p_close_5d", "p_close_10d", "p_close_22d",
            "p_r52w_high", "p_r52w_low",
        ]])

    print(f"  Stock features built for {len(frames)} stocks.")
    return pd.concat(frames, ignore_index=True)


def build_nifty_features() -> pd.DataFrame:
    """Prev-day NIFTY50 features for MF1-MF7 and SF1 (sector proxy)."""
    df = pd.read_parquet(DAILY_DIR / "NIFTY50.parquet")
    df["date"] = (pd.to_datetime(df["datetime"])
                    .dt.normalize().dt.tz_localize(None).dt.date)
    df = df.sort_values("date").reset_index(drop=True)

    df["ma50"]     = df["close"].rolling(50, min_periods=50).mean()
    df["atr14"]    = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
    df["close_5d"] = df["close"].shift(5)

    df["n_close"]    = df["close"].shift(1)
    df["n_ma50"]     = df["ma50"].shift(1)
    df["n_atr14"]    = df["atr14"].shift(1)
    df["n_close_6d"] = df["close_5d"].shift(1)   # 6 trading days ago

    df["n_atr_ratio"] = df["n_atr14"] / df["n_close"]
    df["n_week_ret"]  = (df["n_close"] - df["n_close_6d"]) / df["n_close_6d"]

    print("  NIFTY50 features built.")
    return df[["date", "n_close", "n_ma50", "n_atr_ratio", "n_week_ret"]]


def build_master(trades: pd.DataFrame) -> pd.DataFrame:
    """Join all features onto trades and return master table."""
    print("Building stock features ...")
    sf = build_stock_features()

    print("Building NIFTY50 features ...")
    nf = build_nifty_features()

    # Per-stock medians (for VF1, VF2)
    medians = (sf.groupby("stock")[["p_atr_ratio", "p_range_ratio"]]
                 .median()
                 .rename(columns={"p_atr_ratio": "med_atr", "p_range_ratio": "med_rng"})
                 .reset_index())

    # Cross-stock market volume proxy (for MF4)
    mkt_vol = (sf.groupby("date")["p_vol_ratio"]
                 .mean()
                 .reset_index()
                 .rename(columns={"p_vol_ratio": "mkt_vr"}))

    nifty_med_atr = float(nf["n_atr_ratio"].median())

    # Trades cover full 2015-2025 range
    trades = trades.copy()
    print(f"  Joining features onto {len(trades):,} trades ...")

    sf2    = sf.merge(medians, on="stock", how="left")
    master = trades.merge(sf2, left_on=["stock", "trade_date"],
                          right_on=["stock", "date"], how="left")
    master = master.merge(nf, left_on="trade_date", right_on="date",
                          how="left", suffixes=("", "_nif"))
    master = master.merge(mkt_vol, left_on="trade_date", right_on="date",
                          how="left", suffixes=("", "_mkv"))
    master["nmed_atr"] = nifty_med_atr

    keep = [
        "raw_pnl", "net_pnl_upstox", "net_pnl_kite", "year",
        "p_close", "p_open",
        "p_ma50", "p_ma100", "p_ma200",
        "p_atr_ratio", "p_range_ratio", "p_body_ratio",
        "p_vol_ratio", "ma50_slope", "dist_ma50",
        "p_close_5d", "p_close_10d", "p_close_22d",
        "p_r52w_high", "p_r52w_low",
        "med_atr", "med_rng",
        "n_close", "n_ma50", "n_atr_ratio", "n_week_ret", "nmed_atr", "mkt_vr",
    ]
    master = master[keep].copy().reset_index(drop=True)
    print(f"  Master table: {len(master):,} rows, {len(master.columns)} columns.")
    return master


def get_master(trades: pd.DataFrame) -> pd.DataFrame:
    """Load from cache if available, else build and cache."""
    if MASTER_PKT.exists():
        print(f"Loading cached master features ({MASTER_PKT.name}) ...")
        m = pd.read_parquet(MASTER_PKT)
        print(f"  {len(m):,} rows loaded.")
        return m
    print("Building master feature table (first run only) ...")
    m = build_master(trades)
    m.to_parquet(MASTER_PKT, index=False)
    print(f"  Saved: {MASTER_PKT}")
    return m


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2  —  Per-filter mask builder (28 filters)
# ══════════════════════════════════════════════════════════════════════════════

def get_filter_mask(fname: str, df: pd.DataFrame,
                    natural: bool, t: dict) -> pd.Series:
    """
    Return boolean Series for one filter.
      natural=True  -> natural direction (e.g. PF1: prev_close > MA50)
      natural=False -> flipped direction (e.g. PF1: prev_close < MA50)
    Rows with missing data are always excluded (False) in both directions.
    """
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

    # ── Original 23 filters (identical to fv1 regime_optuna.py) ──────────
    if fname == "PF1":
        valid, cond = m50.notna(),                       pc > m50
    elif fname == "PF2":
        valid, cond = m100.notna(),                      pc > m100
    elif fname == "PF3":
        valid, cond = m200.notna(),                      pc > m200
    elif fname == "PF4":
        valid, cond = po.notna() & pc.notna(),           pc > po
    elif fname == "PF5":
        valid, cond = r5.notna()  & pc.notna(),          pc > r5
    elif fname == "PF6":
        valid, cond = r10.notna() & pc.notna(),          pc > r10
    elif fname == "PF7":
        valid, cond = r22.notna() & pc.notna(),          pc > r22
    elif fname == "PF8":
        ratio = pc / h52.replace(0, np.nan)
        valid, cond = h52.notna() & pc.notna(),          ratio > t["PF8"]
    elif fname == "PF9":
        ratio = pc / l52.replace(0, np.nan)
        valid, cond = l52.notna() & pc.notna(),          ratio > t["PF9"]
    elif fname == "VF1":
        valid, cond = atr.notna() & ma.notna(),          atr < ma
    elif fname == "VF2":
        valid, cond = rng_.notna() & mr.notna(),         rng_ < mr
    elif fname == "VF3":
        valid, cond = body.notna(),                      body > t["VF3"]
    elif fname == "TF1":
        valid, cond = slp.notna(),                       slp > 0
    elif fname == "TF2":
        valid, cond = m50.notna() & m100.notna(),        m50 > m100
    elif fname == "TF3":
        valid, cond = m50.notna() & m200.notna(),        m50 > m200
    elif fname == "TF4":
        valid, cond = (dist.notna(),
                       (dist >= t["TF4_lo"]) & (dist <= t["TF4_hi"]))
    elif fname == "VL1":
        valid, cond = (vr.notna() & po.notna() & pc.notna(),
                       (vr > t["VL1"]) & (pc > po))
    elif fname == "VL2":
        valid, cond = vr.notna(),                        vr < 1
    elif fname == "MF1":
        valid, cond = nc.notna() & nm.notna(),           nc > nm
    elif fname == "MF2":
        valid, cond = nw.notna(),                        nw > 0
    elif fname == "MF3":
        valid, cond = na.notna() & nmd.notna(),          na < nmd
    elif fname == "MF4":
        valid, cond = mv.notna(),                        mv >= t["MF4"]
    elif fname == "MF5":
        valid = nc.notna() & nm.notna() & nw.notna()
        cond  = (nc > nm) & (nw > 0)

    # ── 5 new filters ─────────────────────────────────────────────────────
    elif fname == "PF10":
        # Prev day was a bullish candle (close > open)
        valid, cond = po.notna() & pc.notna(),           pc > po

    elif fname == "MF6":
        # NIFTY50 prev ATR ratio (absolute volatility level)
        # dir=True  → high-vol days OK (na > thresh)
        # dir=False → avoid high-vol days (na < thresh)
        valid, cond = na.notna(),                        na > t["MF6"]

    elif fname == "TF5":
        # MA50 slope with continuous threshold (extends TF1)
        # dir=True  → slope positive above thresh
        # dir=False → slope negative below thresh
        valid, cond = slp.notna(),                       slp > t["TF5"]

    elif fname == "MF7":
        # NIFTY50 prev 5-day return with continuous threshold (extends MF2)
        # dir=True  → positive week return required
        # dir=False → negative week (counter-trend entry)
        valid, cond = nw.notna(),                        nw > t["MF7"]

    elif fname == "SF1":
        # Sector regime: NIFTY50 as universal sector proxy
        # (no sector index parquets available; refine when sector data added)
        # dir=True  → trade only when NIFTY50 > NIFTY50_MA50
        # dir=False → trade only when NIFTY50 < NIFTY50_MA50
        valid, cond = nc.notna() & nm.notna(),           nc > nm

    else:
        raise ValueError(f"Unknown filter: {fname}")

    if natural:
        return (valid & cond.fillna(False)).fillna(False)
    else:
        return (valid & (~cond.fillna(True))).fillna(False)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3  —  CAGR helper
# ══════════════════════════════════════════════════════════════════════════════

def cagr_pct(pnl_by_year: dict, n_years: int) -> float:
    total = sum(pnl_by_year.values())
    final = INITIAL_CAPITAL + total
    if final <= 0 or n_years == 0:
        return -100.0
    return ((final / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100


def _apply_masks(params: dict, master: pd.DataFrame):
    """Shared logic: apply param dict to master, return filtered subset."""
    t = {
        "PF8"   : params.get("thresh_PF8",     _DEFAULT_THRESHOLDS["PF8"]),
        "PF9"   : params.get("thresh_PF9",     _DEFAULT_THRESHOLDS["PF9"]),
        "VF3"   : params.get("thresh_VF3",     _DEFAULT_THRESHOLDS["VF3"]),
        "TF4_lo": params.get("thresh_TF4_lo",  _DEFAULT_THRESHOLDS["TF4_lo"]),
        "TF4_hi": params.get("thresh_TF4_hi",  _DEFAULT_THRESHOLDS["TF4_hi"]),
        "MF4"   : params.get("thresh_MF4",     _DEFAULT_THRESHOLDS["MF4"]),
        "VL1"   : params.get("thresh_VL1_vol", _DEFAULT_THRESHOLDS["VL1"]),
        "MF6"   : params.get("thresh_MF6",     _DEFAULT_THRESHOLDS["MF6"]),
        "TF5"   : params.get("thresh_TF5",     _DEFAULT_THRESHOLDS["TF5"]),
        "MF7"   : params.get("thresh_MF7",     _DEFAULT_THRESHOLDS["MF7"]),
    }
    gate         = params.get("gate_logic", "OR")
    active       = []
    active_masks = []

    for fname in ALL_FILTERS:
        if params.get(f"use_{fname}", False):
            active.append(fname)
            nat = params.get(f"dir_{fname}", True)
            active_masks.append(get_filter_mask(fname, master, natural=nat, t=t))

    if not active_masks:
        return master, active, gate

    if gate == "AND":
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined &= m
    else:  # OR
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined |= m

    return master[combined], active, gate


def eval_params_full(params: dict, master: pd.DataFrame) -> dict:
    """Apply params to master, return full stats for all 3 PnL types."""
    sub, active, gate = _apply_masks(params, master)

    years   = sorted(sub["year"].unique())
    n_years = len(years)

    raw_by_yr  = {yr: float(sub.loc[sub["year"] == yr, "raw_pnl"].sum())        for yr in years}
    up_by_yr   = {yr: float(sub.loc[sub["year"] == yr, "net_pnl_upstox"].sum()) for yr in years}
    kite_by_yr = {yr: float(sub.loc[sub["year"] == yr, "net_pnl_kite"].sum())   for yr in years}

    return {
        "gate_logic"       : gate,
        "active_filters"   : active,
        "trade_count"      : len(sub),
        "raw_cagr_pct"     : round(cagr_pct(raw_by_yr,  n_years), 4),
        "upstox_cagr_pct"  : round(cagr_pct(up_by_yr,   n_years), 4),
        "kite_cagr_pct"    : round(cagr_pct(kite_by_yr, n_years), 4),
        "raw_pnl_by_year"  : {str(k): round(v, 0) for k, v in raw_by_yr.items()},
        "upstox_by_year"   : {str(k): round(v, 0) for k, v in up_by_yr.items()},
        "kite_by_year"     : {str(k): round(v, 0) for k, v in kite_by_yr.items()},
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4  —  Optuna objective
# ══════════════════════════════════════════════════════════════════════════════

def objective(trial: optuna.Trial) -> float:
    global _MASTER, _BASELINE_TRADES

    # ── Thresholds (continuous) ───────────────────────────────────────────
    t = {
        "PF8"   : trial.suggest_float("thresh_PF8",      0.70,  0.95),
        "PF9"   : trial.suggest_float("thresh_PF9",      1.05,  1.30),
        "VF3"   : trial.suggest_float("thresh_VF3",      0.30,  0.70),
        "TF4_lo": trial.suggest_float("thresh_TF4_lo",  -0.05,  0.00),
        "TF4_hi": trial.suggest_float("thresh_TF4_hi",   0.02,  0.10),
        "MF4"   : trial.suggest_float("thresh_MF4",      0.70,  1.30),
        "VL1"   : trial.suggest_float("thresh_VL1_vol",  0.80,  1.50),
        # New thresholds
        "MF6"   : trial.suggest_float("thresh_MF6",      0.005, 0.030),
        "TF5"   : trial.suggest_float("thresh_TF5",     -0.010, 0.020),
        "MF7"   : trial.suggest_float("thresh_MF7",     -0.030, 0.030),
    }

    # ── Gate logic ───────────────────────────────────────────────────────
    gate = "OR"  # Step 4.3: OR-only (AND removed from search space)

    # ── Build active filter masks ─────────────────────────────────────────
    active_masks = []
    for fname in ALL_FILTERS:
        use = trial.suggest_categorical(f"use_{fname}", [True, False])
        nat = trial.suggest_categorical(f"dir_{fname}", [True, False])
        if not use:
            continue
        active_masks.append(get_filter_mask(fname, _MASTER, natural=nat, t=t))

    # ── Combine masks ─────────────────────────────────────────────────────
    if not active_masks:
        sub = _MASTER
    elif gate == "AND":
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined &= m
        sub = _MASTER[combined]
    else:
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined |= m
        sub = _MASTER[combined]

    n_trades = len(sub)
    if n_trades == 0:
        return -9999.0

    # Hard disqualify tiny pockets — not a real regime filter
    if n_trades < 5_000:
        return -9999.0

    years       = sorted(sub["year"].unique())
    pnl_by_year = {yr: float(sub.loc[sub["year"] == yr, "raw_pnl"].sum())
                   for yr in years}
    result      = cagr_pct(pnl_by_year, n_years=len(years))

    # Proportional penalty: filters keeping <50% of baseline trades are penalised
    trade_ratio = n_trades / _BASELINE_TRADES if _BASELINE_TRADES > 0 else 1.0
    if trade_ratio < 0.5:
        result -= (1.0 - trade_ratio) * 200.0

    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5  —  Warm-up trial builder
# ══════════════════════════════════════════════════════════════════════════════

def _build_warmup_params(solo_filter: str) -> dict:
    """
    Return a param dict for a single-filter warm-up trial:
      - only solo_filter active (use_<f>=True, dir=True)
      - all other use_* flags False
      - thresholds at midpoint defaults
      - gate_logic = "OR" (irrelevant for 1 filter, but must be valid)
    """
    params = {
        # Thresholds at midpoint
        "thresh_PF8"     : 0.825,
        "thresh_PF9"     : 1.175,
        "thresh_VF3"     : 0.50,
        "thresh_TF4_lo"  : -0.025,
        "thresh_TF4_hi"  :  0.06,
        "thresh_MF4"     :  1.00,
        "thresh_VL1_vol" :  1.15,
        "thresh_MF6"     :  0.0175,
        "thresh_TF5"     :  0.005,
        "thresh_MF7"     :  0.00,
        "gate_logic"     : "OR",
    }
    for fname in ALL_FILTERS:
        params[f"use_{fname}"] = (fname == solo_filter)
        params[f"dir_{fname}"] = True   # natural direction for all
    return params


def enqueue_warmup_trials(study: optuna.Study) -> int:
    """
    Enqueue 28 solo-filter warm-up trials (one per filter).
    Skips any warm-up trial that has already been enqueued or completed
    so that resuming an existing study is idempotent.
    Returns the count of newly enqueued trials.
    """
    # Collect params dicts already in study (enqueued or completed)
    existing_warmup = set()
    for t in study.trials:
        p = t.params
        active = [f for f in ALL_FILTERS if p.get(f"use_{f}", False)]
        if len(active) == 1:
            # Looks like a warm-up trial — record the solo filter
            existing_warmup.add(active[0])

    newly_enqueued = 0
    for fname in ALL_FILTERS:
        if fname in existing_warmup:
            continue
        study.enqueue_trial(_build_warmup_params(fname))
        newly_enqueued += 1

    return newly_enqueued


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6  —  Main entry point
# ══════════════════════════════════════════════════════════════════════════════

_MASTER: pd.DataFrame = None   # global; loaded once before optimize()
_BASELINE_TRADES: int = 0      # global; set in main() before optimize()


def main():
    global _MASTER, _BASELINE_TRADES

    print("=" * 70)
    print("  FV1 Sandbox — Step 4: Regime Filter Optuna  (28 params)")
    print("=" * 70)

    # ── Load / generate trades ────────────────────────────────────────────
    trades = get_winner_trades()

    # ── Build / load master feature table ─────────────────────────────────
    _MASTER = get_master(trades)
    print(f"\nMaster table loaded: {len(_MASTER):,} trades\n")

    # ── Sanity check 1: baseline CAGR (full 2015-2025), trade count ≈ 77,028 ─
    years   = sorted(_MASTER["year"].unique())
    n_years = len(years)
    raw_by_yr = {yr: float(_MASTER.loc[_MASTER["year"] == yr, "raw_pnl"].sum())
                 for yr in years}
    baseline_cagr = cagr_pct(raw_by_yr, n_years)
    baseline_cnt  = len(_MASTER)

    print("─" * 70)
    print("  SANITY CHECK — Baseline (no regime filter)")
    print("─" * 70)
    print(f"  Trade count : {baseline_cnt:,}   (expected ≈ 77,028  [DS3 2015-2025])")
    print(f"  Raw CAGR    : {baseline_cagr:+.2f}%  (full 2015-2025)")
    for yr, pnl in raw_by_yr.items():
        print(f"    {yr}  Rs {pnl:>+12,.0f}")

    if baseline_cnt < 70_000 or baseline_cnt > 85_000:
        print("\n  [WARN] Trade count outside expected range — investigate before trusting results.")
    else:
        print("\n  [OK] Baseline within expected range. Proceeding.\n")

    # Set global baseline trade count for proportional penalty in objective()
    _BASELINE_TRADES = baseline_cnt
    print(f"  Baseline trades for penalty calc: {_BASELINE_TRADES:,}")
    print(f"  Hard disqualify threshold       : 5,000 trades")
    print(f"  Proportional penalty kicks in at: {_BASELINE_TRADES // 2:,} trades (50% of baseline)\n")

    # ── Create or resume Optuna study ─────────────────────────────────────
    storage = f"sqlite:///{DB_PATH}"
    study   = optuna.create_study(
        study_name     = "sb_regime_optuna_step4",
        storage        = storage,
        load_if_exists = True,
        direction      = "maximize",
        sampler        = TPESampler(seed=42, multivariate=True, warn_independent_sampling=False),
        pruner         = MedianPruner(n_startup_trials=50, n_warmup_steps=0),
    )

    # ── Warm-up phase: enqueue 28 solo-filter trials ──────────────────────
    n_enqueued = enqueue_warmup_trials(study)
    if n_enqueued > 0:
        print(f"  Enqueued {n_enqueued} warm-up trials (solo-filter, one per param).")
    else:
        print("  All 28 warm-up trials already present in study DB — skipping enqueue.")

    done   = len([t for t in study.trials
                  if t.state == optuna.trial.TrialState.COMPLETE])
    remain = max(0, N_TRIALS - done)

    print(f"\n  Completed trials : {done}")
    print(f"  Trials remaining : {remain}")

    if remain > 0:
        print(f"\n  Running {remain} trials (warm-up trials run first) ...\n")
        study.optimize(
            objective,
            n_trials          = remain,
            show_progress_bar = True,
            gc_after_trial    = False,
        )
    else:
        print("\n  All trials complete — loading results only.\n")

    # ── Best trial ────────────────────────────────────────────────────────
    best  = study.best_trial
    stats = eval_params_full(best.params, _MASTER)

    print(f"\n{'='*70}")
    print(f"  BEST  trial #{best.number:>4d}   raw CAGR = {best.value:+.2f}%")
    print(f"{'='*70}")
    print(f"  Gate logic      : {stats['gate_logic']}")
    print(f"  Active filters  : {stats['active_filters']}")
    print(f"  Trade count     : {stats['trade_count']:,}")
    print()
    print(f"  Raw CAGR        : {stats['raw_cagr_pct']:+.4f}%   (vs baseline {baseline_cagr:+.2f}%)")
    print(f"  Upstox CAGR     : {stats['upstox_cagr_pct']:+.4f}%")
    print(f"  Kite CAGR       : {stats['kite_cagr_pct']:+.4f}%")
    print()
    print(f"  {'YEAR':<6}  {'Raw PnL':>13}  {'Upstox':>13}  {'Kite':>13}")
    for yr in sorted(stats["raw_pnl_by_year"]):
        rp = stats["raw_pnl_by_year"][yr]
        up = stats["upstox_by_year"][yr]
        kt = stats["kite_by_year"][yr]
        print(f"  {yr}    Rs {rp:>+12,.0f}  Rs {up:>+12,.0f}  Rs {kt:>+12,.0f}")

    # ── Success criteria check ────────────────────────────────────────────
    print()
    raw_c    = stats["raw_cagr_pct"]
    kite_c   = stats["kite_cagr_pct"]
    p1 = "PASS" if raw_c  > baseline_cagr else "FAIL"
    p2 = "PASS" if raw_c  > 2.69          else "FAIL"
    p3 = "PASS" if kite_c > 0             else "FAIL"
    print(f"  Primary   (raw > {baseline_cagr:+.2f}%) : {p1}")
    print(f"  Secondary (raw > +2.69%)         : {p2}")
    print(f"  Stretch   (kite > 0%)            : {p3}")

    # ── Save best_params.json ─────────────────────────────────────────────
    out = {
        "trial"           : best.number,
        "objective_value" : best.value,
        **stats,
        "baseline_raw_cagr"  : round(baseline_cagr, 4),
        "baseline_trade_count": baseline_cnt,
        "raw_params"      : best.params,
    }
    with open(BEST_JSON, "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\n  Saved: {BEST_JSON}")

    # ── Top-20 trials CSV ─────────────────────────────────────────────────
    complete = [t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE]
    complete.sort(key=lambda t: t.value, reverse=True)
    rows = []
    for t in complete[:20]:
        active = [k.replace("use_", "") for k, v in t.params.items()
                  if k.startswith("use_") and v]
        row = {
            "trial"          : t.number,
            "raw_cagr"       : round(t.value, 4),
            "gate_logic"     : t.params.get("gate_logic", "OR"),
            "active_filters" : "|".join(active),
            "n_active"       : len(active),
        }
        row.update(t.params)
        rows.append(row)
    pd.DataFrame(rows).to_csv(TOP20_CSV, index=False)
    print(f"  Saved: {TOP20_CSV}")

    # ── Visualisation (optional, non-blocking) ────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import optuna.visualization.matplotlib as vizm

        vizm.plot_optimization_history(study)
        fig = plt.gcf()
        fig.set_size_inches(12, 5)
        fig.suptitle("SB Regime Optuna Step 4 — Optimisation History (raw CAGR %)")
        plt.tight_layout()
        fig.savefig(str(OUT_DIR / "optimization_history.png"), dpi=150)
        plt.close("all")

        vizm.plot_param_importances(study)
        fig = plt.gcf()
        fig.set_size_inches(10, 16)
        fig.suptitle("SB Regime Optuna Step 4 — Parameter Importances")
        plt.tight_layout()
        fig.savefig(str(OUT_DIR / "feature_importance.png"), dpi=150)
        plt.close("all")
        print(f"  Saved: optimization_history.png, feature_importance.png")
    except Exception as e:
        print(f"  [WARN] Plots skipped: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()