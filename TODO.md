# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — resume during live market hours (Monday)
        2026-07-26 progress: 24th July fully reconciled (39 trades stitched across the
        restart, recon script's EOD off-by-one fixed (`>=`->`>` + fetch buffer, applied to
        the real ma_rejection_v1_reconcile.py too), full bar+trade recon run - 09:15
        login-warmup mess and 13:05 skipped-bucket both confirmed real at the bar level;
        of 17 trade mismatches, most are ordinary tick-vs-official noise near-misses;
        RELIANCE/TATAMOTORS/PNB are genuine no-nearby-match exceptions, parked (not worth
        chasing against bugs already fixed) - tomorrow's clean live run is the real judge.
        Validation on the 24th's data is CONCLUDED.
        Next up (Monday market hours):
        1) Watch the bot's first real restart under the new catch-up/discard logic - confirm
           no duplicate, no gap, and the catch-up bar gets a genuine touch-check
        2) If spare time (EOD today or before Monday login): revisit RELIANCE/TATAMOTORS/PNB
           specifically, otherwise let Monday's clean run be the judge
        3) Confirm VM's live.py is the fully updated version permanently
        4) Re-assess the ATR14 divergence question now that the warmup bug is fixed
        Older items still open: MA20/ATR14+touch-eval logging not yet added

P2  MemLabs regime-model — 3 methods tried, all negative on TATAMOTORS 11yr ATR%-based
        2026-07-24/25: tertile bucketing, single-feature OLS, and online-learning
        (SGDRegressor) all independently show the same thing - no persistent regime effect,
        promising-looking averages are just masking year-to-year noise in every case
        Next: (a) test across multiple stocks (single-stock signal may just be too noisy
        regardless of method), or (b) try a feature other than ATR%-based, or (c) use Grok
        CLI (~/.grok/bin/grok, confirmed available) to independently validate the trade-log
        build itself before trying more variations
        Buy MemLabs notebook ($5.50, patreon.com/cw/MemLabs) — card declined, retry

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
