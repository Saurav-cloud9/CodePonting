# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Created strategies/flagship/ (SMC-style numbered flat-file convention), seeded with
   copies of all 6 locked flagship variants (indices 02-07, originals untouched) + new
   canonical naming: the tested 6bce family is now labeled 6BCEH (High-triggered) to
   disambiguate from its untested 6BCEL (Low-triggered) sibling. Fixed the FRESH_6BCE_*
   labels to FRESH_6BCEHSHORT_* across all smc/ master + flagship_fullds3 CSVs.
2. Built + ran the 3 remaining 6-Bar-Close-Extreme variants (indices 08-10):
   6BCEL-Short, 6BCEH-Long, 6BCEL-Long. ALL 3 RULED OUT — same decisive-negative-alpha
   pattern as Liquidity V0-V3 (CIs entirely clear of zero). Notably, the priority-#1
   hypothesis (6BCEL-Short benefiting from the project's structural short-bias finding)
   did NOT pan out — confirms the short-bias finding doesn't generalize to "any short
   entry works." Only the originally-locked 6BCEH-Short clears the bar in this family.
   Full detail + CAPM rows: flagship/01_plan.md, flagship/master_nifty.csv & basket.csv.
3. SMC Liquidity concept fully tested — recovered prior concepts/results from a bookmarked
   claude.ai session into smc/, then built + ran a fresh 4-variant matrix ({swing low,swing
   high} x {long,short}) against DS3. ALL 4 RULED OUT, same negative-alpha pattern. Full
   detail: smc/04_liquidity_findings.md.
4. Lowered backtesting_rules.md §12's "ruled out" gate 0.85→0.75→then removed entirely
   (replaced with: compute Table 2/3 + alpha for every combo regardless of raw-round ZPF,
   no RULED_OUT placeholders) — found the old gates would have wrongly excluded real,
   already-locked flagship variants.
5. Parity-checked monthly_reconciliation.py's 6 replay engines against DS3, fixed 2 real
   bugs (one-bar-stale indicators; indicators skipped during position-guard skip-ahead) —
   now 99.6-100% parity. Added 95% CI columns to the report.

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. All 6 strategies/ variants locked + deployed into monthly_reconciliation.py on the live
   bot VM (2026-09-05) — replaces the old debunked raw-ZPF variant list with rigorously
   validated SL/TP combos, correct raw-₹ alpha methodology, and dual NIFTY/basket benchmarks
