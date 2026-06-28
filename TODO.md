# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Refine fv2 MA Bounce Baseline — improve raw edge (PF 0.908 → >1.01)
        v1 (wick-only touch) confirmed on TV; logic validated against Python (208/209 match)
        Next: explore VWAP context filter (touch below VWAP = bearish context, consider filtering)

P2  Big Beluga indicators — review and assess applicability to fv2 signal
        Look at Beluga-based indicators on TradingView for pattern context ideas
        Regime labels (Red/Yellow/Green/Blue) already in glossary

P3  RSI×MACD combination filter — find zone where both together push PF > 1.0
        rsi_macd_mfe.py already has both indicators; add 2D heatmap: RSI bucket × MACD zone → PF grid
        RSI<30 alone: PF=1.31 (n=53, too small). Need combo to get sufficient sample size.

P4  Trading ABC — apply A/B/C stock classification filter on 30-stock baseline
        Top-9 subset found earlier: PF=1.197, N=911 vs full-universe PF=0.922
        Next: re-run ABC filter on ma_bounce.py baseline + walk-forward test for overfit check

# ── PARKED / FUTURE ───────────────────────────────────────────
F1  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)

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
# PF          — profit factor
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
