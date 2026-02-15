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
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pathlib import Path
import pandas as pd

# Framework imports
from core.indicators import (
    add_intraday_indicators,
    compute_daily_mas,
    add_atr
)
from core.engine import BacktestEngine
from core.portfolio import Portfolio  # Add this line

# =========================================================
# ATR CONFIGS
# =========================================================

ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tgt_mult': 4.0},
    'Extreme-2': {'sl_mult': 2.5, 'tgt_mult': 4.5},
    'Extreme-3': {'sl_mult': 3.0, 'tgt_mult': 4.5},
    'Extreme-4': {'sl_mult': 3.0, 'tgt_mult': 5.0}
}

all_trades = []


# =========================================================
# CONFIG
# =========================================================
STOCK_FILES = list(Path("../data/historical/intraday_5min/").glob("*.parquet"))

DATA_PATH = "../data/historical/intraday_5min/TATASTEEL.parquet"  # INPUT
OUTPUT_DIR = Path("../outputs/trades")  # Add Path()
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
# RUN BACKTEST - ALL CONFIGS
# =========================================================
print("Running backtest for all ATR configs...")

all_trades = []

for config_name, config in ATR_CONFIGS.items():
    print(f"\n=== Running {config_name} ===")

    engine = BacktestEngine(df)
    engine.portfolio = Portfolio(
        atr_mult_stop=config['sl_mult'],
        rr_target=config['tgt_mult'] / config['sl_mult']
    )

    trades, equity, stats = engine.run()
    trades['atr_config'] = config_name
    all_trades.append(trades)

    print(f"Trades: {len(trades)}, PnL: {stats['net_pnl']:.2f}")

# Combine all configs
final_trades = pd.concat(all_trades, ignore_index=True)

# =========================================================
# SAVE OUTPUTS
# =========================================================
print("Saving results...")

final_trades.to_csv(TRADES_OUT, index=False)

print(f"Trades saved -> {TRADES_OUT}")
print(f"Total trades across all configs: {len(final_trades)}")

# =========================================================
# STATS SUMMARY
# =========================================================
print("\n===== STATS BY CONFIG =====")
for config_name in ATR_CONFIGS.keys():
    config_trades = final_trades[final_trades['atr_config'] == config_name]
    wins = (config_trades['pnl'] > 0).sum()
    total = len(config_trades)
    net_pnl = config_trades['pnl'].sum()
    win_rate = wins / total if total > 0 else 0

    print(f"\n{config_name}:")
    print(f"  Trades: {total}")
    print(f"  Win Rate: {win_rate:.2%}")
    print(f"  Net PnL: ₹{net_pnl:,.2f}")
