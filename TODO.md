# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  MemLabs Pearson's r feature screening — resume from here (notebook 35)
        2026-08-06: Train-only r/p screening vs fixed target close_log_return, benchmarked
        against Model A's own lag_1 (always non-significant). RSI(14, lagged) tested: NIFTY50
        not significant, TATAMOTORS r=0.0548/p=0.012 significant but r^2~=0.3%, still very weak.
        Next: screen more candidates (volume on TATAMOTORS - NIFTY50's own volume is confirmed
        meaningless; gap-size vs intraday-move target; other RSI periods). Only escalate to a
        full Model A/B build + WFA once something meaningfully stronger than RSI turns up.

P2  NIFTY50-as-shared-gate hypothesis — CLOSED, debunked via full WFA
        2026-08-06: built + validated end-to-end (notebook 31, scripts 25-29/32/33). Full WFA
        (9-fold + 4-fold rolling, via Grok) - every fold net-negative in pooled money terms.
        Top single-split "winners" traced to one dominant event (2024-06-04 crash) + Train/Test
        boundary sensitivity, not real edge. Writeup: 34_updated_validation_summary.md.
        Established reusable methodology: pooled (not mean-of-ratios) ZPF, rolling (not
        expanding) WFA windows - apply to any future multi-bucket validation.

P3  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix.
        Saurav validating live trades + weekly recon with VM CC directly (not this session).
        Older items still open: MA20/ATR14+touch-eval logging not yet added; ATR14 divergence
        question.

P4  ATR formula exploration - CLOSED. If spare time only: full 90-combo SL/TP sweep x 6 ATR
        variants via Grok (nice-to-have, not priority, carried over unchanged).

P5  August 2026 DS3 gap-fill — once the month closes, same CCG pattern as the July fill just
        completed (all 30 stocks + NIFTY50 daily).

# ── PARKED / FUTURE ───────────────────────────────────────────
F1  Single-stock trade dump (TATAMOTORS) — verify SHORT calculations
F2  Nifty Futures — Beluga signal on Nifty (post HMA Bounce investigation)
F3  Volume Spike Exhaustion — hypothesis parked
F4  Stock diversity analysis — check if 5 stocks fire on same days
F5  Portfolio construction — capital allocation across stocks
F6  Insurance review
F7  New signal sweeps via Grok — VWAP done (confirmed dead); RSI/MACD combos not yet run
F8  Cloud backtesting engine — run fv2 backtests from any device without local setup
        (Primary: Oracle Cloud; fallback: AWS EC2)

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
# DS3         — primary historical dataset (30 stocks, 2015-02 to 2026-07, 5-min parquet,
#               Framework_V2 copy is primary as of 2026-08-06 - has ma20/atr14 precomputed)

# Note: kbccp/kbss (kite bot scoped CCP/SS) moved to CLAUDE.md SHORTHAND section -
# action-triggering shorthand lives there (auto-loaded every session), not here.
