"""
run_backtest_fast.py
====================
Lean sandbox backtest runner for FV1 MA Bounce strategy.

- Reads best config per stock from FV1's existing fv1_metrics.csv
- Runs best config only (not all 4) — no CSV, no charts, no per-trade logging
- Terminal output: per-stock metrics, portfolio summary, year-wise CAGR table
- Target runtime: < 60 seconds

Paths:
  Data   → Framework_V1/data/historical/intraday_5min/  (read-only)
  Config → Framework_V1/outputs/stats/fv1_metrics.csv   (read-only)

Speed strategy:
  Bypasses BacktestEngine / Portfolio classes (which use slow df.iloc[i] row access).
  Uses pre-computed numpy integer arrays for all time comparisons — no pd.Timestamp()
  calls inside the hot loop. Replicates strategy.py + portfolio.py logic exactly.
"""

import sys
import io
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

# ─── PATH SETUP ────────────────────────────────────────────────────────────────
SANDBOX_DIR = Path(__file__).resolve().parent.parent
FV1_DIR     = SANDBOX_DIR.parent

sys.path.insert(0, str(SANDBOX_DIR))

from core.indicators import add_intraday_indicators, compute_daily_mas, add_atr

# ─── DATA / CONFIG PATHS (point to FV1) ────────────────────────────────────────
INTRADAY_DIR = FV1_DIR / "data/historical/intraday_5min"
FV1_METRICS  = FV1_DIR / "outputs/stats/fv1_metrics.csv"

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────
INITIAL_CAPITAL   = 1_000_000
NUM_STOCKS        = 30
YEARS_BACKTEST    = 4
CAPITAL_PER_STOCK = INITIAL_CAPITAL / NUM_STOCKS
RISK_PCT          = 0.01
RISK_AMT          = INITIAL_CAPITAL * RISK_PCT
EXCLUDE           = {"VI", "IDEA", "NIFTY50"}

VOL_MULT          = 1.2
LOOKAHEAD         = 3
ENTRY_CUTOFF_MIN  = 14 * 60 + 30   # 14:30 in minutes since midnight
EOD_MIN           = 15 * 60        # 15:00 in minutes since midnight

SPECIFIED_BEST = {
    "SUNPHARMA":  "Extreme-4",
    "BHARTIARTL": "Extreme-1",
    "HDFCBANK":   "Extreme-4",
    "ICICIBANK":  "Extreme-4",
    "ASHOKLEY":   "Extreme-4",
}

ATR_CONFIGS = {
    "Extreme-1": {"sl_mult": 2.5, "tgt_mult": 4.0},
    "Extreme-2": {"sl_mult": 2.5, "tgt_mult": 4.5},
    "Extreme-3": {"sl_mult": 3.0, "tgt_mult": 4.5},
    "Extreme-4": {"sl_mult": 3.0, "tgt_mult": 5.0},
}


# ─── FAST INLINE BACKTEST ──────────────────────────────────────────────────────
def run_stock_fast(df: pd.DataFrame, sl_mult: float, tgt_mult: float) -> pd.DataFrame:
    """
    Numpy-based backtest replicating strategy.py + portfolio.py logic exactly.
    No pd.Timestamp() in inner loop — uses integer time arrays throughout.
    Returns a DataFrame of closed trades with columns: entry_time, pnl.
    """
    rr_target = tgt_mult / sl_mult
    n = len(df)
    if n < 4:
        return pd.DataFrame()

    # --- Pre-extract numpy arrays ---
    dt64    = df["datetime"].values                       # numpy datetime64[ns]
    open_a  = df["open"].values.astype(np.float64)
    high_a  = df["high"].values.astype(np.float64)
    low_a   = df["low"].values.astype(np.float64)
    close_a = df["close"].values.astype(np.float64)
    vol_a   = df["volume"].values.astype(np.float64)
    ma20_a  = df["ma20"].values.astype(np.float64)
    avgv_a  = df["avg_volume"].values.astype(np.float64)
    atr_a   = df["atr_14"].values.astype(np.float64)

    # --- Pre-compute integer time components (no pd.Timestamp in loop) ---
    # Datetimes are IST (UTC+05:30). numpy casts to UTC internally.
    # Add IST offset (330 min) so minute-of-day comparisons work in IST.
    IST_OFFSET = 330
    dt_m    = dt64.astype("datetime64[m]").astype(np.int64)           # minutes since epoch (UTC)
    dt_d    = dt64.astype("datetime64[D]").astype(np.int64)           # days since epoch (UTC≡IST for trading hours)
    dt_M    = dt64.astype("datetime64[M]").astype(np.int64)           # months since epoch (UTC≡IST for trading hours)
    minutes = ((dt_m + IST_OFFSET) % 1440).astype(np.int32)           # minutes since midnight (IST)

    # ── SIGNAL GENERATION (mirrors BounceStrategy.generate_signals) ──────────
    signal_indices: dict[int, tuple] = {}   # bar_idx → (entry_price, atr)

    for i in range(n - 3):
        if np.isnan(ma20_a[i]):
            continue
        if not np.isnan(avgv_a[i]) and vol_a[i] < avgv_a[i] * VOL_MULT:
            continue
        if low_a[i] <= ma20_a[i]:
            ma_touch = ma20_a[i]
            for j in range(i, min(i + LOOKAHEAD + 1, n)):
                if close_a[j] > ma_touch:
                    nx = j + 1
                    if nx >= n:
                        break
                    # Cross-month guard (same logic as strategy.py)
                    if dt_M[i] != dt_M[nx]:
                        break
                    # Entry cutoff 14:30
                    if minutes[nx] >= ENTRY_CUTOFF_MIN:
                        break
                    if nx not in signal_indices:
                        signal_indices[nx] = (open_a[nx], atr_a[nx])
                    break

    # ── POSITION TRACKING (mirrors Portfolio.update) ──────────────────────────
    positions: list[dict] = []
    trades_pnl:  list[float]    = []
    trades_time: list           = []   # numpy datetime64

    for i in range(n):
        # Entries
        if i in signal_indices:
            entry_px, atr = signal_indices[i]
            stop_dist = (atr * sl_mult) if (not np.isnan(atr) and atr > 0) else entry_px * 0.01
            max_by_cap  = int(CAPITAL_PER_STOCK / entry_px) if entry_px > 0 else 1
            max_by_risk = int(RISK_AMT / stop_dist)         if stop_dist > 0 else 1
            qty = max(min(max_by_cap, max_by_risk), 1)
            positions.append({
                "entry_idx": i,
                "entry_day": dt_d[i],
                "entry_px":  entry_px,
                "qty":       qty,
                "stop":      entry_px - stop_dist,
                "target":    entry_px + stop_dist * rr_target,
                "entry_time": dt64[i],
            })

        # Updates
        if not positions:
            continue

        cur_day  = dt_d[i]
        cur_min  = minutes[i]
        cur_open = open_a[i]
        cur_high = high_a[i]
        cur_low  = low_a[i]
        cur_close= close_a[i]
        is_bull  = cur_close > cur_open

        closed_idx = []
        for pi, pos in enumerate(positions):
            if pos["entry_idx"] == i:
                continue

            exit_px = 0.0
            if cur_day == pos["entry_day"] and cur_min >= EOD_MIN:
                exit_px = cur_open
            else:
                if is_bull:
                    if cur_low <= pos["stop"]:
                        exit_px = pos["stop"]
                    elif cur_high >= pos["target"]:
                        exit_px = pos["target"]
                else:
                    if cur_high >= pos["target"]:
                        exit_px = pos["target"]
                    elif cur_low <= pos["stop"]:
                        exit_px = pos["stop"]

            if exit_px:
                trades_pnl.append((exit_px - pos["entry_px"]) * pos["qty"])
                trades_time.append(pos["entry_time"])
                closed_idx.append(pi)

        for pi in reversed(closed_idx):
            positions.pop(pi)

    if not trades_pnl:
        return pd.DataFrame()

    return pd.DataFrame({"entry_time": trades_time, "pnl": trades_pnl})


# ─── METRIC HELPERS ────────────────────────────────────────────────────────────
def profit_factor(pnl: np.ndarray) -> float:
    wins   = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl < 0].sum())
    return round(float(wins / losses), 4) if losses > 0 else float("inf")


def safe_cagr(total_pnl_rs: float, capital: float) -> str:
    final = capital + total_pnl_rs
    if final <= 0:
        return "< -100%"
    pct = ((final / capital) ** (1.0 / YEARS_BACKTEST) - 1) * 100
    return f"{pct:>+7.2f}%"


def portfolio_cagr(total_pnl_rs: float) -> float:
    final = INITIAL_CAPITAL + total_pnl_rs
    return ((final / INITIAL_CAPITAL) ** (1.0 / YEARS_BACKTEST) - 1) * 100


# ─── LOAD BEST CONFIG MAP ──────────────────────────────────────────────────────
if not FV1_METRICS.exists():
    print(f"[ERROR] fv1_metrics.csv not found at {FV1_METRICS}")
    print("  Run fv1_backtest_analysis.py from FV1 first to generate it.")
    sys.exit(1)

_m = pd.read_csv(FV1_METRICS)
best_cfg = dict(zip(_m["stock"], _m["best_config"]))
best_cfg.update(SPECIFIED_BEST)

# ─── DISCOVER STOCK FILES ──────────────────────────────────────────────────────
stock_files = sorted(
    f for f in INTRADAY_DIR.glob("*.parquet")
    if f.stem not in EXCLUDE and f.stem in best_cfg
)

print(f"\n{'='*68}")
print(f"  FV1 SANDBOX — FAST BACKTEST RUNNER")
print(f"  Stocks: {len(stock_files)}  |  Mode: best config only  |  No I/O")
print(f"{'='*68}\n")

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
t0 = time.time()

per_stock_rows = []
all_trades_list: list[pd.DataFrame] = []

for stock_path in stock_files:
    stock  = stock_path.stem
    config_name = best_cfg[stock]
    cfg    = ATR_CONFIGS[config_name]

    try:
        df = pd.read_parquet(stock_path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)

        _t = df["datetime"].dt.time
        df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
        df = df.reset_index(drop=True)
        del _t

        df = add_intraday_indicators(df)
        df = compute_daily_mas(df)
        df = add_atr(df)

        trades = run_stock_fast(df, cfg["sl_mult"], cfg["tgt_mult"])

        if trades.empty:
            per_stock_rows.append({
                "stock": stock, "config": config_name,
                "cagr_str": "   0.00%", "trades": 0, "pf": 0.0, "exp": 0.0,
                "pnl_rs": 0.0,
            })
            print(f"  {stock:<14} {config_name:<11}  0 trades")
            continue

        pnl    = trades["pnl"].values
        n      = len(pnl)
        pf     = profit_factor(pnl)
        exp    = round(float(pnl.mean()), 2)
        pnl_rs = float(pnl.sum())
        cgr    = safe_cagr(pnl_rs, CAPITAL_PER_STOCK)

        per_stock_rows.append({
            "stock": stock, "config": config_name,
            "cagr_str": cgr, "trades": n, "pf": pf, "exp": exp, "pnl_rs": pnl_rs,
        })

        trades = trades.copy()
        trades.insert(0, "stock", stock)
        all_trades_list.append(trades)

        print(
            f"  {stock:<14} {config_name:<11}  "
            f"CAGR={cgr}  Trades={n:>5}  "
            f"PF={pf:>6.4f}  Exp=₹{exp:>+8.2f}"
        )

    except Exception as e:
        print(f"  [ERROR] {stock}: {e}")

elapsed = time.time() - t0

# ─── PORTFOLIO AGGREGATION ─────────────────────────────────────────────────────
print(f"\n{'='*68}")
print(f"  PORTFOLIO SUMMARY")
print(f"{'='*68}")

if not all_trades_list:
    print("[ERROR] No trades generated.")
    sys.exit(1)

all_trades = pd.concat(all_trades_list, ignore_index=True)
all_trades["entry_time"] = pd.to_datetime(all_trades["entry_time"])
all_trades["year"]       = all_trades["entry_time"].dt.year

total_pnl_rs = float(all_trades["pnl"].sum())
final_equity = INITIAL_CAPITAL + total_pnl_rs
port_cagr    = portfolio_cagr(total_pnl_rs)
total_trades = len(all_trades)
port_pf      = profit_factor(all_trades["pnl"].values)
port_exp     = round(float(all_trades["pnl"].mean()), 2)

print(f"  Stocks          : {len(per_stock_rows)}")
print(f"  Total Trades    : {total_trades:,}")
print(f"  Initial Equity  : ₹{INITIAL_CAPITAL:>12,}")
print(f"  Final Equity    : ₹{final_equity:>12,.2f}")
print(f"  4yr CAGR        : {port_cagr:>+9.2f} %")
print(f"  Profit Factor   : {port_pf:>9.4f}")
print(f"  Expectancy      : ₹{port_exp:>+9.2f} / trade")

# ─── YEAR-WISE RETURN TABLE ────────────────────────────────────────────────────
print(f"\n{'─'*44}")
print(f"  YEAR-WISE ANNUAL RETURN")
print(f"{'─'*44}")
print(f"  {'YEAR':<6}  {'PnL (₹)':>12}  {'Return %':>9}  {'Cum Equity':>14}")
print(f"  {'-'*6}  {'-'*12}  {'-'*9}  {'-'*14}")

running = INITIAL_CAPITAL
for year in [2022, 2023, 2024, 2025]:
    yr_pnl = float(all_trades[all_trades["year"] == year]["pnl"].sum())
    yr_ret = (yr_pnl / running) * 100
    running += yr_pnl
    print(
        f"  {year:<6}  {yr_pnl:>+12,.2f}  {yr_ret:>+8.2f}%  ₹{running:>12,.2f}"
    )

# ─── FOOTER ────────────────────────────────────────────────────────────────────
match = "✓ MATCH" if (abs(port_cagr - (-9.74)) < 0.01 and total_trades == 76709) else "✗ MISMATCH"
print(f"\n{'='*68}")
print(f"  Runtime : {elapsed:.1f}s")
print(f"  Baseline: CAGR=-9.74%, 76,709 trades  →  {match}")
print(f"{'='*68}\n")
