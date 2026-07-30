# Handoff Note — 2026-07-28

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- Running live, healthy. Today's weekend-fix restart validation is DONE: 3 real mid-session
  restarts (09:51/10:14/10:35) with open positions, all clean - catch-up/discard fix fully
  proven under real conditions, not just morning startup. Nothing left untested there.
- archive_daily_logs() now auto-archives the day's CSVs on EOD auto-stop - no more manual
  archiving needed before tomorrow's start.
- PnL summary line fixed (was buried at top of each bucket + catch-up never had one at all +
  "Trades" field was ambiguous) - now a clean trailing footer with
  Trades(total)/Closed/Open/Wins/Losses/PnL, verified on both live and catch-up buckets.
- kbccp/kbss shorthand now live in CLAUDE.md's SHORTHAND section (moved from TODO.md, which
  doesn't auto-load) - use these directly to scope to just the bot instead of full SS/CCP.
- Next session (market hours): just the routine morning start (refresh token, check for
  scripts still in sync, start bot) - no more manual archiving step needed now.
- Still open: re-assess ATR14 divergence question; RELIANCE/TATAMOTORS/PNB from 24th July
  recon only if spare time (not priority); MA20/ATR14+touch-eval logging not yet added.

## Current State — MemLabs regime-model thread
- Single-feature linear methods are now MORE comprehensively exhausted than before. Computed
  DIRECT Pearson r (not inferred) for 6 candidate features against TATAMOTORS 11yr PnL/win-
  loss: ATR%-rollmean40, RSI14, MACD%, EMA100-rel-pos, HMA100-rel-pos, VWAP-rel-pos. ALL SIX
  show negligible correlation (max |r| ~0.02-0.04), raw or 40-bar-smoothed. This kills the
  earlier "ATR% specifically lacks direction" theory in favor of a broader one: no single
  linear feature at all relates to this strategy's outcome on this stock.
- Scripts: 16 (unsmoothed, all 6 features) and 17 (all 6 consistently 40-bar-smoothed) in
  Framework_V2/scripts/trials/regime_model/memlabs/. Both confirm the same verdict.
- Side finding: online-learning's eta0 is capped 96.4% of the time at 0.01 (barely PA1 at
  all in practice). Swept eta0 to 10.0 and jointly with epsilon - nothing rescues it, best
  cell still fails year-wise (6/11 years) and at the Sharpe level (ZSh(D) swings -7.4 to
  +2.4). This closes the hyperparameter-tuning avenue for the online-learning model entirely.

## Next Step (START HERE) - explicitly agreed with the user

### Kite bot thread (P1)
1. Routine morning start only - no manual archiving needed anymore
2. Re-assess ATR14 divergence question now the warmup bug is fully proven fixed
3. RELIANCE/TATAMOTORS/PNB from 24th July recon - only if genuinely spare time

### MemLabs thread (P2) - in this order
1. Test across multiple stocks - single-stock TATAMOTORS noise floor may be too high to see
   anything real regardless of feature/method (this is the natural next step given 6/6
   single features on one stock all failed identically)
2. If multi-stock also shows nothing: accept single-feature linear methods are exhausted,
   move to feature COMBINATIONS or a genuinely non-linear approach
3. Rebuild the memory-encoding models directly against the author's actual video code
   snapshots and retest
4. Standing rule: once any model is properly validated, bring in Opus 5/Fable 5 for an
   independent gap-check before trusting the result

## Known Issues
- Kite bot: ATR14 divergence question needs re-assessment post-warmup-fix
- Kite bot: MA20/ATR14+touch-eval logging still not added
- MemLabs: no single-feature linear relationship found across 6 features x 2 smoothing
  variants x 3 fitting methods (bucketing/OLS/online-learning) on TATAMOTORS alone - strong,
  well-substantiated negative result; multi-stock test is the natural next real question
- MemLabs notebook purchase blocked on a declined card
- Old baseline sweep scripts still use monthly Sharpe - not ZSh(D)-compliant
