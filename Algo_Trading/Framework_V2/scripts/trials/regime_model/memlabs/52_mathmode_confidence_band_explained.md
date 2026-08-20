# [MATH-MODE] Confidence band — what SE is and how it relates to the data and to alpha

**Note:** standalone math-mode material — pure concept, no trading/notebook data. Explains the
shaded band in Steps 5-6 of `52_alpha_beta_concept_and_powergrid.ipynb`, using a tiny 5-point
dummy dataset instead.

**Objective:** understand what SE (standard error) actually measures, why the band is narrow in
the middle and wide at the edges, and exactly how `SE(alpha)` is just a special case of that same
idea, evaluated at one specific spot.

---

## The dummy dataset (5 points, clean integers)

| x | y |
|---|---|
| -2 | 1 |
| -1 | 2 |
| 0 | 4 |
| 1 | 5 |
| 2 | 7 |

Fitted line (same beta/alpha steps as before): `beta = 1.5`, `alpha = 3.8` → `y = 3.8 + 1.5x`.
Residuals: `[0.2, -0.3, 0.2, -0.3, 0.2]` (sum = 0, as always). `Var(error) = 0.1` (n-2 = 3).
`Sxx = 10` (spread of the x values around their mean).

Graph: [`52_mathmode_confidence_band_example.png`](52_mathmode_confidence_band_example.png)
Script: [`52_mathmode_confidence_band_example.py`](52_mathmode_confidence_band_example.py)

---

## What SE is actually asking

The fitted line is only OUR BEST GUESS, built from these 5 points. A different 5 points (even from
the same underlying process) would fit a slightly different line. **SE at any point x0 measures
how much the line's height there could plausibly wobble, if we re-did this with different sample
data.** Small SE = confident about the line's height there. Big SE = not very confident.

## The formula, broken into its two ingredients

```
SE(y at x0) = sqrt( Var(error) * ( 1/n  +  (x0 - mean(x))^2 / Sxx ) )
```

Two separate sources of uncertainty added together, then scaled and square-rooted:

1. **`1/n`** — a baseline "we only have `n` points" uncertainty. Same for every x0. More data
   points anywhere → this shrinks → band gets thinner everywhere at once.
2. **`(x0 - mean(x))^2 / Sxx`** — an EXTRA penalty for standing far from the data's center of mass
   (`mean(x)`). This term is exactly **0** right at `x0 = mean(x)`, and grows the further out you
   go, divided by `Sxx` (how spread-out the x-data already is).

Both terms get multiplied by `Var(error)` (how noisy/scattered the residuals are — noisier data →
wider band everywhere), then square-rooted to bring it back to the same units as y.

**Why narrow in the middle, wide at the edges:** think of the fitted line like a **see-saw
balanced on a pivot at `mean(x)`.** We're not 100% sure of the exact tilt (`beta`) — but near the
pivot, an uncertain tilt barely moves the height. Far from the pivot, that same uncertain tilt
swings the height a lot. That's term #2 above, literally.

Confirmed with our numbers: `SE at x=0 (the pivot) = 0.14`, `SE at x=2 (the edge) = 0.24` —
visibly wider at the edge, exactly as the see-saw picture predicts.

## How this connects to alpha specifically

`alpha` isn't a separate idea — **alpha IS the line's height at x0 = 0** (that's its definition,
the y-intercept). So:

```
SE(alpha) = SE(y at x0) evaluated at x0 = 0
```

— the exact same formula above, just with `x0` plugged in as `0`. Nothing new. In our dummy
example, `mean(x)` also happens to be exactly `0`, so `x0=0` lands right on the pivot — meaning
`SE(alpha)` here is the narrowest point of the whole band (`0.14`, the minimum possible). That's a
coincidence of this dummy data, not a rule: in the real notebook, `mean(market_return)` is not
exactly 0, so `x0=0` sits slightly off the true pivot, and `SE(alpha)` is a little wider than the
band's absolute minimum — but always computed via this same one formula.

## Recap

| Concept | What it means here |
|---|---|
| SE(y at x0) | how uncertain the fitted line's height is, at one specific x0 |
| `1/n` term | baseline uncertainty from sample size, same everywhere |
| `(x0-mean(x))^2/Sxx` term | extra uncertainty from distance to the data's center (see-saw effect) |
| `Var(error)` | overall noise level — scales the whole band up/down |
| SE(alpha) | just SE(y at x0), with x0 fixed at 0 (since alpha = height at x=0) |
