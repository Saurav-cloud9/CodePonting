# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Lock both baselines into baseline_reserve/
        Copy ma_bounce.py + ma_rejection.py from baseline_explorations/ → baseline_reserve/
        These become the v0 LONG and SHORT locked reference files

P2  Explore AWS EC2 for fv2 backtesting
        Spin up a test EC2 instance; run fv2 backtests from PC + mobile
        Goal: strategy testing on the go (ideas from online, TV, etc.) without local setup

P3  Analyse SHORT vs LONG edge — why rejection beats bounce
        Structural factors (price behaviour at MA), use TV visualisation
        Document findings before building v1

P4  Build SHORT v1 — wick-only SHORT (mirror of LONG v1 structural mod)
        Proper clean build; run stockwise + yearwise; log to iteration_log.md
        Then: equity curve, drawdown, NPF analysis

P5  Debug runner scripts (run_baseline_v*.py)
        Minor errors found — debug and verify all 5 run cleanly

# ── PARKED / FUTURE ───────────────────────────────────────────
F1  Single-stock trade dump (TATAMOTORS) — verify SHORT calculations
        Print raw trade list: entry bar, entry_px, SL, TGT, exit_px, outcome
F2  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)
F2  Volume Spike Exhaustion — hypothesis parked
F3  Compare H1 vs export_h5_signals.py signal scanning logic
F4  Claude-in-Claude Artifacts — paste OHLCV, get signal analysis in browser
F5  YouTube Strategy Scanner (post paper-trading)
F6  Insurance review
F7  Stock diversity analysis — check if 5 stocks fire on same days
F8  Portfolio construction — capital allocation across stocks
F9  Checkout VSCode Agent
F10 TradingView AI Chart Copilot

# ── GLOSSARY ──────────────────────────────────────────────────
## Signal Geometry
# T0          — touch bar: candle where price touches MA20 or Kijun
# tb_gap      — touch-to-bounce gap: bars between T0 and bounce bar
# diff        — bars between bounce bar and entry bar

## Kijun Strategy
# Kijun-HL    — traditional Ichimoku: (highest HIGH + lowest LOW) / 2 over 50 days
# Kijun-Close — Pine Script variant: (highest CLOSE + lowest CLOSE) / 2 over 50 days
# touch bar   — 5-min bar where low dips below daily Kijun, open above
# confirm bar — next bar: low back above Kijun, close > low
# entry bar   — bar after confirm: entry at open

## Gates & Params
# G1          — Gate 1: pre-touch regime check
# G2          — Gate 2: touch & bounce quality
# G3          — Gate 3: post-bounce follow-through
# p11         — G3a (live-compatible): entry bar open > bounce bar close
# p12         — DROPPED: entry bar volume (lookahead)

## Regime (Big Beluga)
# Red         — strong downtrend + above-average volume
# Yellow      — weak downtrend + below-average volume
# Green       — uptrend + above-average volume
# Blue        — weak uptrend + below-average volume

## Metrics & System
# PF          — raw profit factor (Python backtest, zero charges)
# TPF         — TradingView Profit Factor (brokerage only, 0.05%/side)
# NPF         — Neo Profit Factor (Kotak Neo): full real-world charges (brokerage + statutory)
# CBQ         — Charge Break-even Qty: NPF vs qty sweep to find the quantity where charges are overcome
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# R/R         — reward/risk ratio
# BE          — breakeven W/(W+L) = SL/(SL+TGT)
# MFE         — Max Favourable Excursion (best point trade reached, in ATR units)
# MAE         — Max Adverse Excursion (worst point trade reached, in ATR units)

## Frameworks & Data
# fv2         — Framework V2 (active)
# H5          — fv2 gate tuner HTML viewer
# tb3/tb9     — bounce search window variants (3 or 9 bars)
# DS3         — primary historical dataset (29 stocks, 2015-2025, 5-min parquet)
