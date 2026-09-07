# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. SMC Liquidity concept fully tested — recovered prior concepts/results from a bookmarked
   claude.ai session into smc/, then built + ran a fresh 4-variant matrix ({swing low,swing
   high} x {long,short}) against DS3. ALL 4 RULED OUT. The 2 that cleared soft-triage (V1
   contrarian-short, V2 true-mirror-short) both show confidently, decisively NEGATIVE alpha
   (p<0.001, CIs entirely clear of zero) — a real negative edge, not just absence of one,
   same pattern as the flagship family. Full detail: smc/04_liquidity_findings.md.
2. Confirmed a real structural parallel to the flagship's ma_short/ma_long_flip touch/flip
   pattern: Liquidity's V1 (contrarian short on the bullish-looking swing-low setup) is the
   strongest of its 4 variants, mirroring exactly why ma_long_flip was the one flagship
   variant that got locked.
3. Lowered backtesting_rules.md §12's "ruled out" gate 0.85→0.75, reframed as a soft
   pre-triage check rather than a final verdict — found the old 0.85 would have wrongly
   killed 3 of the 6 currently-locked flagship variants at their own raw-round stage.
4. Parity-checked monthly_reconciliation.py's 6 replay engines against DS3, fixed 2 real
   bugs (one-bar-stale indicators; indicators skipped during position-guard skip-ahead) —
   now 99.6-100% parity. Added 95% CI columns to the report (confidently-zero vs
   inconclusive vs confidently-not-zero — info the p-value alone doesn't carry).
5. All 6 flagship strategies/ variants remain locked (ma_short_v1/v2vwap, 6bce_v0/v1vwap,
   ma_long_flip_v0/vwap), each with an sl_sweet_spot.md recording its sweep — unchanged
   this session, referenced throughout as the comparison baseline for SMC work.

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. All 6 strategies/ variants locked + deployed into monthly_reconciliation.py on the live
   bot VM (2026-09-05) — replaces the old debunked raw-ZPF variant list with rigorously
   validated SL/TP combos, correct raw-₹ alpha methodology, and dual NIFTY/basket benchmarks
