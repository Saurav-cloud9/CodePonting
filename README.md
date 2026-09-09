# CodePonting — Algorithmic Trading System

Quantitative research and live paper-trading system for NSE F&O equities, built with Claude Code as an agentic execution layer.

## Status

| Framework | Status | Notes |
|-----------|--------|-------|
| Framework_V0 | ⛔ Archived | Legacy bot v0.1–v1 |
| Framework_V1 | ❌ Closed (2026-03-25) | Signal insufficient — charges 3.4× raw profit at scale |
| Framework_V1_Sandbox | ❌ Closed | BQS + DT/RF experiments exhausted, no viable filter found |
| **Framework_V2** | ✅ **Active** | 6 strategy variants deployed to the live paper-trading bot for monitoring |

**Market:** NSE F&O equities (India) — 30-stock universe (29 DS3 + BAJFINANCE)
**Brokers:** Kotak Neo (primary) · Zerodha Kite (paper-trading bot, live)

## What's Actually Running

A daily **paper-trading bot** (`kite_oracle_papertrading/`, deployed on an Oracle Cloud VM) trades the fv2 strategy variants live against real market data via the Zerodha Kite API — not backtested, actually executing during market hours every trading day, while results are monitored before anything is treated as final.

- **Lifecycle:** auto-login (systemd timer, 08:55 IST) → warm-up → live trading (09:15–15:30 IST) → EOD tick-exit square-off → auto-stop
- **Hardened for unattended operation:** systemd auto-restart on crash/reboot, crash-safe position recovery, ntfy push alerts to desktop/phone on failure
- **Reconciliation:** daily settled-trade recon (weekday cron) + monthly full reconciliation (1st of month) against official Kite bars, with 95% confidence-interval alpha/beta reporting (distinguishes "confidently near-zero" edge from "genuinely inconclusive")

## fv2 Strategy Families (Tracked & Monitored)

Six SL/TP-tuned variants, each swept and deployed into the live bot's monthly reconciliation report — being monitored, not yet finalized:

| Variant | SL / TP | Notes |
|---|---|---|
| `ma_short_v1` | 4.5 / 3.0 | MA-rejection SHORT, baseline |
| `ma_short_v2_vwap` | 4.5 / 3.0 | VWAP-filtered variant |
| `6bce_v0` | 8.0 / 3.0 | |
| `6bce_v1_vwap` | 4.5 / 3.0 | VWAP-filtered variant |
| `ma_long_flip_v0` | 7.0 / 3.0 | Flagged inconclusive (wide 95% CI) — not confidently zero |
| `ma_long_flip_vwap` | 4.0 / 3.0 | |

**Recent finding (2026-09-04):** a systematic EOD-riding artifact was found inflating every strategy family's top-ranked SL/TP combo — wide SL/TP barely binds intraday, so trades were riding to the EOD square-off regardless of signal quality, not reflecting genuine directional edge. Now a mandatory diagnostic (`backtesting_rules.md`: SL%/TP%/EOD+%/EOD-% breakdown) before trusting any ranked combo.

**v1 clean-touch SHORT** (earlier config, cross-validated array backtest + offline engine): SL=2.0×/TP=4.5× → PF=1.135, Sharpe=2.358, 110,641 trades across DS3's full 11-year history.

## Data

- **DS3** — 30 stocks, 5-minute OHLCV, 2015–2025 (11 years), with `ma20`/`atr14` precomputed. Primary dataset for all current research.
- **NIFTY50 daily** — same 11-year coverage, used as the market-return benchmark for alpha/beta CAPM analysis.

## Research Track (MemLabs)

A parallel statistical-rigor thread (`Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/`) — CAPM alpha/beta derivations, Pearson-r feature screening, walk-forward validation — used to stress-test whether any candidate signal survives formal significance testing before it's trusted. Repeated finding: several candidate edges (regime filters, online-learning models, raw feature signals) do **not** survive — a deliberately skeptical check on the live strategies above, not itself a source of new signals.

## fv1 (Closed — historical reference)

Proximity-based MA20 touch detector (not a true bounce): 28,085 trades over 4 years, transaction charges exceeded raw profit under every filter variant tested. Frozen as a learning record; do not modify or build on it.

## Project Structure (current)

```
CodePonting/
├── Algo_Trading/
│   ├── Framework_V2/
│   │   ├── data/historical/intraday_5min_DS3/   # 30-stock 5-min dataset, 2015–2025
│   │   ├── data/historical/daily/NIFTY50.parquet
│   │   ├── scripts/trials/regime_model/memlabs/ # MemLabs research (alpha/beta, feature screening)
│   │   ├── strategies/                          # 6 tracked SL/TP variants (see table above)
│   │   └── backtesting_rules.md                 # EOD-exit logic, ATR SL/TP convention, NPF formula
│   └── kite_oracle_live_trading/                # Live-trading infra, gated on paper validation
├── PROGRESS.md / PROGRESS_HISTORY.md / TODO.md  # Session continuity (see CLAUDE.md)
├── CLAUDE.md                                     # Behavioral instructions for Claude Code
└── CCG_ORCHESTRATION.md                          # Task delegation log (Claude Code ↔ Grok)
```

The live paper-trading bot itself (`kite_oracle_papertrading/`) runs outside this repo, on the same Oracle Cloud VM — kept separate from research code by design.

## Roadmap

- [x] fv2 signal designed and 6 SL/TP variants deployed for monitoring
- [x] Deployed to live paper-trading bot with daily + monthly reconciliation
- [x] Systematic EOD-riding artifact found and fixed
- [ ] MemLabs research track — ongoing significance testing of candidate features/regimes
- [ ] Sustained clean paper-trading track record before considering real capital
- [ ] Live trading via Zerodha Kite, gated on paper-trading validation

## Risk Disclosure

**This is a research and paper-trading system. Nothing here constitutes financial advice, and no live capital is currently at risk under Framework_V2.** Framework_V1 was closed specifically because a promising-looking backtest failed to survive real transaction costs — a reminder that a good raw signal is not the same as a profitable one.

## Contributing

Solo project — not currently seeking external contributions.

## License

Open Source — Research & Educational purposes

## Author

**Saurav (CodePonting)**
Quant Developer | Quantitative Systematic Trader | Strategy Researcher | Trading Infrastructure Engineer

*Built with Claude Code as an agentic development and research partner.*

---

**Trading involves risk. Use at your own discretion.**
