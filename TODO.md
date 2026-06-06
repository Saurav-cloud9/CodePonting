# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Await Claude.ai discussion outcome — next action TBD
        Context: regime filter WFA complete; worst years are dead regimes (zero valid days)
        Options on table: (a) year-level go/no-go gate, (b) signal redesign, (c) Optuna on regime-approved years only
        Also in play: Opus plan — ER + MA20 run-length + VR as alternative regime metrics

P2  Regime gate implementation — define as year/month-level pre-filter using ATR14% + Vol_StdDev20%
        Thresholds found: ATR14% >= 2.25%, Vol_StdDev20% >= 65%
        Re-run Optuna only on approved periods

P3  Voice Bridge — end-to-end test: trigger write_instruction from Claude Desktop,
        confirm instructions.txt gets written, voice_bridge.py picks it up in CC terminal

P4  Re-run Optuna on regime-approved stock-years only (after P1/P2 resolved)
        Goal: higher PF per stock rather than broad N coverage

P5  Opening bar framework — 9:15 signals need separate G1 evaluation

# ── PARKED / FUTURE ───────────────────────────────────────────
F0  Compare H1 vs export_h5_signals.py signal scanning logic
F1  Claude-in-Claude Artifacts — paste OHLCV, get signal analysis in browser
F2  Signal replacement / position upgrade logic (post-WFA)
F3  YouTube Strategy Scanner (post paper-trading)
F4  Insurance review
F5  Stock diversity analysis — check if 5 stocks fire on same days
F6  Portfolio construction — capital allocation across 5 stocks
F7  Checkout VSCode Agent
F8  TradingView AI Chart Copilot
F9  If regime filter fails OOS → pivot to ORB strategy (reuse all fv2 infra)

# ── GLOSSARY ──────────────────────────────────────────────────
## Signal Geometry
# T0          — touch bar: candle where price touches MA20
# tb_gap      — touch-to-bounce gap: bars between T0 and bounce bar
# diff        — bars between bounce bar and entry bar

## Gates & Params
# G1          — Gate 1: pre-touch regime check
# G2          — Gate 2: touch & bounce quality
# G3          — Gate 3: post-bounce follow-through
# p11_open    — G3a (live-compatible): entry bar open > bounce bar close
# p12         — DROPPED: entry bar volume (lookahead)

## Regime
# Regime filter  — pre-condition above G1/G2/G3; says "bounce-friendly day or not"
# Bounce rate    — % of raw touch signals that naturally bounce (no filters applied)
# Mean-reversion — price oscillates around MA20; suits our signal
# Trending       — price stays above/below MA20 for extended periods; breaks our signal
# ER             — Efficiency Ratio: |net move| / sum(|bar moves|); ER→0=chop, ER→1=trend
# Run-length     — mean consecutive bars on same side of MA20; short=oscillating, long=trending
# VR             — Variance Ratio: Var(30-min returns) / (6 × Var(5-min returns)); VR<1=mean-reverting

## Metrics & System
# PF          — profit factor
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# R/R         — reward/risk ratio

## Frameworks & Data
# fv2         — Framework V2 (active)
# H5          — fv2 gate tuner HTML viewer
# tb3/tb9     — bounce search window variants (3 or 9 bars)
