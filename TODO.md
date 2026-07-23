# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — resume during tomorrow's login
        VM deployment achieved 2026-07-22: WSL/Ubuntu + SSH to Oracle VM working, venv +
        deps installed, live bot files copied, rate-limit bug found+fixed (batched ltp call
        + warm-up delay)
        Two NEW unresolved VM-specific bugs (top priority next session):
        1) VM system timezone is UTC not IST -> bar timestamps + EOD_HOUR check both wrong
           in real-world terms. Fix known: sudo timedatectl set-timezone Asia/Kolkata (VM)
        2) Bot process silently exited on VM after ~2 bar cycles, no crash seen yet - check
           original launch terminal's final output to diagnose before trusting unattended runs
        After those: re-run full-day VM test -> recon script against VM's live_bars.csv
        Older items still open: reconcile script's fetch-window bug (misses EOD exits, fix
        by extending to session_end inclusive), MA20/ATR14+touch-eval logging not yet added,
        SUNPHARMA reconstruction mismatch unresolved (needs live-captured warm-up data)

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
