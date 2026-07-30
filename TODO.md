# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# ─────────────────────────────────────────────────────────────

P1  Kite bot (market hours only) — running live daily, resume next market session
        2026-07-28 progress: 3 real mid-session restarts today (09:51/10:14/10:35) with open
        positions live - all successful, fully validates the weekend's catch-up/discard fix
        under real conditions (not just morning startup). archive_daily_logs() added - bot
        now auto-archives its own CSVs on EOD, no more manual archiving each morning. PnL
        summary fixed: trailing footer after all 30 stocks (was buried at top after just the
        first), catch-up buckets now get a summary too (never had one before), fields
        expanded to Trades(total)/Closed/Open/Wins/Losses/PnL. kbccp/kbss moved into
        CLAUDE.md itself (auto-loads every session, TODO.md glossary doesn't).
        Next up: continue watching daily runs; re-assess ATR14 divergence question;
        revisit RELIANCE/TATAMOTORS/PNB from 24th July recon only if spare time
        Older items still open: MA20/ATR14+touch-eval logging not yet added

P2  MemLabs regime-model — single-feature linear approaches now exhausted (6 features tested)
        2026-07-28: computed DIRECT Pearson r (not inferred) for ATR%-rollmean40 vs PnL/win-
        loss - confirmed negligible (-0.015/-0.022). Extended to 5 more candidates (RSI14,
        MACD%, EMA100/HMA100/VWAP-relative-position) - ALL SIX show negligible correlation,
        raw or 40-bar-smoothed. This is a stronger finding than "ATR% lacks direction" -
        NO single-feature linear relationship exists at all for this strategy on TATAMOTORS,
        magnitude-only or genuinely directional. Also confirmed eta0 sweep (0.01-10.0) and a
        joint epsilon x eta0 sweep don't rescue the online-learning model either - every
        cell's ZPF stays at or below ~1.0, and the "best" cell's year-wise breakdown still
        shows 6 of 11 years failing badly. ZSh(D) confirms the same instability at the
        Sharpe level (year-wise swings from -7.4 to +2.4).
        Next (agreed):
        1) Test across multiple stocks (single-stock TATAMOTORS noise floor may be too high
           to see anything real, regardless of feature or method)
        2) If multi-stock also shows nothing: accept single-feature linear methods are
           exhausted, consider feature COMBINATIONS or a genuinely non-linear approach
        3) Rebuild the memory-encoding models directly against the author's video code
           snapshots and retest
        Standing rule: once any ML model here is properly tested/validated, bring in
        Opus 5/Fable 5 for an independent gap-check on our computation/code before trusting
        the result
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

# Note: kbccp/kbss (kite bot scoped CCP/SS) moved to CLAUDE.md SHORTHAND section -
# action-triggering shorthand lives there (auto-loaded every session), not here.
