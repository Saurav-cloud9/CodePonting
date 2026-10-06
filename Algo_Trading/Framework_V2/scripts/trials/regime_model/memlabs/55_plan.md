# #55 — Regression escalation for FLAGSHIP_6BCEH_SHORT_VWAP_RSI60

**Purpose**: escalate `#54`'s exhausted manual Pearson-r/threshold screening to a
fitted regression, per `54_...baseline.md` §4's design spec "last resort" step.
Workflow: math mode reasons/specs each sub-step, fv2 builds/runs it (Saurav-approved
split, 2026-09-24) — Opus tokens spent on reasoning, Sonnet on execution.

## Sub-steps

- **55a [DONE] — exploratory bridge + full 12-step template on dispersion alone (kept as-is, not to be modified)** (`55a_build.py` ->
  `55a_single_feature_ols.ipynb`, 33 cells). Saurav's call (2026-09-27/10-04): complete
  the full template on one feature first, `55b` on hold. Sections 1-8B are the
  FULL-sample bridge/visual reference (reviewed before build — NaN-drop pinned to
  dispersion+zpnl only, n≈2497, matching `#54`'s original reference r=0.0565).
  Sections 9-13 (also plan-reviewed before build) redo the gating steps correctly on
  TRAIN only: steps 1-9 TRAIN-calibrated, decision boundary, Ridge (closed-form +
  sklearn cross-check, exact match), chronological 5-fold CV (TimeSeriesSplit,
  expanding window) to pick λ, and a 4-gate summary table. Result: CV chose λ=0 (OLS)
  — no held-out benefit to shrinking. 3/4 gates pass (A: OOS R²>0 ✓, B: textbook
  p<0.05 ✓, C: TRAIN-calibrated circular-shift p<0.05 ✓, D: TEST traded-days ZPF>1.0
  ✗) → verdict NEEDS-MORE-WORK under this 4-gate framework. Important caveat: this
  4-gate framework is more lenient than `#54`'s full max-of-13 discipline (Gate C
  uses TRAIN's own circular-shift calibration, not the full-sample max-of-13
  correction — a plan-review fix, since that ceiling was derived on a different n) —
  doesn't contradict `#54`'s RULED OUT verdict, just reflects a narrower bar.
- **55b [DONE, 2026-10-06] — clean 12-step template on dispersion** (`55b_build.py` ->
  `55b_dispersion_12step.ipynb`, 31 cells). Saurav's call: new notebook laid out strictly as
  3 stages (Build 1-4 / Is it real? 5-9 / Trading rule 10-12), one markdown + one code cell per
  step, no full-sample/equivalence/two-feature cells; step 10 includes the yellow dashed
  decision-boundary chart. 17 numeric asserts + exact-count/verdict asserts against 55a
  Sections 9-13 all pass (w=1.154600, b=-2.2046, t=2.4909, textbook p=0.012836, circular p=19/1746=0.010882,
  x*=1.9094, chosen lambda=0, 3/4 gates, NEEDS-MORE-WORK).
- **55c (on hold, starts after 55b) — feature pairs / multi-feature + Ridge + cross-validation**
  (previously labelled 55b). Spec to follow from math mode. This is where Ridge actually earns
  its keep (correlated features, e.g. dispersion x india_vix_level r=0.49).

## Conventions carried over from #54 (do not deviate silently)

- Circular-shift null (exhaustive n-1 rotations) is the correct primary — an iid
  shuffle was found too lenient for autocorrelated features (dispersion acf1=0.417).
- Chronological (not random) train/test split for any OOS claim.
- Target: `daily_zpnl` (continuous, leads) computed as `groupby('date')['zpnl'].sum()`
  on `54c_trade_log_with_features.csv`; features already lagged 1 day at build time
  (`54c_regime_features.py`'s `.shift(1)`) — never lag again on join.
- `#54`'s max-of-13 circular-shift ceiling (daily_zpnl): ceil95=0.0637, ceil99=0.0812
  (from `54e_screen_us_overnight.ipynb`) — reused as reference, not recomputed here.
