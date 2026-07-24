# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — resume during live market hours
        2026-07-24 progress: found+fixed the warmup duplicate-bar bug (explained most of
        yesterday's trade mismatches - real root cause, not just tick-vs-official noise),
        added PnL summary line, temporarily bumped EOD_HOUR to 16 for testing (REVERT TO 15
        before next real trading day)
        Next up (highest priority - do FIRST next session):
        0) REVERT EOD_HOUR back to 15 in ma_rejection_v1_core.py + push to VM (currently 16
           for testing purposes only)
        1) Implement the stale-first-tick fix: in on_ticks(), when starting a new forming_bar
           for a symbol, discard the tick if its bucket is older than current_bucket (computed
           at warmup) - closes the reconnect-stale-timestamp duplicate case found today
        2) Yesterday's ATR14 divergence question (live tick-bar ATR vs pure-official-replay
           ATR) - now partially explained by the warmup duplicate bug found today; re-assess
           whether it's still a separate issue once the two fixes above are in place
        3) Port both of today's warmup fixes to be the permanent VM version (already pushed
           for testing - confirm staying there after revert)
        4) Fix VM's live_trades.csv loss issue - old trades silently dropped on restart
        Older items still open: reconcile script's fetch-window bug (misses EOD exits),
        MA20/ATR14+touch-eval logging not yet added

P2  MemLabs regime-model — memory encoding tested, negative result on TATAMOTORS 11yr
        2026-07-24: built full pipeline (Framework_V2/scripts/trials/regime_model/memlabs/),
        rolling-40-mean ATR% feature bucketed vs raw ATR% - neither shows a persistent
        regime effect across 2015-2025 (year-wise breakdown is just noise, no bucket wins
        consistently). Single-year (2023) "strong" results didn't replicate - overfitting.
        Next: either (a) fit the actual OLS regression (w/b/y_hat/sign, not yet done - only
        bucketing was tried) on the full 11yr data as a more rigorous test before giving up,
        or (b) test across multiple stocks (single-stock signal may just be too noisy
        regardless of feature), or (c) try a different feature entirely (not ATR%-based)
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
