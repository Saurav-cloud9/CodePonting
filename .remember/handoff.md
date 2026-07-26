# Handoff Note — 2026-07-26

## Current State — Kite paper trading bot (Algo_Trading/kite_oracle_papertrading/)
- **EOD_HOUR reverted to 15** (both local + VM) - Friday's temporary 16-for-testing value is
  gone, config is clean for the next real trading day
- **Warmup-boundary fix now COMPLETE** (was only partially done Friday): the bucket that's
  still forming at connect time is no longer silently seeded OR duplicated - `on_ticks()`
  discards any tick belonging to it, and a scheduled one-shot `catchup_current_bucket()`
  (via `threading.Timer`, fires 5 min after connect-time) fetches that bucket once it's
  genuinely closed and runs it through the FULL `process_bar()` - giving it a real
  touch-check, not just an indicator contribution. Implemented in
  ma_30_rejection_v1_live.py, syntax-verified, pushed to VM. **NOT yet tested live** -
  market was closed all weekend (Sat/Sun) - first real test is Monday.
- **live_trades.csv/live_bars.csv data-loss bug fixed**: `load_existing_logs()` now runs at
  startup, loading any existing CSV data into memory before the periodic save cycle begins -
  old trades survive a restart instead of being silently overwritten. Verified via
  standalone simulation, pushed to VM.
- Neither fix has real market data behind it yet - Monday's first live run is the actual
  validation for both.

## Current State — MemLabs regime-model thread
- **All three approaches now tested, all three negative**: static tertile bucketing (Fri),
  single-feature OLS regression (Fri/Sat), and online-learning SGDRegressor with year-wise
  breakdown (Sat) - every method shows the same thing: no persistent, tradeable regime
  effect from ATR%-based features (raw or memory-encoded) on TATAMOTORS across 11 years.
  Promising-looking overall averages in every case turned out to be masking real
  year-to-year instability, not reflecting a stable pattern.
- All work (scripts 01-13, output CSVs/PNGs) confirmed committed + pushed to git
  (origin/main), so it's pullable from the laptop too.
- Grok CLI (~/.grok/bin/grok) confirmed available and cost isn't a concern - still not
  actually used yet for independent validation, worth doing before trying more variations
- MemLabs notebook purchase still blocked on a declined card

## Current State — New: VM backtesting environment + VS Code Remote-SSH (side quest, done)
- `~/backtesting/` fully set up on the VM: own venv (`backtest_env`), scoped CLAUDE.md +
  PROGRESS.md (deliberately NOT a full `.remember/` system - overkill for this scope),
  backtesting_rules/ copied in with a hard "always read+follow it" rule, 2 reference
  scripts, and the full DS3 dataset (160MB) copied in. Fully independent from
  kite_oracle_papertrading/ - hard rule in its CLAUDE.md never to touch that folder unless
  explicitly asked.
- VS Code Remote-SSH now works end-to-end (`oracle-vm` host configured on the Windows side,
  key permissions fixed via icacls) - direct live file browsing/editing on the VM without
  manual scp round-trips, usable alongside this chat session for command execution.
- Deliberate decision: VM stays as plain folders, NOT a git repo - CodePonting (desktop)
  remains the single source of truth (local + GitHub); avoids needing to manage secrets/.env
  and noisy data-file diffs in a VM-side git history.

## Next Step (START HERE) - all explicitly agreed with the user

### Kite bot thread (P1) - Monday market hours
1. Watch the bot's first real restart under the new catch-up/discard logic - confirm no
   duplicate, no gap, catch-up bar gets a genuine touch-check
2. Review 24th July's PnL logs + validate against recon:
   (a) quantify how many of the 24th's trades were actually affected by the stale-tick
       duplicate bug found that day
   (b) consolidate the day's fragmented iteration snapshots (multiple restarts for testing)
       into one clean, complete day-level picture
   (c) remember: today's 2 new fixes can't be validated against the 24th's old data - only
       Monday's fresh run actually tests them
3. Confirm VM's live.py is the fully updated version, staying there permanently
4. Re-assess the ATR14 divergence question now that the warmup bug is properly fixed
5. Older items: reconcile script's fetch-window bug, MA20/ATR14+touch-eval logging

### MemLabs thread (P2) - after the above
1. Test across multiple stocks (single-stock signal may just be too noisy regardless of
   method) OR try a feature other than ATR%-based
2. Use Grok CLI to independently validate the trade-log build before trying more variations
3. Buy MemLabs notebook (card declined, retry)

## Known Issues
- Kite bot: today's 2 fixes are implemented but UNTESTED against real market data
- Kite bot: ATR14 divergence question needs re-assessment post-warmup-fix
- Kite bot: reconcile script's fetch-window bug (misses EOD trades), MA20/ATR14+touch-eval
  logging not yet added
- MemLabs: no persistent regime effect found across 3 methods on ATR%-based features alone -
  real negative result, informs next steps (multi-stock or different feature)
- MemLabs notebook purchase blocked on a declined card
- Old baseline sweep scripts still use monthly Sharpe - not ZSh(D)-compliant
