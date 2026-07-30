# Session Log — 2026-07-28

## Kite bot: live-daily operation hardened, restart fix fully validated
- Morning routine: refreshed Kite access token, archived Monday's leftover top-level files
  (both VM and local - load_existing_logs() would otherwise merge them into today's run),
  confirmed local/VM scripts in sync (including yesterday's pre-open-tick fix, found by the
  user's separate phone CC session and synced back), started the bot for the day.
- Deliberately triggered 3 real mid-session restarts today (09:51, 10:14, 10:35), each with
  genuinely open positions live (up to 6 at once by the 3rd) - specifically to validate the
  weekend's catch-up/discard fix under real conditions, since Monday's uninterrupted run
  never exercised it. All 3 fully successful: excluded bucket correctly identified each time,
  catch-up fired exactly on schedule, all 30 stocks got a real touch-check via the [catch-up]
  tag (not just silent indicator seeding), existing open positions correctly re-evaluated
  with zero duplication, live tick processing resumed cleanly afterward every time. This
  closes out the last untested piece of the weekend's fix.
- Added `archive_daily_logs()`: the bot now archives its own live_trades.csv/live_bars.csv/
  warmup_bars.csv/open_positions.json into a dated 'daily data/<Nth><Month>' folder
  automatically, firing only on a genuine EOD auto-stop (not manual Ctrl+C restarts, which
  still need same-day append behavior to keep working). No more manual archiving needed
  before starting the bot each morning going forward.
- Fixed the PnL summary line, in two passes (user noticed it "wasn't showing up," then
  caught it still wasn't quite right after the first fix):
  1. It was firing after the FIRST stock's bar closed each bucket - buried at the top of a
     30-line block instead of acting as a clean bucket-complete marker. Moved to a trailing
     "===" footer that only prints once all 30 stocks (UNIVERSE) have finalized their bar
     for that bucket, tracked via a new `bucket_stocks_seen` set.
  2. The catch-up code path (a separate function, not routed through the same per-tick
     logic) never printed a summary at all - true from day one, not a regression. Added one
     call to a new shared `print_pnl_summary()` right after catch-up's loop finishes.
  3. Also fixed a naming ambiguity the user caught: "Trades" looked like it should mean
     total positions taken, but was actually just closed-trade count. Expanded to
     Trades(total=closed+open) / Closed / Open / Wins / Losses / PnL.
  All verified working correctly on real data across both live buckets and catch-up buckets.
- Moved `kbccp`/`kbss` shorthand from TODO.md's glossary into CLAUDE.md's own SHORTHAND
  section, per the user's correct observation: CLAUDE.md auto-loads into every new session's
  context automatically, TODO.md's glossary doesn't unless a session explicitly reads it.
  TODO.md now holds only terminology definitions, not action-triggering commands.

## MemLabs: direct correlation check across 6 features - single-feature linear methods now more comprehensively exhausted
- Computed the actual, direct Pearson r (not inferred from the online-learning model's noisy
  weight range, which was the earlier approach) between ATR%-rollmean40 and both PnL and
  win/loss - confirmed genuinely negligible (-0.0149, -0.0225), both deep in the "no real
  relationship" band (|r| < 0.1 threshold).
- Extended the same direct-correlation methodology to 5 more candidate features: RSI14,
  MACD% ((EMA12-EMA26)/close, a price-scale-normalized version to avoid the same "raw
  price-level" confound that would make raw EMA/HMA values spuriously correlate with PnL
  purely from 11 years of stock price drift), EMA100-relative-position, HMA100-relative-
  position (Hull MA, lower-lag alternative), and VWAP-relative-position (daily-reset VWAP,
  using DS3's volume column). Deliberately did NOT use MA20 for the "relative position"
  candidates, since the existing touch condition already requires close<MA20 at every touch
  bar by construction - that would give zero variance and a meaningless correlation.
- ALL SIX candidates showed negligible correlation (max |r| ~0.02 raw, ~0.04 when all six
  consistently 40-bar-smoothed for a fair apples-to-apples comparison, script 17 vs 16).
  This reframes the working theory: it's not "ATR% specifically lacks direction, directional
  features will work better" - none of the 6 tested features show ANY linear relationship
  with outcome, whether pure-magnitude (ATR%) or genuinely directional (RSI/MACD/MA-family/
  VWAP). Single-feature linear approaches (bucketing/OLS/online-learning) are now more
  comprehensively exhausted than the ATR%-only theory suggested.
- Traced and fully explained a real discrepancy between two correlation runs (-0.0148 vs
  -0.0401 for the identical ATR feature, script 16 vs 17) down to one single outlier trade
  (2025-10-14, pnl=17.2, ~7.4 standard deviations from typical) being included in one run but
  excluded from the other, purely because the other 5 features' smoothing needs slightly
  more warmup bars than ATR% alone needs. Confirmed via direct value diffing (bit-identical
  on the matched subset) that this was not a computation bug - just illustrates how
  sensitive/fragile a near-zero correlation reading is to single data points.
- Side investigation into the online-learning model's hyperparameters: found the model is
  capped at its eta0 step-size ceiling 96.4% of the time at eta0=0.01, meaning it barely
  behaves like genuine Passive-Aggressive learning at all (nearly identical to the old,
  already-broken constant-rate model). Swept eta0 up to 10.0 - doesn't help, ZPF stays below
  1.0 at every value, and weight-sign-flip count explodes from 10 to 1100+, confirming bigger
  steps just chase noise more aggressively rather than adapting more accurately. A joint
  epsilon x eta0 sweep's single best cell (eta0=0.05, epsilon=0.5, aggregate ZPF=1.048) still
  fails under scrutiny - 6 of 11 years below breakeven, and ZSh(D) (Zerodha daily Sharpe)
  swings wildly year to year (-7.4 to +2.4), confirming the instability at the Sharpe level
  too, not just PF/ZPF.

## Next session priorities (explicitly agreed with the user)
1. Test across multiple stocks - single-stock TATAMOTORS noise floor may simply be too high
   to see anything real, regardless of feature choice or fitting method
2. If multi-stock also shows nothing: accept single-feature linear methods are exhausted,
   consider feature combinations (not single-variable) or a genuinely non-linear approach
3. Rebuild the memory-encoding models directly against the author's actual video code
   snapshots and retest
4. Standing rule: once any ML model here is properly tested/validated, bring in Opus 5 or
   Fable 5 for an independent gap-check on the computation/code before trusting the result
