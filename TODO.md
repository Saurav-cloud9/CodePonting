# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kijun Bounce — run all 30 stocks on Python (Kijun-HL)
        Script: Algo_Trading/Framework_V2/scripts/kijun_bounce_backtest.py
        Expand STOCKS list to all 30, check which stocks hold PF>1
        Then investigate TV vs Python gap (ATR method, entry price differences)

P2  Kijun Bounce — resolve TV vs Python discrepancy
        TV ADJ mode shows PF=0.759 vs Python Kijun-Close PF=1.37 for ITC
        Likely cause: ATR smoothing method + entry price execution differences
        Fix: match ATR method (Wilder's RMA) and verify signal count alignment

P3  MA Bounce — parked, not abandoned
        Resume after Kijun Bounce investigation completes
        Key open item: share ITC filter findings with Opus on claude.ai before resuming

P4  Re-export H5 signals with p11 bug fixed
        All 30 stocks x 4 years x 2 tb variants need regeneration after p11 fix

P5  Codedex learning track — current: Pandas (ex8 messy data); next: Matplotlib → SQL → GenAI

# ── PARKED / FUTURE ───────────────────────────────────────────
F0  Volume Spike Exhaustion — parked after Kijun Bounce pivot
        Hypothesis: low-vol move → spike cluster (conflict) → resolution → entry
        Resume if Kijun Bounce doesn't hold across 30 stocks
F1  Compare H1 vs export_h5_signals.py signal scanning logic
F2  Claude-in-Claude Artifacts — paste OHLCV, get signal analysis in browser
F3  YouTube Strategy Scanner (post paper-trading)
F4  Insurance review
F5  Stock diversity analysis — check if 5 stocks fire on same days
F6  Portfolio construction — capital allocation across 5 stocks
F7  Checkout VSCode Agent
F8  TradingView AI Chart Copilot
F9  Nifty Futures — Beluga signal on Nifty index (post Kijun Bounce investigation)

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
# PF          — profit factor
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# R/R         — reward/risk ratio
# BE          — breakeven W/(W+L) = SL/(SL+TGT)

## Frameworks & Data
# fv2         — Framework V2 (active)
# H5          — fv2 gate tuner HTML viewer
# tb3/tb9     — bounce search window variants (3 or 9 bars)
