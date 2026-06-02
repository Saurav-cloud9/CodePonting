# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Regime filter — NEXT PRIORITY
        Step 1: Break down all 4 years (2022/2023/2024/2025) by month
                Find best and worst months within each year across 5 stocks
        Step 2: Compute raw bounce success rate per year and per month
                Check if 2022/2023 naturally higher than 2024/2025
        Step 3: Identify what is mathematically common between good periods
                and bad periods — quantify into a measurable metric
        Step 4: Define regime metric → plot → overlay Optuna results
        Step 5: Translate findings into a filter formula for the live script

P2  Voice Bridge — end-to-end test: trigger write_instruction from Claude Desktop,
        confirm instructions.txt gets written, voice_bridge.py picks it up in CC terminal

P3  Re-run Optuna with lower N floor (50-60 signals) after regime filter defined
        Goal: higher PF per stock rather than broad N coverage

P4  Opening bar framework — 9:15 signals need separate G1 evaluation

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
