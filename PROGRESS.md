# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every SS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. MemLabs: computed direct Pearson r (not inferred from model weights) between ATR%-rollmean40 and PnL/win-loss — confirmed genuinely negligible (-0.015/-0.022). Extended to 5 more candidates (RSI14, MACD%, EMA100/HMA100/VWAP-relative-position) — ALL six showed negligible correlation too, whether raw or consistently 40-bar-smoothed. This is a stronger finding than the earlier "ATR% lacks direction" theory: no single-feature linear relationship exists at all for this strategy on TATAMOTORS, magnitude-only or genuinely directional. Also traced (and resolved) a real discrepancy between two correlation runs down to a single 7.4-std-dev outlier trade being included/excluded by differing warmup requirements — confirmed no computation bug, and illustrated how fragile near-zero correlations are to single data points
2. Kite bot: deliberately tested 3 real mid-session restarts today (09:51, 10:14, 10:35) with open positions live — all successful, validating the weekend's catch-up/discard fix under real conditions (not just morning startup). Fixed the PnL summary line: moved from firing after the first stock per bucket (buried at the top) to a trailing footer after all 30 stocks, added a missing summary call for catch-up buckets (never had one), and expanded fields to Trades(total)/Closed/Open/Wins/Losses/PnL
3. Added `archive_daily_logs()`: bot now auto-archives its own daily CSVs into a dated folder on a genuine EOD auto-stop — no more manual archiving needed before each morning's restart
4. Moved `kbccp`/`kbss` shorthand from TODO.md into CLAUDE.md itself — CLAUDE.md auto-loads every session, TODO.md's glossary doesn't unless explicitly read; TODO.md now holds terminology only, not action-triggering commands
5. Reconciled 24th July end-to-end: stitched the day's 2 real runs into 39 trades, fixed a recon-script-only off-by-one (session_end excluded the EOD bar via `>=`, now `>` + fetch buffer) — applied to the real reconcile script too. Confirmed the 09:15 login-warmup mess and 13:05 skipped-bucket as real; most trade mismatches explained as ordinary tick-vs-official noise

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. MemLabs regime-model tested three independent ways (static tertile bucketing, single-feature OLS regression, online-learning SGDRegressor) on TATAMOTORS 11yr DS3 — all three reach the same honest negative verdict: no persistent, tradeable regime effect from ATR%-based features alone (2026-07-24/25)
