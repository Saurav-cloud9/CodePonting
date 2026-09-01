# Session Log — 2026-08-30/31 → 2026-09-01 (math-mode VM session)

## Vector/geometric interpretation of the normal equations — completed in depth

- Walked through `52_mathmode_normal_equations_projection_interactive.html` (orthogonal
  projection view of Steps 1-2's normal equations) extensively:
  - Distinguished "spanning vectors" (the 1's-vector and x-vector, the generating pair) from
    "vectors in the plane" (any combination `a·1+b·x`) — only the former get the name.
  - Proved via linearity of the dot product why perpendicular-to-the-2-spanning-vectors implies
    perpendicular-to-the-entire-plane (not just those two vectors) — the actual reason checking
    2 equations suffices instead of infinitely many.
  - Disentangled ambient-space dimension (n = number of data points) from plane/hyperplane
    dimension (number of spanning vectors = number of parameters) — n=k means zero degrees of
    freedom, forces a perfect/overfit zero-residual fit; this ties directly to why `df=n-2` must
    be positive for SE/t-stat/p-value to mean anything.
  - Established that visually judging perpendicularity from a 3D screenshot is unreliable (both
    projection distortion and, for a hand-drawn reference line, genuine 3D-direction ambiguity)
    — dot product is the only real evidence, not the rendered picture.
  - Fully connected "normal equations" (normal=perpendicular, geometry) vs "normal/Gaussian
    residuals" (normal=bell-curve, statistics) — same English word, two unrelated meanings, only
    the second is a synonym for Gaussian.
  - Clarified i.i.d. Gaussian residuals as 3 separate conditions (independent / identically-
    distributed=homoscedastic / Gaussian-shaped), and that CLT protects alpha's own sampling
    distribution (a different "population of hypothetical datasets" than the T-distribution
    itself) regardless of whether the residual-level assumption holds exactly — rescues the
    *conclusion*, doesn't make the assumption true.
  - Confirmed OLS and SGDRegressor share the same linear-model shape and, restricted to squared-
    error loss, the same convex-bowl minimum (SGD converges toward it iteratively; OLS reaches it
    directly) — but OLS only exists for squared-error loss, while SGD generalizes to losses like
    Model C's epsilon-insensitive/passive-aggressive that OLS has no closed form for at all.

## POWERGRID residual diagnostics — 4th panel + mechanistic explanation of the X-shape

- Added a histogram + fitted-Gaussian-curve panel to `52_alpha_beta_concept_and_powergrid.ipynb`
  (now 4 panels total: vs time, vs market_return, rolling std, histogram). Finding: real residual
  histogram is visibly peaked/narrower than the fitted Gaussian — a genuine, mild non-Gaussian
  shape on top of the already-known heteroscedasticity.
- Fully explained the striking X-shaped "Residuals vs market_return" pattern algebraically:
  `strategy_return_t = signal_t × market_return_t` (signal ∈ {+1,-1}) substituted into
  `error_t = strategy_return_t - (alpha+beta×x_t)` collapses to two near-straight lines
  (`error≈x` for long days, `error≈-x` for short days, using the real fitted beta≈-0.029) — a
  deterministic artifact of how the strategy return is constructed, not real noise misbehaving.
  Corrected an earlier mislabeling: `market_return` in this notebook is POWERGRID's own actual
  return (true_y), not NIFTY — this is a "beat buy-and-hold" test, not a market-index CAPM test.

## eta0=2.0 selection-bias question — resolved, confirmed via eta0=5.0 run

- Flagged (correctly) that eta0=2.0 was chosen purely by best-of-9 raw cumulative return, a
  textbook selection-bias setup. fv2 confirmed from `50d_full_recap_seed.md`: 9 values tested
  (0.001-5.0), only 2/9 net-positive, eta0=2.0 best (+0.692), eta0=5.0 second (+0.201). fv2's
  argument: since the most-favorably-selected config already failed significance, the other 8
  (mostly worse) have no realistic path to significance either.
- Ran the confirmatory check directly: added Part 3 to the same notebook for eta0=5.0 — full
  pipeline (replication, alpha/beta fit, 4-panel residual diagnostics, SE/t/p-value, confidence
  band). **Result: alpha=-0.000033, p=0.9134** — even more decisively non-significant than
  eta0=2.0's 0.39. Confirms fv2's prediction exactly. eta0 selection-bias thread now closed.

## Single-feature/two-feature separability checks (Model B + Model C)

- Built Model B's #32-series direction-only visualizations (`32_model_b_actual_direction_only.py`
  /html, `32_model_b_actual_direction_quadrant.py`/png) — NIFTY50, lag_1+ma_lag_1 vs actual
  buy/sell direction. Corr ~0.03 for both features individually; 2D scatter shows a shapeless,
  fully intermixed cloud, no structure at all.
- Built a dummy XOR/interaction-effect toy example
  (`52_mathmode_xor_interaction_quadrant_example.py`/png) to test whether Model B's near-zero
  individual correlations could be hiding a real joint/interaction pattern (like XOR, where
  individual correlations are ~0 but the combination is perfectly separable). Confirmed: real
  Model B data shows NO such hidden structure either — genuinely no signal, not just linearly
  undetectable signal. Added a hypothetical straight-fitted-line overlay to the dummy example
  too, visually showing why a linear fit fails specifically on XOR-shaped data.
- Extended the same check to Model C (POWERGRID, single feature): `50e_powergrid_lag1_
  direction_only.py`/png — lag_1 alone vs actual buy/sell. Corr=-0.047, 50.9% sign-match (coin
  flip), fitted line's own predicted magnitude ~15x smaller than real return magnitude, model
  predicts BUY 74.6% of days (intercept-dominated). Confirms the same "no real feature signal"
  finding independently, on a different stock and different model.

## New planning doc: #53 — feature screening → model build → alpha/p-value pipeline

- Created `53_feature_screening_to_model_pipeline.md`, chaining together the full chronology:
  recap #35 (audit RSI/Volume screening for mistakes) → continue screening (gap-size vs
  intraday-move, individual r) → select 1-2 candidates → Step 2.5 XOR/interaction check via 2D
  scatter (only if 2 features selected) → Step 3 revisit #51 (least-squares-3D primer, only if
  2 features) → build Model B/C → full alpha/beta derivation to final p-value verdict (mirroring
  #52's now-validated pipeline). Explicitly a continuation of #35, not a restart.

## Tooling — VS Code Remote-SSH / Live Preview on the VM

- Worked through opening/previewing interactive Plotly HTML files from VS Code connected via
  SSH/Tunnel directly to the Oracle VM (distinct from the local WSL instance, confirmed as a
  separate machine/filesystem). Live Preview extension (embedded webview, JS-capable) is the
  right tool here — confirmed working, including hover tooltips, unlike earlier static-file
  viewers. "Open in Integrated Browser" (VS Code's newer built-in feature) confirmed local-only
  — not available in the Remote-SSH picker at all. Set `workbench.editorAssociations` to default
  `.html` files to Live Preview. Multiple-file-open workaround: split editor groups (preview-tab
  reuse is scoped per group, not global) — or use the built-in Browser panel's own tab support
  by pasting Live Preview's served URLs into it directly.
- cpgeneric (peer, RS check-in) separately confirmed: VM tunnel's Live Preview hardcodes
  127.0.0.1 (breaks over a remote tunnel — needs the manual tunnel URL + path workaround
  instead), and set up Live Preview cleanly on Saurav's desktop WSL VS Code session (works with
  no tunnel involved there).

## Peer check-ins (RS)

- cplearning (codeponting-d1): rerouted from ML module to Data Structures & Algorithms as of
  2026-08-28 (next Codedex ML lesson not yet unlocked); ML resumes once released.
- cpgeneric (codeponting-00): diagnosed the VM-tunnel Live Preview 127.0.0.1 issue (see above);
  verified 2026-08-28 kite_oracle_papertrading paper-trading run clean end-to-end (39 trades,
  PnL +29.31, ZPnL -13.22).

## Next session priorities

1. Math-mode/vector-geometry teaching thread is functionally complete for now — further work
   optional/exploratory only (e.g. Saurav returns for a specific math concept as needed).
2. PRIMARY: #53 pipeline, starting with Step 0 (recap #35 for mistakes) then Step 1 (screen
   gap-size vs intraday-move) — see `53_feature_screening_to_model_pipeline.md` for full plan.
3. F10 (parked): Model C 3D time-evolution visualization — curiosity-driven only, not blocking.
