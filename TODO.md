# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — resume during tomorrow's login
        EOD tick-based fix + hard auto-stop CONFIRMED working live (2026-07-21, both 14:00
        test cutoff and real 15:00); MODE_FULL timestamp fix applied, needs a longer full-day
        run to fully validate boundary-tick reduction (short test showed no red flags)
        Next: add MA20/ATR14 + touch-eval logging to live_bars.csv — eliminates manual
        reconstruction needed 3x already (INFY/SUNPHARMA/NATIONALUM)
        Reconciliation script bug: fetch window stops at session_end exclusive, never
        captures EOD-triggered exits — needs fixing
        Reconciliation gap root cause: partially traced (startup-corrupted first bar affects
        signal detection — confirmed for JSWSTEEL matching, SUNPHARMA/INFY still need full
        reconstruction-based verification, not just comparison)

P2  Regime-adaptive online learning model — NEW DIRECTION
        Buy MemLabs notebook ($5.50, patreon.com/cw/MemLabs) — card declined, retry
        Adapt passive aggressive regressor to NSE MA rejection SHORT signal
        Features: ATR%, vol, regime state; target: trade win/loss outcome

P3  New signal sweeps via Grok — ongoing, lower priority until regime model built
        VWAP done (both baseline + VWAP variant confirmed dead); next: RSI/MACD combos

P4  Build cloud backtesting engine for paper trading
        Target: run fv2 backtests from any device (mobile/remote) without local setup
        Primary: Oracle Cloud; fallback: AWS EC2

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
# SL/TP       — Stop Loss / Take Profit (standard shortform going forward, replaces
#               TGT in all new scripts starting with the kite paper trading bot;
#               existing files keep TGT, not retroactively renamed)
# PF          — raw profit factor (Python backtest, zero charges)
# ZPF         — Zerodha Profit Factor: PF after full Zerodha intraday charges
# ZSh(D)      — Zerodha Daily Sharpe (annualised): daily zpnl mean/std × √252
# NPF         — Neo Profit Factor (Kotak Neo, archived — Zerodha is now primary)
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# SL          — stop loss (replaces old "SL" in SL/TGT — industry standard)
# TP          — take profit (replaces TGT — industry standard)
# R/R         — reward/risk ratio
# BE          — breakeven W/(W+L) = SL/(SL+TP)
# MFE         — Max Favourable Excursion (best point trade reached, in ATR units)
# MAE         — Max Adverse Excursion (worst point trade reached, in ATR units)

## Frameworks & Data
# fv2         — Framework V2 (active)
# DS3         — primary historical dataset (30 stocks, 2015-2025, 5-min parquet)
