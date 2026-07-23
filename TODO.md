# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — resume tomorrow during live market hours
        2026-07-23 progress: VM timezone fixed, systemd+crash-alert (ntfy) built+tested,
        position-recovery+gap-check built+validated on real trades, EOD exit validated,
        new trade_check.py script built for custom-window trade validation
        Next up:
        1) Investigate the ATR14 divergence properly - live's real SL/TP (built from its own
           tick-based bars) vs a pure-official-data replay's SL/TP disagree because ATR is
           sensitive to high/low (unlike MA20 which is close-only and matches well). Decide
           if/how to reconcile this for trade-level validation to be meaningful
        2) Only 2/17 trades matched exactly across the 3 checked windows today - dig into the
           remaining unexplained ones (6 unexplained "only in live", AXISBANK/HINDALCO "only
           in official") once ATR question above is resolved
        3) Port today's position-recovery/gap-check fix to VM's live.py permanently (already
           pushed once for testing - confirm it's the version staying there)
        4) Sync VM's live_trades.csv loss issue - old trades get silently dropped once a new
           run's first save overwrites the file (the `if trades:` guard never merges old data)
        Older items still open: reconcile script's fetch-window bug (misses EOD exits),
        MA20/ATR14+touch-eval logging not yet added, SUNPHARMA reconstruction mismatch (local,
        pre-VM) — likely superseded by today's live SUNPHARMA validation, re-check relevance

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
