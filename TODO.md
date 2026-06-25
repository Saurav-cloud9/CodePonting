# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Trading ABC — apply A/B/C stock classification filter on 30-stock baseline
        Top-9 subset found earlier: PF=1.197, N=911 vs full-universe PF=0.922
        Next: re-run ABC filter on ma_bounce.py baseline + walk-forward test for overfit check

P2  RSI + MACD filters — apply on ma_bounce.py baseline as signal refinement
        RSI overbought/oversold + MACD momentum to filter/confirm bounce signals
        Codedex: current Pandas (ex8 messy data); next Matplotlib → SQL → GenAI

P3  HMA Bounce — revisit later
        hma_bounce_backtest.py exists (raw PF=0.944 vs SMA 0.922)
        Parked until P1+P2 explored on SMA baseline

P4  Kijun filter — may skip depending on P1+P2 results
        Use Kijun level as quality filter for existing fv2 MA Bounce signal

P5  fv2 baseline locked ✅
        ma_bounce.py: N=49,039 | PF=0.922 | Prof_WR=41.5% | EOD hard stop 15:00
        No slippage, no charges. 30 stocks, 2022–2025.

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

## Frameworks & Data
# fv2         — Framework V2 (active)
# H5          — fv2 gate tuner HTML viewer
# tb3/tb9     — bounce search window variants (3 or 9 bars)
