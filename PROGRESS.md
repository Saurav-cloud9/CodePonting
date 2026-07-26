# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Reconciled 24th July end-to-end: stitched the day's 2 real runs (pre/post the 13:05 restart) into 39 trades, fixed a recon-script-only off-by-one (session_end excluded the EOD bar via `>=`, now `>` + fetch buffer), and ran full bar+trade level recon — confirmed the 09:15 login-warmup mess and 13:05 skipped-bucket as real, explained most of the 17 trade mismatches as ordinary tick-vs-official noise; RELIANCE/TATAMOTORS/PNB flagged as genuine no-nearby-match exceptions, parked (not chased against already-fixed bugs) pending tomorrow's clean live run as the real judge
2. Reverted temporary EOD_HOUR=16 test config back to 15 (local + VM) — clean for the next real trading day
3. Refined the warmup-boundary fix further: the currently-forming bucket at connect time now gets a proper touch-check too (not just silently seeded) — a scheduled one-shot `catchup_current_bucket()` fires exactly when that bucket genuinely closes, fetches it, and runs it through the full signal logic; `on_ticks()` discards any tick belonging to that bucket or older so live bar-building only ever starts on a clean, complete boundary
4. Fixed the live_trades.csv/live_bars.csv data-loss bug: bot now loads any existing CSV data into memory at startup (`load_existing_logs()`) before the periodic save cycle begins, so old trades/bars survive a restart instead of being silently overwritten — verified via simulation
5. MemLabs: extended the online-learning (SGDRegressor) test with a year-wise breakdown — same negative verdict as the static bucketing: the promising-looking overall filtered result (N=479, ZPF=1.01) doesn't hold up year by year (6 pass, 4 fail, 1 borderline), and the model's filter drifts toward "always take" over time rather than staying selectively adaptive

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. MemLabs regime-model tested three independent ways (static tertile bucketing, single-feature OLS regression, online-learning SGDRegressor) on TATAMOTORS 11yr DS3 — all three reach the same honest negative verdict: no persistent, tradeable regime effect from ATR%-based features alone (2026-07-24/25)
