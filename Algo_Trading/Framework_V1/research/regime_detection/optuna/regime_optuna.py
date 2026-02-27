"""
regime_optuna.py
------------------------------------------------------------------------------
Optuna TPE optimisation over 23 prev-day regime features to find the best
combination that maximises 4-year CAGR on FV1 best-config trades while
keeping trade count >= 27,000.

Features (all use PREVIOUS-DAY values only -- no lookahead):
  PF1-PF9 : price / MA / momentum / breadth   (9)
  VF1-VF3 : volatility                         (3)
  TF1-TF4 : trend strength                     (4)
  VL1-VL2 : volume character                   (2)
  MF1-MF5 : market-wide (NIFTY50 regime)       (5)

Search space per trial (54 params):
  23  binary  use_<filter>    ON / OFF
  23  binary  dir_<filter>    natural / flipped direction
   7  float   thresholds      PF8, PF9, VF3, TF4_lo, TF4_hi, MF4, VL1_vol
   1  categ   gate_logic      AND (intersection) / OR (union) of active masks

Objective : 4yr CAGR  -  50 penalty if trade_count < 27,000
Trials    : 3,000  (resumable via SQLite)
Sampler   : TPESampler(seed=42, multivariate=True)
Pruner    : MedianPruner(n_startup_trials=50)

Run:
  py -X utf8 research/regime_detection/optuna/regime_optuna.py

Safe to interrupt and re-run -- completed trials persist in DB.
Delete outputs/optuna/optuna_study.db to start fresh.
"""

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

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[3]   # Framework_V1/
DAILY_DIR  = BASE / "data" / "historical" / "daily"
TRADES_CSV = BASE / "outputs" / "trades" / "fv1_all_trades.csv"
OUT_DIR    = BASE / "outputs" / "optuna"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_PKT = OUT_DIR / "master_features.parquet"
DB_PATH    = OUT_DIR / "optuna_study.db"
BEST_JSON  = OUT_DIR / "best_params.json"
TOP20_CSV  = OUT_DIR / "top20_trials.csv"
HIST_PNG   = OUT_DIR / "optimization_history.png"
IMP_PNG    = OUT_DIR / "feature_importance.png"

# ── Constants ─────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
MIN_TRADES      = 27_000
TRADE_PENALTY   = 50.0
N_TRIALS        = 3_000

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

ALL_FILTERS = [
    "PF1","PF2","PF3","PF4","PF5","PF6","PF7","PF8","PF9",
    "VF1","VF2","VF3","TF1","TF2","TF3","TF4",
    "VL1","VL2","MF1","MF2","MF3","MF4","MF5",
]


# =============================================================================
# STEP 1 -- Build or load master feature table
# =============================================================================

def build_stock_features() -> pd.DataFrame:
    """
    For each of the 29 stocks, compute all prev-day feature columns
    needed by PF1-PF9, VF1-VF3, TF1-TF4, VL1-VL2.
    Returns a long DataFrame indexed by (stock, date).
    """
    frames = []
    for stock in BEST_CFG:
        path = DAILY_DIR / f"{stock}.parquet"
        if not path.exists():
            print(f"  [WARN] Missing parquet: {stock}")
            continue
        df = pd.read_parquet(path)
        df["date"] = (pd.to_datetime(df["datetime"])
                        .dt.normalize().dt.tz_localize(None).dt.date)
        df = df.sort_values("date").reset_index(drop=True)

        # ── Rolling indicators (on current-day data) ──────────────────────
        df["ma50"]      = df["close"].rolling(50,  min_periods=50).mean()
        df["ma100"]     = df["close"].rolling(100, min_periods=100).mean()
        df["ma200"]     = df["close"].rolling(200, min_periods=200).mean()
        df["atr14"]     = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
        df["vol_avg20"] = df["volume"].rolling(20, min_periods=20).mean()
        df["ma50_5d"]   = df["ma50"].shift(5)          # MA50 five days ago
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
        prev_ma50_5 = df["ma50_5d"].shift(1)   # MA50 value 6 days ago (lag of 5d-ago)
        prev_52h    = df["r52w_high"].shift(1)
        prev_52l    = df["r52w_low"].shift(1)

        df["p_close"]     = prev_close
        df["p_open"]      = prev_open
        df["p_ma50"]      = prev_ma50
        df["p_ma100"]     = prev_ma100
        df["p_ma200"]     = prev_ma200
        df["p_r52w_high"] = prev_52h
        df["p_r52w_low"]  = prev_52l

        # Momentum lookbacks (these are already prev-day relative to trade date)
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
        df["ma50_slope"]    = prev_ma50 - prev_ma50_5
        df["dist_ma50"]     = (prev_close - prev_ma50) / prev_ma50

        df["stock"] = stock
        frames.append(df[[
            "stock","date",
            "p_close","p_open",
            "p_ma50","p_ma100","p_ma200",
            "p_atr_ratio","p_range_ratio","p_body_ratio",
            "p_vol_ratio","ma50_slope","dist_ma50",
            "p_close_5d","p_close_10d","p_close_22d",
            "p_r52w_high","p_r52w_low",
        ]])

    print(f"  Stock features built for {len(frames)} stocks.")
    return pd.concat(frames, ignore_index=True)


def build_nifty_features() -> pd.DataFrame:
    """Prev-day NIFTY50 features for MF1-MF5."""
    df = pd.read_parquet(DAILY_DIR / "NIFTY50.parquet")
    df["date"] = (pd.to_datetime(df["datetime"])
                    .dt.normalize().dt.tz_localize(None).dt.date)
    df = df.sort_values("date").reset_index(drop=True)

    df["ma50"]     = df["close"].rolling(50, min_periods=50).mean()
    df["atr14"]    = (df["high"] - df["low"]).rolling(14, min_periods=14).mean()
    df["close_5d"] = df["close"].shift(5)   # close 5 days ago

    df["n_close"]    = df["close"].shift(1)
    df["n_ma50"]     = df["ma50"].shift(1)
    df["n_atr14"]    = df["atr14"].shift(1)
    df["n_close_6d"] = df["close_5d"].shift(1)   # close 6 days ago (lag of 5d)

    df["n_atr_ratio"] = df["n_atr14"] / df["n_close"]
    df["n_week_ret"]  = (df["n_close"] - df["n_close_6d"]) / df["n_close_6d"]

    print("  NIFTY50 features built.")
    return df[["date","n_close","n_ma50","n_atr_ratio","n_week_ret"]]


def build_master() -> pd.DataFrame:
    """Join all features onto best-config trades and return master table."""
    print("Building stock features ...")
    sf = build_stock_features()

    print("Building NIFTY50 features ...")
    nf = build_nifty_features()

    # Per-stock medians (VF1, VF2 use these)
    medians = (sf.groupby("stock")[["p_atr_ratio","p_range_ratio"]]
                 .median()
                 .rename(columns={"p_atr_ratio":"med_atr","p_range_ratio":"med_rng"})
                 .reset_index())

    # Market vol proxy for MF4 (NIFTY50 is an index -- volume is always 0)
    mkt_vol = (sf.groupby("date")["p_vol_ratio"]
                 .mean()
                 .reset_index()
                 .rename(columns={"p_vol_ratio":"mkt_vr"}))

    # NIFTY ATR median -- scalar, stored as constant column in master
    nifty_med_atr = float(nf["n_atr_ratio"].median())

    print("Loading best-config trades ...")
    trades = pd.read_csv(TRADES_CSV)
    trades.columns = trades.columns.str.strip()
    best_df = pd.DataFrame(list(BEST_CFG.items()), columns=["stock","best_cfg"])
    trades  = trades.merge(best_df, on="stock")
    trades  = trades[trades["atr_config"] == trades["best_cfg"]].copy()
    trades["entry_dt"]   = pd.to_datetime(trades["entry_time"])
    trades["trade_date"] = (trades["entry_dt"]
                              .dt.normalize().dt.tz_localize(None).dt.date)
    trades["year"]       = trades["entry_dt"].dt.year
    print(f"  Best-config trades: {len(trades):,}")

    # Join
    sf2    = sf.merge(medians, on="stock", how="left")
    master = trades.merge(sf2, left_on=["stock","trade_date"],
                          right_on=["stock","date"], how="left")
    master = master.merge(nf, left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_nif"))
    master = master.merge(mkt_vol, left_on="trade_date", right_on="date",
                          how="left", suffixes=("","_mkv"))
    master["nmed_atr"] = nifty_med_atr

    keep = [
        "pnl","year",
        "p_close","p_open",
        "p_ma50","p_ma100","p_ma200",
        "p_atr_ratio","p_range_ratio","p_body_ratio",
        "p_vol_ratio","ma50_slope","dist_ma50",
        "p_close_5d","p_close_10d","p_close_22d",
        "p_r52w_high","p_r52w_low",
        "med_atr","med_rng",
        "n_close","n_ma50","n_atr_ratio","n_week_ret","nmed_atr","mkt_vr",
    ]
    master = master[keep].copy().reset_index(drop=True)
    print(f"  Master table: {len(master):,} rows, {len(master.columns)} columns.")
    return master


def get_master() -> pd.DataFrame:
    """Load from cache if available, else build and cache."""
    if MASTER_PKT.exists():
        print(f"Loading cached master features ({MASTER_PKT.name}) ...")
        m = pd.read_parquet(MASTER_PKT)
        print(f"  {len(m):,} rows loaded.")
        return m
    print("Building master feature table (first run only) ...")
    m = build_master()
    m.to_parquet(MASTER_PKT, index=False)
    print(f"  Saved: {MASTER_PKT}")
    return m


# =============================================================================
# STEP 2 -- Per-filter mask builder
# =============================================================================

def get_filter_mask(fname: str, df: pd.DataFrame,
                    natural: bool, t: dict) -> pd.Series:
    """
    Return boolean Series for one filter.
      natural=True  -> natural direction  (e.g. PF1: prev_close > MA50)
      natural=False -> flipped direction  (e.g. PF1: prev_close < MA50)
    Rows with no valid data are always excluded (False) in both directions.
    """
    pc  = df["p_close"];    po  = df["p_open"]
    m50 = df["p_ma50"];     m100= df["p_ma100"];  m200= df["p_ma200"]
    atr = df["p_atr_ratio"]; rng_= df["p_range_ratio"]
    body= df["p_body_ratio"]; vr = df["p_vol_ratio"]
    slp = df["ma50_slope"];  dist= df["dist_ma50"]
    r5  = df["p_close_5d"]; r10 = df["p_close_10d"]; r22 = df["p_close_22d"]
    h52 = df["p_r52w_high"]; l52= df["p_r52w_low"]
    ma  = df["med_atr"];    mr  = df["med_rng"]
    nc  = df["n_close"];    nm  = df["n_ma50"]
    na  = df["n_atr_ratio"]; nw = df["n_week_ret"]
    nmd = df["nmed_atr"];   mv  = df["mkt_vr"]

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
    else:
        raise ValueError(f"Unknown filter: {fname}")

    if natural:
        return (valid & cond.fillna(False)).fillna(False)
    else:
        # Flip: valid rows where the condition is False
        # cond.fillna(True) -> NaN treated as True -> negation -> False (excluded)
        return (valid & (~cond.fillna(True))).fillna(False)


# =============================================================================
# STEP 3 -- CAGR helper
# =============================================================================

def cagr_pct(pnl_by_year: dict, n_years: int) -> float:
    total = sum(pnl_by_year.values())
    final = INITIAL_CAPITAL + total
    if final <= 0 or n_years == 0:
        return -100.0
    return ((final / INITIAL_CAPITAL) ** (1 / n_years) - 1) * 100


# =============================================================================
# STEP 4 -- Optuna objective
# =============================================================================

def objective(trial: optuna.Trial) -> float:
    global _MASTER

    # ── 7 continuous thresholds ───────────────────────────────────────────
    t = {
        "PF8"   : trial.suggest_float("thresh_PF8",     0.70, 0.95),
        "PF9"   : trial.suggest_float("thresh_PF9",     1.05, 1.30),
        "VF3"   : trial.suggest_float("thresh_VF3",     0.30, 0.70),
        "TF4_lo": trial.suggest_float("thresh_TF4_lo", -0.05, 0.00),
        "TF4_hi": trial.suggest_float("thresh_TF4_hi",  0.02, 0.10),
        "MF4"   : trial.suggest_float("thresh_MF4",     0.70, 1.30),
        "VL1"   : trial.suggest_float("thresh_VL1_vol", 0.80, 1.50),
    }

    # ── Gate logic: combine active masks with AND vs OR ───────────────────
    gate = trial.suggest_categorical("gate_logic", ["AND", "OR"])

    # ── Build per-filter masks for all active features ────────────────────
    active_masks = []
    for fname in ALL_FILTERS:
        use = trial.suggest_categorical(f"use_{fname}", [True, False])
        if not use:
            continue
        nat = trial.suggest_categorical(f"dir_{fname}", [True, False])
        active_masks.append(get_filter_mask(fname, _MASTER, natural=nat, t=t))

    # ── Combine ───────────────────────────────────────────────────────────
    if not active_masks:
        sub = _MASTER                         # no filter = full baseline
    elif gate == "AND":
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined &= m
        sub = _MASTER[combined]
    else:  # OR
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined |= m
        sub = _MASTER[combined]

    n_trades = len(sub)
    if n_trades == 0:
        return -100.0

    years       = sorted(sub["year"].unique())
    pnl_by_year = {yr: float(sub.loc[sub["year"] == yr, "pnl"].sum())
                   for yr in years}
    result = cagr_pct(pnl_by_year, n_years=len(years))

    if n_trades < MIN_TRADES:
        result -= TRADE_PENALTY

    return result


# =============================================================================
# STEP 5 -- Re-evaluate helper (for final reporting)
# =============================================================================

def eval_params(params: dict, master: pd.DataFrame) -> dict:
    """Apply a saved param dict to the master table and return full stats."""
    t = {
        "PF8"   : params.get("thresh_PF8",     0.85),
        "PF9"   : params.get("thresh_PF9",     1.10),
        "VF3"   : params.get("thresh_VF3",     0.50),
        "TF4_lo": params.get("thresh_TF4_lo", -0.02),
        "TF4_hi": params.get("thresh_TF4_hi",  0.05),
        "MF4"   : params.get("thresh_MF4",     1.00),
        "VL1"   : params.get("thresh_VL1_vol", 1.00),
    }
    gate   = params.get("gate_logic", "AND")
    active = []
    active_masks = []

    for fname in ALL_FILTERS:
        if params.get(f"use_{fname}", False):
            active.append(fname)
            nat = params.get(f"dir_{fname}", True)
            active_masks.append(get_filter_mask(fname, master, natural=nat, t=t))

    if not active_masks:
        sub = master
    elif gate == "AND":
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined &= m
        sub = master[combined]
    else:
        combined = active_masks[0].copy()
        for m in active_masks[1:]:
            combined |= m
        sub = master[combined]

    years       = sorted(sub["year"].unique())
    pnl_by_year = {yr: float(sub.loc[sub["year"] == yr, "pnl"].sum())
                   for yr in years}
    c = cagr_pct(pnl_by_year, n_years=len(years))

    return {
        "gate_logic"    : gate,
        "active_filters": active,
        "trade_count"   : len(sub),
        "cagr_pct"      : round(c, 4),
        "pnl_by_year"   : {str(k): round(v, 0) for k, v in pnl_by_year.items()},
    }


# =============================================================================
# STEP 6 -- Main entry point
# =============================================================================

_MASTER: pd.DataFrame = None   # global; loaded once before study.optimize()


def main():
    global _MASTER

    print("=" * 66)
    print("  FV1 Regime Detection -- Optuna TPE Optimisation")
    print("=" * 66)

    _MASTER = get_master()
    print(f"\nMaster table loaded: {len(_MASTER):,} trades\n")

    storage = f"sqlite:///{DB_PATH}"
    study = optuna.create_study(
        study_name     = "fv1_regime_optuna",
        storage        = storage,
        load_if_exists = True,
        direction      = "maximize",
        sampler        = TPESampler(seed=42, multivariate=True),
        pruner         = MedianPruner(n_startup_trials=50, n_warmup_steps=0),
    )

    done   = len([t for t in study.trials
                  if t.state == optuna.trial.TrialState.COMPLETE])
    remain = max(0, N_TRIALS - done)
    print(f"Completed trials : {done}")
    print(f"Trials remaining : {remain}")

    if remain > 0:
        print(f"\nRunning {remain} trials ...\n")
        study.optimize(
            objective,
            n_trials          = remain,
            show_progress_bar = True,
            gc_after_trial    = False,
        )
    else:
        print("All trials already complete -- loading results only.\n")

    # ── Best trial ────────────────────────────────────────────────────────
    best  = study.best_trial
    stats = eval_params(best.params, _MASTER)

    print(f"\n{'='*66}")
    print(f"  BEST  trial #{best.number:>4d}   CAGR = {best.value:+.2f}%")
    print(f"{'='*66}")
    print(f"  Gate logic     : {stats['gate_logic']}")
    print(f"  Active filters : {stats['active_filters']}")
    print(f"  Trade count    : {stats['trade_count']:,}")
    print(f"  CAGR           : {stats['cagr_pct']:+.4f}%")
    print(f"  PnL by year    :")
    for yr, pnl in stats["pnl_by_year"].items():
        ret = round(pnl / INITIAL_CAPITAL * 100, 2)
        print(f"    {yr}  Rs {pnl:>12,.0f}  ({ret:+.2f}%)")

    # ── Save best_params.json ─────────────────────────────────────────────
    out = {
        "trial"     : best.number,
        "cagr_pct"  : best.value,
        **stats,
        "raw_params": best.params,
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
        active = [k.replace("use_","") for k, v in t.params.items()
                  if k.startswith("use_") and v]
        row = {
            "trial"         : t.number,
            "cagr"          : round(t.value, 4),
            "gate_logic"    : t.params.get("gate_logic", "AND"),
            "active_filters": "|".join(active),
        }
        row.update(t.params)
        rows.append(row)
    top20_df = pd.DataFrame(rows)
    top20_df.to_csv(TOP20_CSV, index=False)
    print(f"  Saved: {TOP20_CSV}")

    # ── Visualisation plots (matplotlib backend -- avoids kaleido hang) ──
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import optuna.visualization.matplotlib as vizm
        import warnings
        warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)

        vizm.plot_optimization_history(study)
        fig = plt.gcf()
        fig.set_size_inches(12, 5)
        fig.suptitle("FV1 Regime Optuna -- Optimisation History (CAGR %)")
        plt.tight_layout()
        fig.savefig(str(HIST_PNG), dpi=150)
        plt.close("all")
        print(f"  Saved: {HIST_PNG}")

        vizm.plot_param_importances(study)
        fig = plt.gcf()
        fig.set_size_inches(10, 14)
        fig.suptitle("FV1 Regime Optuna -- Parameter Importances")
        plt.tight_layout()
        fig.savefig(str(IMP_PNG), dpi=150)
        plt.close("all")
        print(f"  Saved: {IMP_PNG}")
    except Exception as e:
        print(f"  [WARN] Plots skipped: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
