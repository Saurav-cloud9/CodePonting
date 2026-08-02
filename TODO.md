# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  MemLabs autoregressive model — resume from here (diverted into ATR exploration, now closed)
        2026-07-31: built genuinely autoregressive model (x=prev trade PnL, y=current trade
        PnL) matching author's actual technique. Real, if modest, OOS edge at live SL/TP
        2.0/4.5 (ZPnL -79.18 -> -50.41), but nearly vanishes at sweep's "best" 6.0/6.0 combo
        (ZPnL -66.60 -> -63.53) - wider SL/TP dilutes trade adjacency the signal likely
        depends on (holding +81%, gaps +30%). Real tradeoff to keep in mind.
        Next: multi-stock test (single-stock TATAMOTORS noise floor may be too high to see
        anything real, same open question as before the ATR detour)

P2  ATR formula exploration — CLOSED, informed P1's SL/TP tradeoff finding
        2026-07-31: 12 variants (Simple/Wilder x 10/14/20 x Signal/Entry) via Grok, validated.
        ZPF spans only 0.760-0.767; current live formula (Simple14/Signal) already best of 12.
        Not a lever that fixes viability. If spare time: full 90-combo SL/TP sweep x 6 ATR
        variants via Grok (nice-to-have, not priority).

P3  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix.
        archive_daily_logs() added, PnL summary fixed (trailing footer + catch-up coverage).
        2026-07-31: Saurav validating 31st July live trades + full 27-31 July weekly recon
        with VM CC directly (not this session) - process-development practice, known low edge.
        Older items still open: MA20/ATR14+touch-eval logging not yet added; ATR14 divergence
        question; RELIANCE/TATAMOTORS/PNB from 24th July recon (spare time only)

P4  New signal sweeps via Grok — ongoing, lower priority until ML thread resolved
        VWAP done (both baseline + VWAP variant confirmed dead); next: RSI/MACD combos

P5  Build cloud backtesting engine for paper trading
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
# SL/TP       — Stop Loss / Take Profit (standard shortform). Retroactively renamed
#               from SL/TGT across ~130 files project-wide on 2026-07-31 (excluded:
#               kite_oracle_papertrading/, .claude/worktrees/, PROGRESS_HISTORY.md)
# PF          — raw profit factor (Python backtest, zero charges)
# ZPF         — Zerodha Profit Factor: PF after full Zerodha intraday charges
# ZSh(D)      — Zerodha Daily Sharpe (annualised): daily zpnl mean/std × √252
# NPF         — Neo Profit Factor (Kotak Neo, archived — Zerodha is now primary)
# WR          — win rate
# WFA         — walk-forward analysis
# OOS         — out-of-sample
# SL          — stop loss (replaces old "SL" in SL/TP — industry standard)
# TP          — take profit (replaces TP — industry standard)
# R/R         — reward/risk ratio
# BE          — breakeven W/(W+L) = SL/(SL+TP)
# MFE         — Max Favourable Excursion (best point trade reached, in ATR units)
# MAE         — Max Adverse Excursion (worst point trade reached, in ATR units)

## Frameworks & Data
# fv2         — Framework V2 (active)
# DS3         — primary historical dataset (30 stocks, 2015-2025, 5-min parquet)

# Note: kbccp/kbss (kite bot scoped CCP/SS) moved to CLAUDE.md SHORTHAND section -
# action-triggering shorthand lives there (auto-loaded every session), not here.
