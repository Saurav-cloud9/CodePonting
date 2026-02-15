"""
BACKTEST RUNNER

Responsibility:
- Load config (backtest.yaml).
- Initialize adapters, engine, strategy.
- Execute backtest run.
- Save results to outputs/.

Usage:
    python run_backtest.py --config configs/backtest.yaml
"""

from pathlib import Path
import pandas as pd

# Framework imports
from core.indicators import (
    add_intraday_indicators,
    compute_daily_mas,
    add_atr
)
from core.engine import BacktestEngine


# =========================================================
# CONFIG
# =========================================================
DATA_PATH = Path("../data/historical/intraday_5min/TATASTEEL_test.parquet")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

TRADES_OUT = OUTPUT_DIR / "trades.csv"
EQUITY_OUT = OUTPUT_DIR / "equity.csv"


# =========================================================
# LOAD DATA
# =========================================================
print("Loading data...")
df = pd.read_parquet(DATA_PATH)

# Ensure datetime dtype
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)


# =========================================================
# INDICATORS PIPELINE
# =========================================================
print("Building indicators...")

df = add_intraday_indicators(df)
df = compute_daily_mas(df)
df = add_atr(df)


# =========================================================
# RUN BACKTEST
# =========================================================
print("Running backtest...")

engine = BacktestEngine(df)

trades, equity, stats = engine.run()


# =========================================================
# SAVE OUTPUTS
# =========================================================
print("Saving results...")

trades.to_csv(TRADES_OUT, index=False)
equity.to_csv(EQUITY_OUT, index=False)

print(f"Trades saved -> {TRADES_OUT}")
print(f"Equity saved -> {EQUITY_OUT}")


# =========================================================
# STATS PRINT
# =========================================================
print("\n===== STATS =====")
print(pd.Series(stats))
