# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  fv2 baseline — sort out exact formula + numbers AND reconcile trade-count discrepancy
        Source of truth: fv2_batch_build.py (no open>MA — that's a temp-script artifact)
        Re-verified 2026-06-16: no-vol N=51,803 PF=0.918 | with-vol N=44,823 PF=0.906
        _temp_per_stock_baseline.py / _temp_fv2_baseline.py gave N=136,849/195,475 (3-4x off) —
        root cause not isolated yet. Save final formula+numbers to CLAUDE.md + guides/ once resolved.

P2  HMA Bounce — side-by-side comparison vs SMA20 baseline pending
        hma_bounce_backtest.py exists (raw PF=0.944 vs SMA 0.918)
        Next: per-stock table comparing HMA vs SMA with TGT-WR, PFT-WR, BE%, PF

P3  Trading ABC — Top-9 subset found (PF=1.197, N=911) vs full-universe PF=0.849-0.878
        Next: walk-forward test subset stability (overfit risk on 4yr in-sample stock pick)

P4  Kijun filter on top of MA20 Bounce
        Use Kijun level as quality filter for existing fv2 MA Bounce signal

P5  RSI + MACD as signal refinement filters for fv2 / Codedex learning track
        RSI overbought/oversold + MACD momentum to filter/confirm bounce signals
        Codedex: current Pandas (ex8 messy data); next Matplotlib → SQL → GenAI

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
