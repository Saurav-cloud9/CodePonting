# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Live-validated every signal fired on the VM today (09:15 market open onward) against official Kite historical_data one by one — touch/entry/exit all independently confirmed correct for the underlying signal logic itself
2. Found a real bug during validation: warmup() could double-count a bar into the MA20/ATR14 rolling window (once from historical_data at boot, once from the live tick engine rebuilding the same period) — root-caused precisely (historical_data can return a still-forming candle), fixed by excluding the currently-forming bucket from warmup and letting live ticks own it exclusively; verified via manual deque reconstruction that this explained 3 real touch-signal discrepancies
3. Applied + tested the fix live via a precisely-timed restart at a bucket boundary — confirmed no duplicate this time, but surfaced a second, related edge case: the first tick after a fresh WebSocket subscribe can carry a stale/cached timestamp (from before the reconnect gap), recreating the same duplicate-bucket problem through a different mechanism (affected 9/30 stocks on one restart)
4. Scoped the fix for the stale-first-tick case (discard any first tick per symbol whose bucket is older than what warmup already covered) — not yet implemented, next session
5. Added a once-per-5-min-cycle PnL/trade summary line to the live bot's console output (total trades, open positions, wins, losses, running PnL) — tested via simulation before deploying, confirmed prints once per bar cycle not per stock

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), plus crash-safe position recovery with historical gap-check — all tested and confirmed working on real market data (2026-07-23)
5. MemLabs regime-model concept (rolling-mean memory encoding) tested for real on TATAMOTORS 11yr DS3 — honest negative result: no persistent regime effect found from ATR%-based memory encoding alone, ruling out the simplest version of the approach (2026-07-24)
