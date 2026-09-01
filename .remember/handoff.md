# Handoff Note — 2026-09-01 (math-mode VM session)

## Current State — Math-mode/vector-geometry teaching thread (COMPLETE for now)

- Alpha/beta CAPM derivation (Steps 0-14) was already complete going into this session (see
  prior handoff). This session extended the *conceptual* side: the vector/orthogonal-projection
  interpretation of the normal equations (`52_mathmode_normal_equations_projection_interactive.
  html`), covering spanning vectors, degrees of freedom (ambient-space vs plane dimension),
  OLS-as-projection equivalence, Gaussian-vs-normal terminology, i.i.d. Gaussian assumption
  breakdown, CLT's role, and OLS-vs-SGDRegressor's relationship (same shape, same convex minimum
  for squared-error loss, but SGD generalizes to losses OLS has no closed form for).
- Full detail: `.remember/today.md` (this session) + `memlabs/50d_full_recap_seed.md` +
  `memlabs/52_mathmode_session_handoff.md` (prior sessions).
- Thread is functionally complete — any further work here is optional/exploratory, on Saurav's
  request for a specific concept, not a continuation of unfinished derivation work.

## Current State — POWERGRID Model C eta0 selection-bias question (RESOLVED/CLOSED)

- Saurav flagged eta0=2.0 (used throughout the alpha/beta test) was chosen purely by best-of-9
  raw cumulative return — a real selection-bias risk. fv2 confirmed the sweep context (9 values
  tested, 0.001-5.0, only 2/9 net-positive) and argued the best-of-9 already failing significance
  means the rest have no realistic path to significance either.
- Confirmatory run added as Part 3 in `52_alpha_beta_concept_and_powergrid.ipynb`: eta0=5.0
  (second-best, +0.201 raw return) → **alpha=-0.000033, p=0.9134** — even more decisively
  non-significant than eta0=2.0's p=0.39. Confirms fv2's reasoning. **This question is closed.**

## Current State — Feature separability checks (Model B two-feature, Model C single-feature)

- Built direction-only visualizations for both models confirming **no separating power** in the
  features tested so far:
  - Model B (NIFTY50, lag_1+ma_lag_1): `32_model_b_actual_direction_only.py`/html,
    `32_model_b_actual_direction_quadrant.py`/png. Corr~0.03 each, shapeless 2D scatter.
  - Model C (POWERGRID, lag_1 only): `50e_powergrid_lag1_direction_only.py`/png. Corr=-0.047,
    50.9% sign-match (coin flip).
- Verified via a dummy XOR/interaction-effect toy example
  (`52_mathmode_xor_interaction_quadrant_example.py`/png) that Model B's near-zero individual
  correlations aren't hiding a real joint/interaction pattern — genuinely no signal at all, not
  just a linearly-undetectable one.

## Current State — MemLabs Pearson's r feature screening (PRIMARY, continues via new #53 doc)

- **New**: `53_feature_screening_to_model_pipeline.md` created — full chronology from #35 recap
  through to a final alpha/p-value verdict:
  1. Recap #35 (`35_pearson_r_feature_screening.ipynb`) end-to-end, checking for mistakes.
  2. Continue screening: gap-size (`log(open_today/close_yesterday)`) vs intraday-move.
  3. Select 1-2 candidates (meaningfully better than RSI's r≈0.08).
  4. Step 2.5 (if 2 features): XOR/interaction check via 2D scatter, same recipe as Model B's.
  5. Step 3 (if 2 features): revisit `51_least_squares_3d.md` for plane-fit intuition before
     interpreting the real model's R²/SSE.
  6. Build Model B/C with selected feature(s).
  7. Full alpha/beta derivation → residual diagnostics → SE → t-stat → p-value → verdict,
     mirroring #52's now-validated pipeline.
- **This is a continuation of #35, not a restart** — #35's existing RSI/Volume results stay
  where they are; #53 is the plan for carrying the *next* candidate all the way through.
- **Next action**: Step 0 of #53 — recap #35 for correctness before screening gap-size.

## Housekeeping / Tooling

- VS Code Remote-SSH (VM) HTML preview workflow clarified: Live Preview extension (embedded,
  JS-capable webview) is correct; "Open in Integrated Browser" (VS Code's newer built-in
  feature) is confirmed local-machine-only, not available over Remote-SSH at all.
  `workbench.editorAssociations` set to default `.html` → Live Preview. Multi-file-open handled
  via split editor groups (preview-tab reuse is per-group) or the Browser panel's own tabs.
- cpgeneric (peer) separately found: VM tunnel's Live Preview hardcodes 127.0.0.1 (breaks over a
  remote tunnel, needs manual tunnel-URL+path workaround); set up Live Preview cleanly on
  Saurav's desktop WSL VS Code instead (works with no tunnel involved).
- cplearning (peer): rerouted from ML module to Data Structures & Algorithms (2026-08-28, next
  Codedex ML lesson not yet unlocked); resumes once released.

## Known Issues

- None new beyond what's documented above. Prior known issues (TODO.md glossary SL/TP note,
  ma_30_rejection_v1.py's missing EOD entry-skip) still carried over, unchanged.
