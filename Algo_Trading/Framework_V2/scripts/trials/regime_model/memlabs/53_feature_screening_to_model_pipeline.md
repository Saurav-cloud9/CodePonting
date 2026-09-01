# Step 53 — Feature Screening → Model Build → Alpha/P-value Pipeline

> New series, but this is a continuation of #35's work, not a restart. #35's Pearson r
> screening (RSI, Volume) stays where it is; #53 picks up the next candidate onward and
> carries it all the way through to a real model + significance verdict.

## Chronology

### Step 0 — Recap #35 (audit before continuing)

Before screening anything new, revisit `35_pearson_r_feature_screening.ipynb` end to end:
- Re-check the RSI period sweep (7/9/14/21/28) and Volume screening results already recorded.
- Re-verify the two real DS3 data bugs found+fixed along the way (INFY frozen-tick day,
  DIVISLAB un-split-adjusted day) are still correctly handled.
- Look for any mistakes worth correcting now, with fresh eyes, before building on top of it —
  cheaper to catch here than after a model is already built on a flawed screening result.

### Step 1 — Continue screening from where #35 left off

Next candidate already queued in TODO.md: **gap-size** (`log(open_today/close_yesterday)`) vs
intraday-move, across the DS3 30-stock + NIFTY universe. Individual Pearson r, same as RSI/Volume
were screened.

**Known blind spot to keep in mind here**: one-at-a-time r-based screening can wrongly discard a
feature that looks weak alone but would matter *in combination* with another (the XOR/interaction-
effect lesson — see `52_mathmode_xor_interaction_quadrant_example.py`). This step doesn't actively
correct for that blind spot; it's a limitation of screening features individually, addressed
properly at Step 2→4 below instead.

### Step 2 — Select candidates

Pick the features (from Step 1, and/or already-screened #35 results) that correlate decently —
not necessarily strongly, just meaningfully better than what's been found so far (RSI ~0.08,
Volume weaker, Model B/C's lag-based features near-zero, ~0.03-0.06). Looking for one or two
reasonable candidates to carry forward, not a guarantee of a strong signal.

### Step 2.5 — Interaction/XOR check (only if two candidates were selected)

Before combining two selected features into one model, draw their 2D scatter (colored by
target), same recipe as `32_model_b_actual_direction_quadrant.png` — this is the concrete
application of the XOR lesson flagged in Step 1: verify the pair doesn't hide a genuine joint
separation pattern that neither feature's individual r value predicted, before trusting whatever
the joint model produces. Skip this step if only one candidate was selected (nothing to combine).

### Step 3 — Conceptual primer: revisit #51 before building the model

If Step 2 produces **two** candidate features (not one), the model built in Step 4 is a genuine
**3D plane fit** (two independent variables + one dependent variable) — exactly the scenario
`51_least_squares_3d.md` illustrates conceptually (R²/SSE convergence, line→plane extension).
Revisit #51's images right here, before interpreting the real model's own R²/SSE, so the
geometric intuition (plane tightening as SSE drops, R² climbing) is fresh going in. This is
where #51 gets closed out — not as a separate standalone task, but as the lens brought into
Step 4.

(If Step 2 produces only **one** viable candidate, the model is a simpler 2D line fit instead —
same as the current POWERGRID alpha/beta test in #52 — and #51's plane-specific content doesn't
directly apply; the general least-squares concept still does.)

### Step 4 — Deploy into Model B or C

Build the actual model (Model B: `LinearRegression`, one-shot OLS fit — or Model C: `SGDRegressor`,
online learning — whichever fits the question) using the selected feature(s) from Step 2.

### Step 5 — Full alpha/beta derivation and final verdict

Same pipeline already validated in `52_alpha_beta_concept_and_powergrid.ipynb`:
- Fit alpha/beta, compute residuals.
- Residual diagnostics: vs time, vs market_return/feature (homoscedasticity check), rolling std
  (constant noise level check), histogram + fitted Gaussian curve (Gaussian-shape check).
- Var(error) → SE(alpha), SE(beta) → t-stats → p-values → final verdict (statistically
  significant or not).
- Document any assumption violations found (as was done for eta0=2.0/5.0 — heteroscedasticity
  tied to signal sign, non-Gaussian peaked histogram) and note whether n is large enough for
  CLT to protect the conclusion regardless.

## Summary of the full chain

```
#35 recap (Step 0)
   -> continue screening: gap-size vs intraday-move, individual r (Step 1)
   -> select 1-2 candidates (Step 2)
   -> [if 2 features] XOR/interaction check via 2D scatter (Step 2.5)
   -> [if 2 features] revisit #51 for plane-fit intuition (Step 3)
   -> build Model B/C with selected feature(s) (Step 4)
   -> full alpha/beta derivation -> SE -> t-stat -> p-value -> verdict (Step 5)
```
