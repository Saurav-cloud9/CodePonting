# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. memlabs #54: the dispersion regime-filter lead is RULED OUT. Built
   `54c_oos_dispersion_gate.py` — chronological 70/30 OOS test of the lagged-dispersion
   Q5 threshold gate (Fable's "first ZPF>1.0 slice" finding). Own-period quintile tables
   show the pattern doesn't hold: TRAIN's real best bucket is Q4 (1.157), not Q5 (0.994,
   flat); TEST period shows every quintile under 1.0, with Q5 (highest dispersion) one of
   the WORST buckets (0.813) — a full reversal. No 54d build off this pair.
2. Built `54c_10feature_screen.py` — full 10-candidate r-vs-daily_zpnl comparison (the
   notebook's §3 combined-null only ever corrected for 2 of the 10 built candidates).
   Surprise: `gap_pct` (r=-0.0625) edges out dispersion (0.0573) as the single strongest
   of all 10 — previously unscreened. Under max-of-10 iid null, both still clear 95th,
   neither clears 99th — the under-correction concern didn't flip the verdict, but this
   hasn't yet been combined with the circular-shift fix (stricter still, not yet run).
3. Verified (independently reproduced) Fable's two `#54` findings from last session: (a)
   the notebook's iid-shuffle null was too lenient for an autocorrelated feature like
   dispersion (acf1=0.417) — a circular-shift null is the correct primary, under which
   dispersion clears 95th not 99th; (b) the Q5 quintile slice was in-sample, now shown
   above to fail OOS. `54c_screen.ipynb` itself NOT yet updated with either correction —
   precise resume point written into `54_...baseline.md` §3 "RESUME HERE".
4. Long stats-literacy Q&A (not yet action items): ACF1 vs r as separate necessary-vs-
   sufficient properties (verified numerically: NIFTY daily return acf1=-0.025 vs its own
   10-day trend acf1=0.905 — same data, mechanical-overlap artifact confirmed); multiple-
   testing correction via coin-flip analogy; weak-form efficiency scopes to directional/
   first-moment features only (trend) — NOT to magnitude/second-moment ones (dispersion,
   volatility, volume), which is why vol-clustering doesn't contradict market efficiency;
   theory-first vs. search-then-validate feature engineering tradeoffs; complexity cap
   clarified (1-2 threshold conditions max, plain AND only, no fitted combination).
5. Locked a `volume_surge` feature definition for next round (not yet built): today's
   volume ÷ that stock's own trailing 20-day average, basket-averaged, shifted 1 day.
   Next session resume order (see baseline doc): (1) notebook correction pass, (2)
   screen `gap_pct` properly (own null-calibration + theory check + OOS gate), (3) build
   + screen `volume_surge`, (4) 54c.4 interaction check (low priority, trend already dead).

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Found + fixed a systematic EOD-riding artifact affecting every fv2 strategy family's top-ranked SL/TP combo (2026-09-04) — raw ZPF rankings were inflated by wide-SL/TP combos barely binding intraday, not genuine edge; now a mandatory backtesting_rules.md diagnostic (SL%/TP%/EOD+%/EOD-%)
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. All 6 strategies/ variants locked + deployed into monthly_reconciliation.py on the live
   bot VM (2026-09-05) — replaces the old debunked raw-ZPF variant list with rigorously
   validated SL/TP combos, correct raw-₹ alpha methodology, and dual NIFTY/basket benchmarks
