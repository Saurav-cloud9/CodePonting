# Session Log — 2026-08-27 (math-mode VM session)

## Alpha/beta CAPM regression — Steps 8-14 complete, applied to real data for the first time

- Completed the full derivation, Steps 0-14, in both `52_mathmode_full_derivation_expanded.md`
  (every algebra line) and `52_mathmode_full_derivation_chronological.md` (compact form):
  - Added the missing `Cov(A,k*B)=k*Cov(A,B)` rule to Step 8 (needed to correctly expand
    Step 11's cross term, `Cov(ȳ,β*(x0-x̄))` — a real gap in the file that the user caught).
  - Step 9's `Cov(ȳ,β)=0` proof and Step 10's `Var(ȳ)=σ²/n` / `Var(β)=σ²/Sxx` derivations were
    independently re-derived by the user (with real errors along the way: a missing denominator
    identity, a wrong substitution of a per-t term for a grand total, sign errors, notation
    inconsistencies) and corrected in real time — all now written up in full in the expanded file.
  - Step 11 (general SE formula), Step 12 (SE(α) special case), Step 13 (t-statistic), Step 14
    (p-value) all derived and confirmed correct.
- Extensive conceptual work resolving several real misconceptions along the way: what "random vs
  non-random" and "constant vs variable across t" actually mean (built a full reference table),
  why `Σ(x_t-x̄)=0` is universal but `Σ(x_t-x̄)²` is not, the "p-value fallacy" (1-p ≠ probability
  alpha is real), what the T-distribution actually represents (a distribution of the *estimated*
  alpha's ratio under the null, not something built from the *true* alpha), true-alpha vs
  estimated-alpha (α̂) terminology, and the confidence-vs-prediction-interval distinction.
- Built two new standalone visuals: `52_mathmode_confidence_vs_prediction_band.py`/`.png`
  (confidence band vs. wider prediction band, same toy dataset) and
  `52_mathmode_diagonal_collapse_example.py`/`.png` (n=6 heatmap of the Cov(y_t,y_s) grid,
  visualizing why independence collapses the double sum to its diagonal).
- **Sanity-checked the whole pipeline against known ground truth** (toy dataset's TRUE_ALPHA=0.01,
  TRUE_BETA=0.6, NOISE_SIGMA=0.02): beta and noise-variance estimates landed close to truth; alpha
  estimate came out with the wrong sign and p=0.44 (not significant) — a live illustration that a
  real, small alpha can easily fail to reach significance in a small sample (n=15), not a pipeline
  bug.
- **Applied the full derivation to REAL data for the first time**: POWERGRID eta0=2.0 Model C,
  n=2808 real trading days (2015-2026). Built out properly as Part 2 of
  `52_alpha_beta_concept_and_powergrid.ipynb` — data quality sanity checks (no gaps, no extreme
  outliers), residual diagnostics for homoscedasticity/independence (residuals vs time, vs
  market_return, 126-day rolling std), full step-by-step cells mirroring Part 1's structure, all
  executed via `jupyter nbconvert --execute --inplace` with every plot embedded in the notebook.
  - **Result: alpha is NOT statistically significant (p=0.3905)**. Beta also not significant
    (p=0.1245, beta≈-0.029, essentially no market exposure either way).
  - Residual diagnostics show noise level varies ~2.7x over time (real-market volatility
    clustering) — homoscedasticity only approximately holds, but the gap from significance is far
    too large for this to change the conclusion.
  - **This formally closes the question this entire math-mode thread was built to answer**:
    Model C's POWERGRID eta0=2.0 equity-curve outperformance is not statistically distinguishable
    from noise — confirms and formalizes (via rigorous statistical test, not just backtest
    comparison) the earlier PROGRESS_HISTORY conclusion that Model C has no transferable edge.

## Housekeeping

- Confirmed via `codeponting-84` (RS peer check-in): that session set up VS Code Tunnels on the
  VM for iPad file access, and renamed shorthand in CLAUDE.md (ris→ras, sif→rs "right save")
  across all 6 CLAUDE.md files, committed/merged to main. Explains the VS Code gateway
  connection error encountered earlier today (routine idle-timeout, tunnel daemon was healthy
  throughout — confirmed via `systemctl --user status code-tunnel.service` and log inspection;
  restarted the service as a troubleshooting step regardless).
- `remember` plugin (installed yesterday) confirmed working via `/remember:doctor` after a
  session restart picked up its hooks.

## Next session priorities
1. Math-mode thread is now functionally complete (Steps 0-14 fully derived + applied to real
   data with a definitive result). Any further work here would be exploratory/optional —
   e.g., re-testing on a different Model C eta0 value or a different stock, if there's appetite.
2. PRIMARY (separate thread): continue Pearson r feature screening in notebook 35 — next
   candidate is gap-size (`log(open_today/close_yesterday)`) vs intraday-move. **Stays P1.**
3. Not urgent: test the weak Pearson-r signal(s) found so far through actual RR/SL-TP exits
   rather than raw full-day-return capture.
