"""
16-Combination Sandbox Backtest Runner
=======================================
4 ATR configs × 4 exit variants = 16 combinations
All 30 stocks, 2022-2025 window.

Output: ranked table by CAGR (CAGR, profit factor, win rate, total trades)
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

parser = argparse.ArgumentParser()
parser.add_argument("--batch-start", type=int, default=0)
parser.add_argument("--batch-end",   type=int, default=None)
args, _ = parser.parse_known_args()

import pandas as pd

from core.indicators import add_intraday_indicators, add_atr
from core.engine import BacktestEngine
from core.portfolio import Portfolio

# ─── PATHS ─────────────────────────────────────────────────────────────────────
SANDBOX_DIR = Path(__file__).resolve().parent.parent
FV1_DIR     = SANDBOX_DIR.parent
DS3_DIR     = FV1_DIR / "data/historical/intraday_5min_DS3"

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 1_000_000
YEARS           = 4
EXCLUDE         = {"NIFTY50"}

# ─── CONFIGS ───────────────────────────────────────────────────────────────────
ATR_CONFIGS = {
    "Extreme-1": {"sl_mult": 2.5, "tp_mult": 4.0},
    "Extreme-2": {"sl_mult": 2.5, "tp_mult": 4.5},
    "Extreme-3": {"sl_mult": 3.0, "tp_mult": 4.5},
    "Extreme-4": {"sl_mult": 3.0, "tp_mult": 5.0},
}

VARIANTS = {
    "A": {"sl_variant": "A",  "breakeven_trigger": None, "trailing_dist": None},
    "B": {"sl_variant": "B",  "breakeven_trigger": 1.5,  "trailing_dist": None},
    "C": {"sl_variant": "C",  "breakeven_trigger": 2.5,  "trailing_dist": None},
    "D": {"sl_variant": "D",  "breakeven_trigger": None, "trailing_dist": 1.5},
}

# ─── DISCOVER STOCKS ───────────────────────────────────────────────────────────
all_stock_files = sorted(
    f for f in DS3_DIR.glob("*.parquet")
    if f.stem not in EXCLUDE
)
stock_files = all_stock_files[args.batch_start : args.batch_end]
print(f"Stocks found: {len(all_stock_files)} total, processing {len(stock_files)} "
      f"(index {args.batch_start}–{args.batch_end or len(all_stock_files)-1})")
print(f"Combinations: {len(ATR_CONFIGS)} ATR configs × {len(VARIANTS)} variants = "
      f"{len(ATR_CONFIGS) * len(VARIANTS)}")
print()

# combo_results[combo_key] = list of per-stock trade DataFrames
combo_results = {
    f"{atr}-{var}": []
    for atr in ATR_CONFIGS
    for var in VARIANTS
}

errors = []
t0 = time.time()

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
for stock_path in stock_files:
    stock = stock_path.stem
    try:
        df = pd.read_parquet(stock_path)
        df["datetime"] = pd.to_datetime(df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S"))
        df = df.sort_values("datetime").reset_index(drop=True)
        _t = df["datetime"].dt.time
        df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
        df = df.reset_index(drop=True)
        df = add_intraday_indicators(df)
        df = add_atr(df)
    except Exception as e:
        errors.append(f"{stock}: load error — {e}")
        continue

    # Generate signals ONCE per stock — same signals for all 16 combos
    try:
        from core.strategy import BounceStrategy
        signals = BounceStrategy().generate_signals(df)
        signal_map = {}
        for s in signals:
            signal_map.setdefault(s["datetime"], []).append(s)
    except Exception as e:
        errors.append(f"{stock}: signal error — {e}")
        continue

    for atr_name, atr_cfg in ATR_CONFIGS.items():
        for var_name, var_cfg in VARIANTS.items():
            combo_key = f"{atr_name}-{var_name}"
            try:
                portfolio = Portfolio(
                    atr_mult_stop     = atr_cfg["sl_mult"],
                    rr_target         = atr_cfg["tp_mult"] / atr_cfg["sl_mult"],
                    sl_variant        = var_cfg["sl_variant"],
                    breakeven_trigger = var_cfg["breakeven_trigger"],
                    trailing_dist     = var_cfg["trailing_dist"],
                )
                for i in range(len(df)):
                    bar = df.iloc[i]
                    dt  = bar.datetime
                    if dt in signal_map:
                        for sig in signal_map[dt]:
                            portfolio.open_position(sig, bar, i)
                    portfolio.update(bar, i)
                trades = portfolio.trades_df()
                if len(trades) > 0:
                    combo_results[combo_key].append(trades)
            except Exception as e:
                errors.append(f"{stock}/{combo_key}: {e}")

    print(f"  done: {stock}", flush=True)

elapsed = time.time() - t0
print(f"\nBatch done in {elapsed:.1f}s")

# ─── SAVE BATCH RESULTS ────────────────────────────────────────────────────────
import pickle, os
RESULTS_CACHE = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / "run16_combo_results.pkl"
if RESULTS_CACHE.exists():
    with open(RESULTS_CACHE, "rb") as f:
        prior = pickle.load(f)
    for k, v in combo_results.items():
        prior[k].extend(v)
    combo_results = prior
with open(RESULTS_CACHE, "wb") as f:
    pickle.dump(combo_results, f)
print(f"Results saved to {RESULTS_CACHE}")

# ─── AGGREGATE & RANK ──────────────────────────────────────────────────────────
rows = []
for combo_key, trade_list in combo_results.items():
    atr_name, var_name = combo_key.rsplit("-", 1)

    if not trade_list:
        rows.append({
            "combo": combo_key, "atr": atr_name, "variant": var_name,
            "trades": 0, "win_rate": 0, "profit_factor": 0,
            "total_pnl": 0, "cagr_pct": 0,
        })
        continue

    all_trades = pd.concat(trade_list, ignore_index=True)
    n          = len(all_trades)
    win_rate   = (all_trades["reason"] == "target").sum() / n * 100

    gross_profit = all_trades.loc[all_trades["pnl"] > 0, "pnl"].sum()
    gross_loss   = all_trades.loc[all_trades["pnl"] < 0, "pnl"].abs().sum()
    pf           = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    total_pnl    = all_trades["pnl"].sum()
    final_equity = INITIAL_CAPITAL + total_pnl
    cagr         = ((final_equity / INITIAL_CAPITAL) ** (1 / YEARS) - 1) * 100

    rows.append({
        "combo":         combo_key,
        "atr":           atr_name,
        "variant":       var_name,
        "trades":        n,
        "win_rate":      round(win_rate, 1),
        "profit_factor": round(pf, 3),
        "total_pnl":     round(total_pnl, 0),
        "cagr_pct":      round(cagr, 2),
    })

results_df = pd.DataFrame(rows).sort_values("cagr_pct", ascending=False).reset_index(drop=True)

# ─── PRINT RANKED TABLE ────────────────────────────────────────────────────────
print()
print(f"{'Rank':<5} {'Combo':<16} {'ATR':<12} {'Var':<5} {'Trades':>7} "
      f"{'Win%':>7} {'PF':>7} {'Total PnL':>14} {'CAGR%':>8}")
print("─" * 85)

for rank, row in results_df.iterrows():
    print(
        f"  {rank+1:<4} {row['combo']:<16} {row['atr']:<12} {row['variant']:<5} "
        f"{int(row['trades']):>7} {row['win_rate']:>7.1f} {row['profit_factor']:>7.3f} "
        f"{row['total_pnl']:>14,.0f} {row['cagr_pct']:>8.2f}%"
    )

print()
print(f"Best combo : {results_df.iloc[0]['combo']}  "
      f"CAGR={results_df.iloc[0]['cagr_pct']:.2f}%  "
      f"PF={results_df.iloc[0]['profit_factor']:.3f}")

if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
