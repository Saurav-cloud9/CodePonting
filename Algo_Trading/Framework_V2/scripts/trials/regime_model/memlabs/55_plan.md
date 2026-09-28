# #55 — Regression escalation for FLAGSHIP_6BCEH_SHORT_VWAP_RSI60

**Purpose**: escalate `#54`'s exhausted manual Pearson-r/threshold screening to a
fitted regression, per `54_...baseline.md` §4's design spec "last resort" step.
Workflow: math mode reasons/specs each sub-step, fv2 builds/runs it (Saurav-approved
split, 2026-09-24) — Opus tokens spent on reasoning, Sonnet on execution.

## Sub-steps

- **55a [DONE] — single-feature bridge (this doc's sibling: `55a_build.py` ->
  `55a_single_feature_ols.ipynb`)**. Not a discovery step — dispersion is already
  known to fail `#54`'s screen. Purpose: (1) show the regression framing is
  numerically equivalent to `#54`'s manual r-based screening for one feature, (2)
  build a clean, reusable regression pipeline `55b` extends. Reviewed before build
  (Agent tool plan review) — one fix applied: NaN-drop scope pinned to
  dispersion+zpnl only (n≈2497), matching `#54`'s original 2-feature-sample
  reference r=0.0565, not the wider 13-feature-sample r=0.0575.
- **55b (later) — multi-feature + Ridge + cross-validation**. Spec to follow from
  math mode once Saurav reviews 55a's results. This is where Ridge actually earns
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
