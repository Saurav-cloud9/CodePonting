# t and T — disambiguation note

**Objective:** `52_alpha_beta_concept_and_powergrid.ipynb` uses the letter "t" (and "T") for
**two completely unrelated things**. That's almost certainly the source of confusion — same
letter, two different jobs. This file isolates each meaning with the smallest possible example,
using real numbers pulled straight from that notebook's toy dataset (just the first 3 of its 15
points, to keep it minimal).

---

## Meaning #1 — "t" as an INDEX (a position pointer)

This is the `error_t`, `market_return_t` kind of "t" — same idea we already covered.

The notebook's real toy data (first 3 of 15 points):

| t | market_return |
|---|---|
| 1 | 0.0000 |
| 2 | 0.0090 |
| 3 | -0.0082 |

Here `t` just walks through the list: t=1 points at 0.0000, t=2 points at 0.0090, t=3 points at
-0.0082. `n` (the notebook's variable name for total count) = 15 for the full list. This "t" never
does any math by itself — it only *labels* which row you're looking at.

## Meaning #2 — "t" as the T-STATISTIC (a single computed number)

Completely different thing. This "t" is not a position — it's the *answer* to one specific
calculation, done ONCE on the whole dataset (not once per row):

```
t_stat = alpha / SE(alpha)
```

Real numbers from the notebook: `alpha = -0.0041`, `SE(alpha) = 0.0052`, so:

```
t_stat = -0.0041 / 0.0052 = -0.7971
```

That's it — one single number, `-0.7971`. It answers "how many SE(alpha)-widths away from zero is
our alpha?" Nothing to do with "which row" — there's no list being walked through here.

## Meaning #3 — capital "T" as a RANDOM VARIABLE (a whole distribution/curve)

In the notebook's Step 8 line — `p-value = P(|T| > |t|), T ~ t-distribution` — capital `T` means
"imagine repeating this whole experiment (new random data, refit alpha/beta) many times; each
repeat produces its own t_stat. T is the name for that whole *spread of possible outcomes* — the
bell-shaped-ish curve in the Step 7-8 plot."

So the p-value question is: "if the TRUE alpha were exactly 0, how often would a random repeat of
this experiment produce a t_stat as extreme as the *one specific number* we actually got
(-0.7971)?" — that's comparing meaning #2 (one observed number) against meaning #3 (the full range
of what could have happened).

⚠️ Note: in this notebook, capital `T` does **NOT** mean "total number of data points" (that job
belongs to `n` = 15 here). `T` is only the random-variable name for the t-distribution.

---

## Quick recap

| Symbol | What it is | Notebook variable | Example value |
|---|---|---|---|
| `t` (subscript, e.g. `market_return_t`) | index — which row | loop position | t=1 → 0.0000, t=2 → 0.0090 ... |
| `n` | total count of rows | `n` | 15 |
| `t` (t-statistic) | one computed number, whole-dataset | `t_stat` | -0.7971 |
| `T` | random variable / t-distribution curve | (conceptual, plotted as the bell curve) | n/a — it's a shape, not a number |

---

## [MATH-MODE] Aside — probability density, via a population-density analogy

**Note:** this section is standalone math-mode material (pure concept, no trading/notebook data) —
not part of the alpha/beta CAPM walkthrough above. It exists to build intuition for "density x
width = probability" (used in Step 8's p-value, where the shaded tail AREA is the probability, not
the curve's height).

**Analogy:** a population density map. The height/color at one exact point tells you how crowded
that spot is — but to get an actual headcount, you multiply density by the size (width) of a
region: `density x width = count`. Same shape as `probability density x width = probability`.

**Dummy example** (numbers, no trading data) — a 10 km road with 2 segments of constant density:

| segment | density |
|---|---|
| km 0 to 4 | 100 people/km |
| km 4 to 10 | 50 people/km |

- Total population = `100*4 + 50*6 = 400 + 300 = 700 people`.
- Headcount in the window **km 2 to 6** (crosses both segments) = sum of the two rectangle pieces
  it overlaps: `100*(4-2) + 50*(6-4) = 200 + 100 = 300 people`.

Density alone (100, or 50) is never a headcount — you only get a real count once you multiply by a
width. That's exactly the p-value logic: the t-distribution's curve HEIGHT is not a probability;
the shaded tail's AREA is.

Graph + generating script (dark-mode, per project convention), saved in this folder:
- [`52_mathmode_population_density_example.png`](52_mathmode_population_density_example.png)
- [`52_mathmode_population_density_example.py`](52_mathmode_population_density_example.py)
