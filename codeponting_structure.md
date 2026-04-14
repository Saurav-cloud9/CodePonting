# CodePonting — Project Structure

**Status:** fv1 CLOSED (2026-03-25). fv2 ACTIVE — true MA bounce redesign, TATAMOTORS 5-min, Gap 1 implemented.
**Strategy:** MA Bounce — 6 classic bounce criteria (fv2). fv1 was proximity detector, not true bounce.

**API Integrations:** Upstox (live trading) · Zerodha Kite (via MCP server)

---

## Root

| File | Description |
|------|-------------|
| `.env` | Upstox API credentials (API_KEY, API_SECRET, ACCESS_TOKEN) |
| `.gitignore` | Ignores Python cache, IDE files, env, large data files |
| `.mcp.json` | MCP server config for Kite API (endpoint: mcp.kite.trade) |
| `README.md` | Project overview — MA Bounce Bot v1.3 description |
| `upstox_auth.py` | OAuth2 token generation for Upstox API |
| `codeponting_structure.md` | This file |

---

## Algo_Trading/

### Docs/

| Path | Description |
|------|-------------|
| `Docs/Architecture/Core_Framework.md` | 10-pillar backtesting framework blueprint (offline data, indicator caching, strategy as pure function, decoupled execution) |
| `Docs/Architecture/One System, Three Environments.md` | Unified system design: backtest / paper trade / live trade modes |
| `Docs/Progress/self_progress_tracker_2026.md` | Daily journal from Jan 30 2026 onwards — Framework_V1 development log |
| `Docs/Archive/` | Historical docs: handover notes, credit spreads, sentiment analysis, Kite guide, trading bot blueprints |

---

### Framework_V0/ — Legacy Bot (v0.1 → v1)

Original live bot implementations before the modular architecture was established.

#### Equity/MA_BOUNCE_BOT/

| Version | Description |
|---------|-------------|
| `v0.1 – v0.4` | Early MA bounce bot iterations with debug files |
| `v0.5` | Debug version with 5-min candle analysis |
| `v0.6_PLATINUM` | Refined version |
| `v0.7(GameChanger)` | Enhanced version with activity logs (PDF trading docs) |
| `v0.8` | Refinement + `trades_log_master.csv` (live trade records) |
| `v0.9(back_test version)` | Backtesting variant |
| `v1/` | Latest live bot — daily run logs `LiveBot_12thJAN` → `LiveBot_18thJAN` (Jan 2026) |

#### Equity/REPORT GENERATOR/

| File | Description |
|------|-------------|
| `daily_report_FINAL_COMPLETE.py` | Comprehensive daily trade report generator |
| `daily_report_ENHANCED_v2.py` | Enhanced report with additional metrics |
| `daily_report_FIXED_with_timeline.py` | Timeline-based daily report |

#### Equity/Strategy Developer/MA Bounce Strategy/

| Path | Description |
|------|-------------|
| `Blue Print/` | Core strategy definition files |
| `BackTesting_Realistic_Execution/` | Realistic execution backtests with SQLite DBs (48-month, multicore, anti-chasing filter variants) |
| `GSS_Validation/GSS_V4_Optimization/` | Golden Section Search parameter optimization v4 |
| `GSS_Validation/GSS_V5_Option_A_Validation/` | GS Search v5 Option A validation |
| `until_19thJAN/` | Dated backtest runs: `BackTesting_10thJAN` → `BackTesting_19thJAN` (timestamped) |

#### Equity/Test and Practice runs/

Misc test scripts: `ma_bounce_scanner.py`, `market_data_puller.py`, `check_orders.py`, `execute_protected_trade.py`, dry runs, utilities (20+ files).

#### Options/Dad's Acc/

Options trading strategy implementation for a secondary account.

---

### Framework_V1/ — Current Production Framework

**Architecture:** Adapter Pattern + Strategy Pattern. One codebase, three environments via dependency injection.

```
Backtest  →  Parquet data adapter  +  Stepped clock  +  Simulated broker
Paper     →  Upstox API adapter    +  Event clock     +  Simulated broker
Live      →  Upstox API adapter    +  Event clock     +  Live Upstox broker
```

#### core/

| File | Description |
|------|-------------|
| `engine.py` | Event-driven backtesting engine — coordinates signals, portfolio updates, main loop |
| `strategy.py` | `BounceStrategy` class — `generate_signals()` pure function (MA20, 15–30 target price detection) |
| `portfolio.py` | Portfolio state — position tracking, cash, PnL, risk constraints |
| `indicators.py` | Technical indicator calculations — MA20, ATR, volume moving averages |
| `metrics.py` | Performance metrics — Sharpe ratio, win rate, equity curve |

#### adapters/

| File | Description |
|------|-------------|
| `broker/live.py` | Live Upstox API broker — real market order execution |
| `broker/simulated.py` | Paper trading simulator — latency + slippage modeling |
| `clock/event.py` | Event-driven clock for live market feed |
| `clock/stepped.py` | Stepped clock for backtesting (row-by-row over historical data) |
| `data/parquet.py` | Parquet file loader for offline backtesting |
| `data/upstox.py` | Upstox API data fetcher for live/historical data |

#### configs/

| File | Description |
|------|-------------|
| `backtest.yaml` | Backtesting mode configuration |
| `paper.yaml` | Paper trading configuration |
| `live.yaml` | Live trading configuration |

#### data/historical/

| Path | Description |
|------|-------------|
| `daily/` | Daily OHLCV candles — 30 stocks + NIFTY50 (Parquet) |
| `intraday_5min/` | 5-min OHLCV candles — 30 stocks + NIFTY50 (Parquet, primary dataset) |
| `intraday_5min_DS3/` | DS3-format 5-min candles with chunked loading |
| `ds3_tokens_chunks.json` | Token metadata for DS3 chunked data loading |

**Coverage:** 11 years (2015–2025) · 30 NSE F&O stocks + NIFTY50

#### scripts/

| File | Description |
|------|-------------|
| `download_data.py` | Downloads 11yr historical data from Upstox API → Parquet (30 stocks, 5-min + daily) |
| `compute-indicators.py` | Precomputes all indicators (MA20, ATR, volume avg) → `data/indicators/` |
| `create_trading_db.py` | Builds SQLite trading database from trade records |
| `diagnose_carry_over.py` | Debugs position carry-over issues between sessions |
| `run_backtest.py` | Main backtest execution runner |
| `run_backtest_fast.py` | Optimized fast backtest with multicore support |
| `std_analysis.py` | Standard statistical analysis of backtest results |
| `ds3_build.py` | Builds DS3 chunked dataset |
| `ds3_append.py` | Appends data to DS3 dataset |
| `ds3_finalize.py` | Finalizes DS3 dataset |
| `ds3_process_toolfiles.py` | Processes tool files for DS3 |

#### research/

| File | Description |
|------|-------------|
| `optuna_runner.py` | Optuna-based hyperparameter optimization framework |
| `stress_test.py` | Stress testing under extreme market scenarios |
| `walk_forward.py` | Walk-forward out-of-sample validation |

#### Notebooks/

| File | Description |
|------|-------------|
| `01_data_download_exploration.ipynb` | Upstox API exploration, downloading data, Parquet creation |
| `02_indicator_calculation.ipynb` | Computing and visualizing technical indicators |
| `03_bounce_detection.ipynb` | Bounce signal detection logic and testing |
| `NIFTY50.ipynb` | NIFTY50 index analysis |
| `parquest and csv.ipynb` | Data format conversion utilities |

#### outputs/

| Path | Description |
|------|-------------|
| `reports/avg_vs_std.png` | Average return vs std deviation chart |
| `reports/monthly_pnl_trend.png` | Monthly P&L trend chart |
| `reports/sharpe_ratio.png` | Sharpe ratio comparison chart |
| `trades/fv1_30stocks_results.csv` | 30-stock backtest performance summary |
| `trades/fv1_all_trades.csv` | Full trade log across all stocks |
| `trades/carry_over_diagnostic.csv` | Position carry-over diagnostics |
| `trades/equity.csv` | Equity curve data |

#### Framework_V1_Sandbox/ — CLOSED ❌

Closed alongside fv1 (2026-03-25). All experiments complete. Read-only reference.

Key outputs:
- `bqs_trades.parquet` — 28,085 trades, 38 cols (R1+R2 BQS metrics)
- `bqs_filter_cagr.py` — 9-filter CAGR replay, F4 best (+0.62% raw, -Rs62k after Upstox)
- `BQS_DECISIONS.md` — charge formulas, w1/w2/w3 definitions, all 19 metric verdicts
- DT/RF scripts: `bqs_dt_rf.py`, `bqs_leaf_analysis.py`

---

### Framework_V2/ — ACTIVE DEVELOPMENT ✅

True MA bounce redesign. Same adapter/core architecture as fv1. TATAMOTORS-only for now.

#### data/historical/csv/intraday_5min/

| File | Description |
|------|-------------|
| `TATAMOTORS_5min.csv` | 73,174 rows, 7 cols + outcome columns |
| | Cols: open, high, low, close, volume, ma20 |
| | Outcome cols: signal_type, exit_reason, raw_pnl, win |
| | Coverage: 2022–2025, MA20 pre-warmed (0 NaN) |
| | Signals: 1,511 total — rising 319, flat 458, falling 734 |

#### outputs/reports/

| File | Description |
|------|-------------|
| `fv2_signal_viewer.html` | HTML1 — signal viewer, Gap 1 toggle, year/month/day navigator |
| `fv2_calculator.html` | HTML2 — Panel A vs B calculator, delta bar, slope breakdown |
| | Panel A (all signals): CAGR -172%, MDD -169%, PF 0.77, WR 16.4% |
| | Panel B (rising only): CAGR -2.07%, MDD -17.88%, PF 0.95, WR 20.4% |

#### core/ / adapters/ / configs/ / scripts/ / research/

Same structure as Framework_V1 — scaffolded, active development.

---

### Kaggle/

| File | Description |
|------|-------------|
| `download_kaggle.py` | Downloads Kaggle datasets |
| `validate_kaggle.py` | Validates 5 stocks vs Framework_V1 source (0.05% OHLC tolerance, 1% volume tolerance) for Jan–Mar 2022 |
| `validate_all_datasets.py` | Comprehensive validation across all Kaggle datasets |
| `dataset1/` | Raw minute-level CSV (regenerable) |
| `dataset2/` | Alternative data source |
| `validation/` | Validation reports and analysis outputs |

---

### Options/

| Path | Description |
|------|-------------|
| `RKO BOT/` | RKO options bot implementation |

---

## Learning/

| Path | Description |
|------|-------------|
| `Coding_Challenge_1.py` | First coding challenge solution |
| `Tests/Practice1–9.py` | Core Python practice exercises |
| `Tests/Test.py – Test18.py` | Progressive learning exercises (with sub-series: Test13_1–5, Test14_1, Test17_1) |
| `Tests/rough.py` | Rough experimentation |
| `Archive/` | Old learning files |

---

## Personal/

| File | Description |
|------|-------------|
| `TODOS.md` | Personal task list — apartment maintenance fundamentals, life skills |

---

## Stats

| Category | Count |
|----------|-------|
| Python files total | 250+ |
| Framework_V0 `.py` files | 187 |
| Framework_V1 `.py` files | 50+ |
| Framework_V2 `.py` files | 30+ |
| Learning `.py` files | 55+ |
| Jupyter notebooks | 11 |
| Markdown docs | 20+ |
| SQLite databases | 8+ (mega backtest results) |
| Parquet files | 60+ (30 stocks × 2 timeframes + indicators) |
| CSV trade logs | 50+ |

---

*Last updated: 2026-03-27*