# Step 52 — full derivation, EXPANDED (every algebra line shown) [MATH-MODE]

Companion to `52_mathmode_full_derivation_chronological.md` (the compact/boxed-result version).
This file re-derives the same steps in the same order, but shows every intermediate algebra line
instead of jumping straight to the boxed result. Being built incrementally, in step order, as we
go back over each step in conversation — only as far as we've actually re-derived so far.

Formulas are in plain-text code blocks (not LaTeX) so they're easy to copy/paste back into chat,
using actual symbols (`α`, `β`, `x̄`, `ȳ`, `σ`) rather than spelled-out words — clearer when
several variables appear in one equation.

**Fitted line — two perspectives, same equation (`ŷ = α + β*x`):**
- *Prediction:* the best-fit relationship used to estimate/forecast `y` for a new or given `x`.
- *Alpha-derivation (inference, this file's focus):* the same line used to decompose `y` into a
  market-explained part (`β*x`) and a leftover intercept (`α`) — not for forecasting, but to
  isolate `α` so its statistical credibility (real skill vs. noise) can be tested.

---

### Step 0. Set up the model and the thing to minimize

**The regression equation — `ŷ(x0) = α + β*x0`.** This is the fitted line itself, used to predict
y at any x0. It's the same equation used throughout this entire derivation — it never changes;
later steps (e.g. Step 11) only ever rewrite it algebraically into a different-looking but
identical form, never a different line. It's also what `error_t` is built from below.

```
excess_strategy_return_t = α + β * excess_market_return_t + error_t
```

Rearranged: `error_t = y_t - (α + β*x_t)` (using `x_t`, `y_t` as shorthand from here on) — not a
line itself, but a per-point application of the regression equation above: plug the line's
predicted value in, subtract it from the actual observed `y_t`, get one residual number.

We want the `α`, `β` that make the total squared error as small as possible:

```
S = Σ error_t²  =  Σ (y_t - α - β*x_t)²
```

Aside (parabola check): holding `β` fixed and expanding `S` as a function of `α` alone confirms
`S` is a parabola in `α` (matches the general form `y = a*x² + b*x + c`):

```
S(α) = Σ(y_t - β*x_t - α)²
     = n*α²  -  2*(Σ(y_t - β*x_t))*α  +  Σ(y_t - β*x_t)²
```

so `a = n` (always > 0) → always opens upward → always has a minimum, which is exactly the point
Step 1 solves for.

Sub-step (cross-check): differentiate this parabola form directly, term by term, using the plain
power rule — no chain rule needed here since `α` only appears as `α²`, `α¹`, `α⁰` (constant) in
this form:

```
d/dα [ n*α² ]                          =  2*n*α
d/dα [ -2*(Σ(y_t - β*x_t))*α ]         =  -2*Σ(y_t - β*x_t)      (coefficient of α¹, times 1)
d/dα [ Σ(y_t - β*x_t)² ]               =  0                       (no α here — constant term)
```

Adding the three pieces:

```
dS/dα = 2*n*α  -  2*Σ(y_t - β*x_t)
```

This matches Step 1's chain-rule result below once expanded — confirms both routes (differentiate
the expanded parabola vs. differentiate the original squared-sum via chain rule) land on the same
slope. Worked through: `-2*Σ(y_t - α - β*x_t) = -2*Σy_t + 2*n*α + 2*β*Σx_t = 2*n*α - 2*Σ(y_t - β*x_t)`
— identical to the power-rule result above.

---

### Step 1. Normal equation 1 — `dS/dα = 0` — solve for `α`

Differentiate `S` w.r.t. `α` (chain rule — derivative of the outer square times derivative of the
inner bracket w.r.t. `α`, which is `-1`):

```
dS/dα = Σ 2*(y_t - α - β*x_t)*(-1)  =  -2 * Σ(y_t - α - β*x_t)
```

Set the slope to `0` (minimum condition) and divide both sides by `-2`:

```
Σ(y_t - α - β*x_t) = 0
```

Expand the summation into three separate sums:

```
Σy_t  -  Σα  -  β*Σx_t  =  0
```

Simplify each piece — `Σα` over `n` points is `n*α` (`α` is a constant, added to itself `n`
times); `Σy_t = n*ȳ` and `Σx_t = n*x̄` by definition of the mean:

```
n*ȳ  -  n*α  -  β*n*x̄  =  0
```

Divide everything by `n`:

```
ȳ - α - β*x̄ = 0
```

Solve for `α`:

```
α = ȳ - β*x̄
```

---

### Step 2. Normal equation 2 — `dS/dβ = 0` — solve for `β`

Differentiate `S` w.r.t. `β` (chain rule — derivative of the outer square times derivative of the
inner bracket w.r.t. `β`; this time the inner derivative is `-x_t`, not `-1`, since `β` is
multiplied by `x_t`):

```
dS/dβ = Σ 2*(y_t - α - β*x_t)*(-x_t)  =  -2 * Σ x_t*(y_t - α - β*x_t)
```

Set the slope to `0` (minimum condition) and divide both sides by `-2`:

```
Σ x_t*(y_t - α - β*x_t) = 0
```

Distribute `x_t` into the bracket — `x_t` is not a constant (it varies per `t`), so it can't be
moved or cancelled; it must multiply each term inside:

```
Σ(x_t*y_t)  -  Σ(α*x_t)  -  Σ(β*x_t²)  =  0
```

Simplify the middle term — `α` is constant across `t` (unlike `x_t`), so it factors out of its
sum: `Σ(α*x_t) = α*Σx_t = α*(n*x̄) = n*α*x̄`. The last term keeps `β` factored out as `β*Σx_t²`
(`Σx_t²` itself does NOT simplify to `n*x̄²` — squaring each `x_t` and summing is not the same as
summing then squaring):

```
Σ(x_t*y_t)  -  n*α*x̄  -  β*Σx_t²  =  0
```

Substitute Step 1's `α = ȳ - β*x̄` (needed to eliminate `α` and solve purely for `β`):

```
Σ(x_t*y_t)  -  n*x̄*(ȳ - β*x̄)  -  β*Σx_t²  =  0
```

Distribute `n*x̄` across the bracket:

```
Σ(x_t*y_t)  -  n*x̄*ȳ  +  n*β*x̄²  -  β*Σx_t²  =  0
```

Group the `β` terms on one side:

```
β*Σx_t²  -  n*β*x̄²  =  Σ(x_t*y_t)  -  n*x̄*ȳ
```

Factor `β` out:

```
β*(Σx_t² - n*x̄²)  =  Σ(x_t*y_t)  -  n*x̄*ȳ
```

Solve for `β`:

```
β = (Σ(x_t*y_t) - n*x̄*ȳ) / (Σx_t² - n*x̄²)
```

---

**Recognize this as `Cov(x,y)/Var(x)` — expand both and show they match**

`Cov(x,y)` and `Var(x)` have their own separate definitions (Step 5):

```
Cov(x,y) = (1/n) * Σ(x_t - x̄)(y_t - ȳ)
Var(x)   = (1/n) * Σ(x_t - x̄)²
```

These don't obviously equal `β`'s numerator/denominator above — has to be shown by expanding.

*`Cov(x,y)`'s sum — FOIL-expand the product, then distribute `Σ` across the four terms:*

```
Σ(x_t-x̄)(y_t-ȳ) = Σ(x_t*y_t - x_t*ȳ - x̄*y_t + x̄*ȳ)
                 = Σx_t*y_t  -  ȳ*Σx_t  -  x̄*Σy_t  +  Σ(x̄*ȳ)
```

Substitute `Σx_t = n*x̄`, `Σy_t = n*ȳ`, and `Σ(x̄*ȳ)` over `n` terms `= n*x̄*ȳ`:

```
= Σx_t*y_t  -  ȳ*(n*x̄)  -  x̄*(n*ȳ)  +  n*x̄*ȳ
= Σx_t*y_t  -  n*x̄*ȳ  -  n*x̄*ȳ  +  n*x̄*ȳ
```

Two of the three `n*x̄*ȳ` terms cancel, leaving one:

```
Σ(x_t-x̄)(y_t-ȳ)  =  Σx_t*y_t  -  n*x̄*ȳ
```

Matches `β`'s numerator exactly.

*`Var(x)`'s sum — same expansion, special case `y_t→x_t`, `ȳ→x̄`:*

```
Σ(x_t-x̄)²  =  Σ(x_t² - 2*x_t*x̄ + x̄²)
           =  Σx_t²  -  2*x̄*Σx_t  +  Σx̄²
           =  Σx_t²  -  2*x̄*(n*x̄)  +  n*x̄²
           =  Σx_t²  -  2n*x̄²  +  n*x̄²
           =  Σx_t²  -  n*x̄²
```

Matches `β`'s denominator exactly.

Since `Cov` and `Var`'s own `1/n` factors cancel when dividing one by the other, the ratio of the
plain sums equals the ratio of `Cov/Var` directly:

```
β  =  (Σx_t*y_t - n*x̄*ȳ) / (Σx_t² - n*x̄²)  =  Cov(x,y) / Var(x)
```

Fully derived, both directions.

---

**Summary — understanding checkpoint after Steps 0-2**

- `S` (sum of squared errors) is the core object of OLS — "minimize `S`" *is* the definition of
  Ordinary Least Squares.
- `error_t` (a single residual) is linear in `α` — squaring it is what turns `S(α)` into a
  parabola. A parabola only has a minimum if it opens upward (`a > 0`); here `a = n`, always
  positive, so a minimum is guaranteed.
- `Σ error_t = 0` is NOT the minimum point itself — it's the **condition/equation** that,
  once solved, tells us *where* the minimum is (same relationship for `β`:
  `Σ(error_t * x_t) = 0` is its condition). Solving these conditions gives the actual
  locations: `α = ȳ - β*x̄` and `β = Cov(x,y)/Var(x)`.
- `α` (alpha) = the strategy's excess return unexplained by market exposure — the "skill"
  component. Desirable when positive and statistically real (tested later via the p-value,
  Step 14).
- `β` (beta) = how sensitive the strategy's returns are to market moves (market exposure/slope).
  Not inherently good or bad on its own — its role in this specific thread is to capture the
  market-driven part of returns so whatever's left over (`α`) can be attributed to something
  other than the market.

---

### Step 3. Now that `α`, `β` are known numbers — compute each residual

For every data point `t` in the dataset, plug in the actual `y_t`, `x_t`, and the now-known
numeric `α`, `β` to get one real number per `t` — the gap between actual and model-predicted:

```
error_t = y_t - (α + β*x_t)
```

With `n` data points, this produces `n` individual residual numbers (`error_1, error_2, ...,
error_n`) — the raw material Steps 4-6 are built from.

Distinct from Step 0: there, `error_t` was symbolic/abstract (used to build `S` before `α`, `β`
were known, never actually computed). Here, it becomes real, computable numbers for the first
time.

---

### Step 4. Two properties fall out for free (they're just Steps 1 and 2, rearranged)

No new derivation needed — these are Steps 1 and 2's normal equations, restated in their
original (unrearranged) form, now interpreted as properties of the residuals:

```
Σ error_t = 0                  (this IS Step 1's equation, unrearranged)
Σ (error_t * x_t) = 0          (this IS Step 2's equation, unrearranged)
```

Because `α`, `β` were chosen specifically to satisfy `dS/dα = 0` and `dS/dβ = 0`, it's
guaranteed that: the residuals sum to exactly zero, and the residuals are "uncorrelated" with
`x_t` (their `x_t`-weighted sum is zero). Both facts get reused later — Step 6 uses the first
one to justify why only `n-2` residuals are truly free (not `n`).

---

### Step 5. Variance / Covariance definitions (used throughout)

```
Var(X)    = (1/n) * Σ (x_i - mean(X))²
Cov(X,Y)  = (1/n) * Σ (x_i - mean(X)) * (y_i - mean(Y))
```

`Var(X)` measures how spread out a single variable's values are around its own mean — no second
variable involved. `Cov(X,Y)` needs two variables — it measures whether their deviations from
their own means tend to move together (same sign → positive Cov) or oppositely (negative Cov).

Correlation is `Cov(X,Y)` normalized by both standard deviations:
`Correlation(X,Y) = Cov(X,Y) / (SD(X)*SD(Y))`. So `Cov(X,Y) = 0` implies `Correlation(X,Y) = 0`
too (zero numerator, as long as the SDs are finite/nonzero).

Aside — why `Σ(error_t*x_t)=0` (Step 4) implies zero *correlation*, not just zero raw sum: since
residuals already have mean zero (`Σerror_t=0`, Step 4's other property),
`Cov(error,x) = (1/n)*Σ(error_t - 0)*(x_t - x̄) = (1/n)*[Σ(error_t*x_t) - x̄*Σerror_t] =
(1/n)*[0 - x̄*0] = 0`. Both Step 4 properties combine to give this — not a generic law that any
"sum of products = 0" implies uncorrelated on its own.

---

### Step 6. Residual variance — why `n-2`, not `n`

`S = Σ error_t²` has two exact constraints on it (Step 4) — fitting `α` and `β` each impose one
linear constraint on the residual set (`Σerror_t=0` from `α`, `Σ(error_t*x_t)=0` from `β`). Each
constraint forces exactly one residual to be fully determined by the rest — not free. So out of
`n` total residuals, only `n-2` are genuinely free to vary independently; the correct variance
divides by that smaller number, not `n`:

```
Var(error) = (1 / (n-2)) * Σ error_t²
```

Concrete demo (10 residuals, 8 freely chosen + 2 forced by the two constraints — full worked
numbers and chart in `52_mathmode_variance_dof_example.py`/`.png`):

```
e_1..e_8 (free)   = 1, -2, 3, -1, 0, 2, -3, 1
e_9, e_10 (forced by solving both constraints together) = -9, 8

Σ error_t   = 0     (check: 1-2+3-1+0+2-3+1-9+8 = 0)  ✓
Σ error_t²  = 174

Var (n=10)    = 174/10 = 17.40   <- wrong divisor, biased low
Var (n-2=8)   = 174/8  = 21.75   <- correct, Step 6's formula
```

Using `n` instead of `n-2` **deflates** the variance estimate (understates it) — not inflates it.
That matters downstream: a deflated `Var(error)` feeds into a deflated `SE(α)` (Step 12), which
inflates the t-statistic (`t = α/SE(α)`, Step 13) and produces an overconfident (too-small)
p-value — making `α` look more statistically real than the data actually supports. The `n-2`
correction exists specifically to prevent that chain of overconfidence.

---

**Summary — understanding checkpoint after Steps 3-6**

- Step 3 turns the abstract `error_t` formula into `n` real, computed numbers (one per data
  point), using the now-known `α`, `β`.
- Step 4's two properties (`Σerror_t=0`, `Σ(error_t*x_t)=0`) aren't new facts — they're Steps 1
  and 2's own fitting equations, now read as guaranteed properties of the residuals.
- Fitting `α` and `β` is a joint/simultaneous solve (`β`'s derivation substitutes `α`'s formula
  directly in), not two independent computations — which is exactly why each one's normal
  equation imposes one linear constraint on the residual set.
- 2 constraints → 2 residuals become fully determined by the rest → `n-2` genuinely free
  residuals, not `n` — the concrete mechanism behind "2 degrees of freedom consumed."
- `Var(error)` divides by `n-2` specifically to avoid deflating the variance estimate, since a
  deflated variance would quietly overstate `α`'s statistical significance several steps later
  (SE → t-stat → p-value).

---

### Step 7. Rewrite `β` and `ȳ` as weighted sums of the `y_t`'s (needed for Step 9-10)

Start directly from Step 2's `β` formula and isolate `y_t` on its own — numerator and
denominator each need their own simplification.

**Numerator** — substitute `n*x̄*ȳ = x̄*Σy_t = Σ(x̄*y_t)` (x̄ is constant across `t`, so it
distributes into the sum), then combine the two sums and factor `y_t` out:

```
Σx_t*y_t - n*x̄*ȳ  =  Σx_t*y_t - Σ(x̄*y_t)  =  Σ[(x_t*y_t) - (x̄*y_t)]  =  Σ(x_t - x̄)*y_t
```

**Denominator** — prove `Σx_t² - n*x̄² = Σ(x_t-x̄)²` by expanding the right side (this is the
identity needed before the denominator can be labeled `Sxx`):

```
Σ(x_t-x̄)² = Σ(x_t² + x̄² - 2*x_t*x̄)
          = Σx_t² + Σx̄² - Σ(2*x_t*x̄)
          = Σx_t² + n*x̄² - 2*x̄*Σx_t          (Σx̄² over n terms = n*x̄²; factor out constant 2*x̄)
          = Σx_t² + n*x̄² - 2*x̄*(n*x̄)          (substitute Σx_t = n*x̄)
          = Σx_t² + n*x̄² - 2n*x̄²
          = Σx_t² - n*x̄²
```

Combining both results — the numerator and denominator simplify to:

```
β = Σ(x_t-x̄)*y_t / Sxx,     Sxx = Σ(x_t-x̄)²
```

Since `Sxx` is a single fixed number, pull it inside the sum and combine it with `(x_t-x̄)` into
one weight per `t`:

```
β  = Σ w_t * y_t,     w_t = (x_t - x̄) / Sxx

ȳ  = Σ v_t * y_t,     v_t = 1/n     (no derivation needed — direct from the definition of the mean)
```

Both `β` and `ȳ` are weighted sums of the same underlying `y_t`'s, but with different, distinct
weights — `w_t` varies per `t` (depends on that point's own `x_t`); `v_t` is the same constant
for every `t`. Both `w_t` and `v_t` are named purely as an intermediate device for Steps 9-10;
they resolve back to plain numbers (`1/Sxx`, `1/n`) once those steps are done.

---

*(To be continued — Step 8 onward added as we re-derive them
in conversation.)*
