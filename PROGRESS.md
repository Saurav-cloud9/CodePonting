# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Found + fixed root cause of live tick bucketing bug: MODE_QUOTE never provides exchange_timestamp, so ticks were bucketed by local datetime.now() instead of real exchange time — switched to MODE_FULL
2. Confirmed EOD-hour tick-based exit + new hard auto-stop feature working live at both a temporary 14:00 test cutoff and the real 15:00 cutoff (2026-07-21)
3. Reconciliation script: fixed to save findings+official bars to data/recon/; found a real bug (fetch window excludes the EOD-triggering bar, so it can never record EOD-based trades)
4. Traced 3-vs-0 live/recon trade mismatch to two distinct causes: the fetch-window bug above, and the startup-corrupted first bar affecting actual signal detection (not just cosmetic OHLC) — confirmed for JSWSTEEL, partially traced for INFY/SUNPHARMA
5. Added warmup_bars.csv logging to live script so future analysis doesn't need error-prone after-the-fact warm-up reconstruction; TODO.md reprioritized, Kite bot now P1

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle: connect → warm-up → trade → EOD tick-exit → auto-stop (2026-07-21, verified at real market close)
4. Kite paper-trading bot architecture established: shared core logic + offline engine + live engine + reconciliation script (Algo_Trading/kite_oracle_papertrading/)
5. LONG confirmed dead (PF<1.0 across all 90 combos, baseline and v1); SHORT is the only viable direction
