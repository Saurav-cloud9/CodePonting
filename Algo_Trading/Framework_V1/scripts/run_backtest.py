"""
BACKTEST RUNNER - BATCH MODE (ALL STOCKS)

Responsibility:
- Loop through all .parquet files in intraday_5min data folder.
- For each stock, run backtest across all 4 Extreme ATR configs.
- Compute summary metrics per stock+config.
- Save consolidated results to outputs/trades/fv1_30stocks_results.csv.
- Skip and log any stock/config that errors; do not abort full run.

Usage:
    python run_backtest.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from core.indicators import add_intraday_indicators, compute_daily_mas, add_atr
from core.engine import BacktestEngine
from core.portfolio import Portfolio


# =========================================================
# ATR CONFIGS
# =========================================================
ATR_CONFIGS = {
    'Extreme-1': {'sl_mult': 2.5, 'tp_mult': 4.0},
    'Extreme-2': {'sl_mult': 2.5, 'tp_mult': 4.5},
    'Extreme-3': {'sl_mult': 3.0, 'tp_mult': 4.5},
    'Extreme-4': {'sl_mult': 3.0, 'tp_mult': 5.0},
}


# =========================================================
# PATHS
# =========================================================
SCRIPT_DIR = Path(__file__).parent
BASE_DIR   = SCRIPT_DIR.parent
INTRADAY_DIR = BASE_DIR / "data/historical/intraday_5min"
OUTPUT_DIR   = BASE_DIR / "outputs/trades"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRADES_OUT      = OUTPUT_DIR / "trades.csv"
SUMMARY_OUT     = OUTPUT_DIR / "fv1_30stocks_results.csv"
ALL_TRADES_OUT  = OUTPUT_DIR / "fv1_all_trades.csv"


# =========================================================
# DISCOVER STOCKS
# =========================================================
stock_files = sorted(f for f in INTRADAY_DIR.glob("*.parquet") if f.stem != "NIFTY50")
print(f"Found {len(stock_files)} parquet files in {INTRADAY_DIR}")

results          = []   # list of dicts -> summary CSV
errors           = []   # list of error strings to report at the end
all_stocks_trades = []  # accumulates all trades across every stock


# =========================================================
# MAIN BATCH LOOP
# =========================================================
for stock_path in stock_files:
    stock = stock_path.stem
    print(f"\n{'='*60}")
    print(f"  STOCK: {stock}")
    print(f"{'='*60}")

    # --- Load & clean data ---
    try:
        df = pd.read_parquet(stock_path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)

        # Drop candles outside regular market hours (09:15 – 15:30 IST)
        _t = df["datetime"].dt.time
        df = df[_t.between(pd.Timestamp("09:15").time(), pd.Timestamp("15:30").time())]
        df = df.reset_index(drop=True)
        del _t

        # Build indicators
        df = add_intraday_indicators(df)
        df = compute_daily_mas(df)
        df = add_atr(df)

    except Exception as e:
        msg = f"{stock}: data load/indicator error — {e}"
        print(f"  [ERROR] {msg}")
        errors.append(msg)
        traceback.print_exc()
        continue  # skip this stock entirely

    # --- Run all 4 configs ---
    stock_all_trades = []

    for config_name, config in ATR_CONFIGS.items():
        try:
            engine = BacktestEngine(df)
            engine.portfolio = Portfolio(
                atr_mult_stop=config['sl_mult'],
                rr_target=config['tp_mult'] / config['sl_mult'],
            )

            trades, equity, stats = engine.run()
            trades['atr_config'] = config_name
            stock_all_trades.append(trades)

            # --- Compute summary metrics ---
            trade_count = len(trades)

            if trade_count == 0:
                results.append({
                    'stock':        stock,
                    'config':       config_name,
                    'trade_count':  0,
                    'win%':         0.0,
                    'protrades%':   0.0,
                    'eff%':         0.0,
                    'total_pnl':    0.0,
                    'pnl_per_share': 0.0,
                })
                print(f"  {config_name}: 0 trades")
                continue

            win_pct       = (trades['reason'] == 'target').sum() / trade_count * 100
            protrades_pct = (trades['pnl'] > 0).sum() / trade_count * 100
            total_pnl     = trades['pnl'].sum()
            total_qty     = trades['qty'].sum()
            invested      = (trades['entry'] * trades['qty']).sum()
            eff_pct       = (total_pnl / invested * 100) if invested > 0 else 0.0
            pnl_per_share = (total_pnl / total_qty)      if total_qty > 0 else 0.0

            results.append({
                'stock':         stock,
                'config':        config_name,
                'trade_count':   trade_count,
                'win%':          round(win_pct,       2),
                'protrades%':    round(protrades_pct, 2),
                'eff%':          round(eff_pct,       4),
                'total_pnl':     round(total_pnl,     2),
                'pnl_per_share': round(pnl_per_share, 4),
            })

            print(
                f"  {config_name}: {trade_count:4d} trades | "
                f"Win={win_pct:.1f}% | ProTrades={protrades_pct:.1f}% | "
                f"PnL={total_pnl:>12,.2f} | PnL/share={pnl_per_share:.4f}"
            )

        except Exception as e:
            msg = f"{stock}/{config_name}: backtest error — {e}"
            print(f"  [ERROR] {msg}")
            errors.append(msg)
            traceback.print_exc()

    # Accumulate all trades (with stock label) for fv1_all_trades.csv
    if stock_all_trades:
        combined = pd.concat(stock_all_trades, ignore_index=True)
        combined.insert(0, 'stock', stock)
        all_stocks_trades.append(combined)
        combined.drop(columns=['stock']).to_csv(TRADES_OUT, index=False)  # per-stock trades.csv (last stock wins)


# =========================================================
# SAVE SUMMARY
# =========================================================
print(f"\n{'='*60}")
print("Saving consolidated summary...")
results_df = pd.DataFrame(results, columns=[
    'stock', 'config', 'trade_count',
    'win%', 'protrades%', 'eff%', 'total_pnl', 'pnl_per_share',
])
results_df.to_csv(SUMMARY_OUT, index=False)
print(f"  Saved -> {SUMMARY_OUT}  ({len(results_df)} rows)")

if all_stocks_trades:
    all_trades_df = pd.concat(all_stocks_trades, ignore_index=True)
    all_trades_df.to_csv(ALL_TRADES_OUT, index=False)
    print(f"  Saved -> {ALL_TRADES_OUT}  ({len(all_trades_df)} rows)")


# =========================================================
# CROSS-STOCK SUMMARY TABLE
# =========================================================
print(f"\n{'='*60}")
print(f"{'STOCK':<15} {'TRADES':>7} {'WIN%':>7} {'PROTRD%':>8} {'EFF%':>7} {'TOTAL PNL':>14} {'PNL/SHR':>10}")
print(f"{'-'*60}")
by_stock = (
    results_df.groupby('stock')
    .agg(
        trade_count  = ('trade_count',   'sum'),
        win_pct      = ('win%',          'mean'),
        protrades_pct= ('protrades%',    'mean'),
        eff_pct      = ('eff%',          'mean'),
        total_pnl    = ('total_pnl',     'sum'),
        pnl_per_share= ('pnl_per_share', 'mean'),
    )
    .reset_index()
)
for _, r in by_stock.iterrows():
    print(
        f"  {r['stock']:<13} {int(r['trade_count']):>7} "
        f"{r['win_pct']:>7.1f} {r['protrades_pct']:>8.1f} "
        f"{r['eff_pct']:>7.4f} {r['total_pnl']:>14,.2f} "
        f"{r['pnl_per_share']:>10.4f}"
    )


# =========================================================
# ERROR REPORT
# =========================================================
if errors:
    print(f"\n{'='*60}")
    print(f"ERRORS ({len(errors)} total — these stocks/configs were skipped):")
    for err in errors:
        print(f"  - {err}")
else:
    print(f"\nAll stocks processed with no errors.")
