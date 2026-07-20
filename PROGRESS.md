# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Shared core logic extracted (ma_rejection_v1_core.py); offline engine refactored to use it
2. Live KiteTicker-based engine built (ma_30_rejection_v1_live.py) — tick-built bars, tick-based SL/TP exits
3. First live connection test run during market hours (2026-07-20): auth, warm-up, ticks, bar-building, signal detection all confirmed working on real data
4. Two real bugs found + fixed live: CSV PermissionError crash (file locked by Excel), EOD-hour exit delayed ~5min (was bar-close-based, now tick-based like SL/TP)
5. Reconciliation script built + first real run: 270/270 bars matched in count but 48 (17.8%) had real OHLC diffs (up to ₹4.50, bigger than DS3's float-tie-break scale); trades 13 live vs 11 official-replay, 7 matched — root causes hypothesized (mid-bucket startup, ticks as periodic snapshots), not yet fully confirmed

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired (DABUR/WIPRO/JSWSTEEL), first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Kite paper-trading bot architecture established: shared core logic + offline engine + live engine + reconciliation script (Algo_Trading/kite_oracle_papertrading/)
4. LONG confirmed dead (PF<1.0 across all 90 combos, baseline and v1); SHORT is the only viable direction
5. TATAMOTORS→TMPV corporate action resolved; DS3 dataset confirmed unaffected
