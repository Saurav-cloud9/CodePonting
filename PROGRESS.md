# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Parity-checked monthly_reconciliation.py's 6 new replay engines against DS3 (trade-by-
   trade diff on August 2026) — found and fixed 2 real bugs: one-bar-stale MA20/ATR14 (all
   3 new engines) and indicators skipped during position-guard skip-ahead (2 of 3). All 6
   variants now show 99.6-100% parity with DS3. Pre-fix August numbers for 5 of 6 variants
   were wrong and are superseded — this validates the deploy this whole thread built toward.
2. Added 95% CI columns (ci_low_capm/ci_high_capm) to the monthly report — distinguishes
   "confidently near-zero" from "inconclusive" from "confidently not-zero," information the
   p-value alone doesn't carry. Found ma_long_flip_v0 (p=0.061) is genuinely inconclusive
   (wide CI), not "confidently zero" — same fragility class as 6bce_v0.
3. Cleanup: removed dead pcap_lookup code, sl_tp separator changed to "x" (Excel date-
   parsing risk), locked n=days/n_trades=trade-count naming convention (TODO.md GLOSSARY).
4. All 6 strategies/ variants locked: ma_short_v1/v2vwap (SL=4.5/TP=3.0), 6bce_v0
   (SL=8.0/TP=3.0), 6bce_v1vwap (SL=4.5/TP=3.0), ma_long_flip_v0 (SL=7.0/TP=3.0),
   ma_long_flip_vwap (SL=4.0/TP=3.0) — each with an sl_sweet_spot.md recording its sweep.
5. Archived 4 redundant folders into strategies/_archive_pre_strategies_consolidation/ via
   git mv (history preserved). CLAUDE.md: pcap/tcap flagged as display-only, never for
   computation without explicit direction.

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. All 6 strategies/ variants locked + deployed into monthly_reconciliation.py on the live
   bot VM (2026-09-05) — replaces the old debunked raw-ZPF variant list with rigorously
   validated SL/TP combos, correct raw-₹ alpha methodology, and dual NIFTY/basket benchmarks
