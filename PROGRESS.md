# PROGRESS.md — CodePonting
# Two views, 5 pointers each. Update both on every RS.
# Full history → PROGRESS_HISTORY.md
# ─────────────────────────────────────────────────────────────

── RECENT (last 5 steps) ────────────────────────────────────
1. Completed the vector/geometric interpretation of the normal equations (orthogonal projection,
   `52_mathmode_normal_equations_projection_interactive.html`) — spanning vectors vs vectors-in-
   the-plane, degrees of freedom (ambient-space dim vs plane dim), OLS-as-projection equivalence,
   Gaussian/normal-equations terminology disambiguation, CLT's role protecting alpha's sampling
   distribution regardless of residual-shape violations
2. Added a 4th panel (histogram + fitted Gaussian curve) to the POWERGRID residual diagnostics
   in `52_alpha_beta_concept_and_powergrid.ipynb`; explained the X-shaped heteroscedasticity
   mechanistically (strategy_return = signal_t × market_return_t collapses residual into two
   near-straight lines, slope ≈+1.03/-0.97) — deterministic artifact of strategy construction,
   not real noise misbehaving
3. Resolved the eta0=2.0 selection-bias question (fv2 confirmed best-of-9 by raw return): ran a
   confirmatory Part 3 in the same notebook for eta0=5.0 (second-best) — alpha=-0.000033,
   p=0.9134, even more decisively non-significant than eta0=2.0's p=0.39. Closes the eta0 thread
4. Built Model B's #32-series direction-only visualizations (NIFTY50, lag_1+ma_lag_1 vs actual
   buy/sell) and a single-feature POWERGRID/Model C check (`50e_powergrid_lag1_direction_only.py`)
   — both show no separating power (near-zero correlation, ~coin-flip sign-match); confirmed via
   a dummy XOR toy example that this isn't a hidden interaction effect either
5. Created `53_feature_screening_to_model_pipeline.md` — chains #35 recap → continue screening
   (gap-size vs intraday-move, r + 2D-scatter/XOR check) → select candidates → #51 plane-fit
   primer (if 2 features) → build Model B/C → full alpha/beta derivation to final p-value,
   picking up #35's work rather than restarting it

── MILESTONES (5 most important) ────────────────────────────
1. v1 clean-touch SHORT locked: SL=2.0x/TP=4.5x → PF=1.135 Sharpe=2.358 (110,641 trades, DS3 11yr) — cross-validated (array backtest + offline engine + Grok)
2. Live paper-trading bot successfully connected + traded on real market data for the first time (2026-07-20): real signals fired, first real trade closed (WIPRO, SL hit) with verified-correct PnL math
3. Live bot now has a confirmed-working full daily lifecycle on local PC AND on the VM: connect → warm-up → trade → EOD tick-exit → auto-stop
4. VM deployment hardened for unattended operation: systemd auto-restart-on-reboot + crash-alert (ntfy push to desktop/phone), crash-safe position recovery, warmup-boundary duplicate/gap bug fully fixed, and data-loss-on-restart fixed — all tested and confirmed working on real market data (2026-07-23/24)
5. Model C (online PA learning) formally, statistically confirmed to have no defensible edge across its full eta0 sweep: POWERGRID's best-of-9 (eta0=2.0, p=0.39) AND second-best (eta0=5.0, p=0.91) both fail significance — closes the selection-bias question definitively, reinforcing the same rigor bar set by the NIFTY50-gate debunking (2026-08-16)
