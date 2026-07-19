# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Script fixes for ZPF/ZSh(D) compliance (two changes)
        a) Sharpe → daily: replace monthly resample (×√12) with daily PNL agg (×√252)
        b) Entry bar hour check: add `if hour[i+1] >= 15: skip` after signal detection
        Apply to all sweep scripts in baseline_explorations/ and sweep/

P2  Build cloud backtesting engine for paper trading
        Target: run fv2 backtests from any device (mobile/remote) without local setup
        Primary: Oracle Cloud; fallback: AWS EC2

P3  Lock both baselines into baseline_reserve/
        Copy ma_bounce.py + ma_rejection.py from baseline_explorations/ → baseline_reserve/
        These become the v0 LONG and SHORT locked reference files

P4  Backtest new strategy ideas (TV, online sources)
        Run 90-combo sweep + ZPF/ZSh(D) evaluation on each new signal
        Filters to try: VWAP, RSI, MACD, Beluga oscillator
        Metrics to explore: max drawdown, equity curve, efficient frontier, AUC/ROC

P5  v1_vwap sweep — no fresh 90-combo sweep done yet
        ma_30_rejection_v1_vwap.py exists but SL/TGT not swept
        Run sl_tgt_sweep for v1_vwap SHORT, log results to iteration_log.md

# ── PARKED / FUTURE ───────────────────────────────────────────
F1  Single-stock trade dump (TATAMOTORS) — verify SHORT calculations
F2  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)
F3  Volume Spike Exhaustion — hypothesis parked
F4  Stock diversity analysis — check if 5 stocks fire on same days
F5  Portfolio construction — capital allocation across stocks
F6  Insurance review

# ── GLOSSARY ──────────────────────────────────────────────────
## Signal Geometry
# T0          — touch bar: candle where price touches MA20 or Kijun
# tb_gap      — touch-to-bounce gap: bars between T0 and bounce bar

## Gates & Params
# G1          — Gate 1: pre-touch regime check
# G2          — Gate 2: touch & bounce quality
# G3          — Gate 3: post-bounce follow-through

## Metrics & System
# PF          — raw profit factor (Python backtest, zero charges)
# ZPF         — Zerodha Profit Factor: PF after full Zerodha intraday charges
# ZSh(D)      — Zerodha Daily Sharpe (annualised): daily zpnl mean/std × √252
# NPF         — Neo Profit Factor (Kotak Neo, archived — Zerodha is now primary)
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# R/R         — reward/risk ratio
# BE          — breakeven W/(W+L) = SL/(SL+TGT)
# MFE         — Max Favourable Excursion (best point trade reached, in ATR units)
# MAE         — Max Adverse Excursion (worst point trade reached, in ATR units)

## Frameworks & Data
# fv2         — Framework V2 (active)
# DS3         — primary historical dataset (30 stocks, 2015-2025, 5-min parquet)
