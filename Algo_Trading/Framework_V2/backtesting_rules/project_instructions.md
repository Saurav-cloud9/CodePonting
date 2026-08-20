# Backtesting Project — Framework V2
## NSE Intraday Strategy Development

This project is built to systematically backtest intraday trading strategies on NSE equities using 11 years of 5-minute OHLCV data (2015–2025) across 30 Nifty large-cap stocks.

---

## What We Are Doing

We are developing, backtesting, and validating intraday SHORT strategies with sufficient statistical rigour to deploy in live trading via Zerodha.

The process is iterative:
1. Define an entry signal (strategy hypothesis)
2. Run a 90-combo parameter sweep to find the best SL/TP combination
3. Evaluate results using ZPF and ZSh(D) as primary metrics
4. Add filters or structural modifications to improve signal quality
5. Re-sweep and compare against baseline
6. Repeat until targets are met or the strategy is ruled out

---

## Data

- **Universe:** 30 Nifty large-cap stocks
- **Timeframe:** 5-minute OHLCV bars
- **Period:** 2015–2025 (~11 years)
- **Format:** Parquet files, one per stock
- **Columns:** datetime, open, high, low, close, volume, oi, ma20, atr14

---

## How to Use This Project

- Entry signal rules and any filters will be provided in the chat
- The AI must confirm it has understood the rules before running any backtest
- In case of any ambiguity, ask the user — do not assume
- All output must include the metrics listed in the rules file
- Results should be presented overall AND year-wise (2015–2025)

---

## Targets

- **ZPF > 1.0** — strategy is profitable after Zerodha charges
- **ZSh(D) > 0** — strategy is consistent enough day-to-day
- Both must be met simultaneously for a strategy to be considered viable for paper trading
