# Step 52 — Alpha/Beta CAPM regression: full derivation, chronological order [MATH-MODE]

**Note:** standalone math-mode reference. Unlike `52_alpha_beta_formulas.md` (which lists formulas
in APPLICATION order — the order you'd plug numbers into a spreadsheet), this file lists them in
the order they were actually **derived**, each with the calculation shown, not just the result.
Built entirely from this conversation's own step-by-step derivations.

Formulas are in plain-text code blocks (not LaTeX) so they're easy to copy/paste back into chat,
using actual symbols (`α`, `β`, `x̄`, `ȳ`, `σ`) rather than spelled-out words — clearer when
several variables appear in one equation.

**Regression, in general:** the technique of fitting the best-fit line/curve that relates one
variable to another, by minimizing total squared error (OLS) between the fit and the actual data —
no notion of time or causation built in, just "best-fit relationship."

This derivation is one **application** of that general math — specifically, regression used for
*inference* (testing whether `alpha` is real) rather than for prediction, same-day (contemporaneous)
market/strategy returns, not past-predicting-future.

In finance specifically, this exact setup (CAPM alpha/beta) is called a **factor regression** or
**performance-attribution regression**. Same OLS math either way, just a different purpose for
the output.

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

---

### Step 1. Normal equation 1 — `dS/dα = 0` — solve for `α`

```
dS/dα = -2 * Σ(y_t - α - β*x_t) = 0   =>   Σ(y_t - α - β*x_t) = 0
```

Expand and solve directly (using `Σy_t = n*ȳ`, `Σx_t = n*x̄`):

```
α = ȳ - β*x̄
```

---

### Step 2. Normal equation 2 — `dS/dβ = 0` — solve for `β`

```
dS/dβ = -2 * Σ x_t*(y_t - α - β*x_t) = 0   =>   Σ x_t*(y_t - α - β*x_t) = 0
```

Substitute Step 1's `α` in, expand, and simplify (algebra shown in-conversation):

```
β = (Σ x_t*y_t  -  n*x̄*ȳ) / (Σ x_t²  -  n*x̄²)
```

Recognize numerator/denominator as `Cov`/`Var` in disguise (expand `Σ(x_t-x̄)(y_t-ȳ)` and
`Σ(x_t-x̄)²` — they equal the same expressions):

```
β = Cov(x,y) / Var(x)
```

(the `1/n` in `Cov` and `Var`'s own definitions cancels top/bottom, so it never matters here)

---

### Step 3. Now that `α`, `β` are known numbers — compute each residual

```
error_t = y_t - (α + β*x_t)
```

---

### Step 4. Two properties fall out for free (they're just Steps 1 and 2, rearranged)

```
Σ error_t = 0                  (this IS Step 1's equation, unrearranged)
Σ (error_t * x_t) = 0          (this IS Step 2's equation, unrearranged)
```

---

### Step 5. Variance / Covariance definitions (used throughout)

```
Var(X)    = (1/n) * Σ (x_i - mean(X))²
Cov(X,Y)  = (1/n) * Σ (x_i - mean(X)) * (y_i - mean(Y))
```

---

### Step 6. Residual variance — why `n-2`

`S = Σ error_t²` has two exact constraints on it (Step 4) — 2 degrees of freedom consumed by
fitting `α` and `β`. Only `n-2` residuals are truly free, so:

```
Var(error) = (1 / (n-2)) * Σ error_t²
```

---

### Step 7. Rewrite `β` and `ȳ` as weighted sums of the `y_t`'s (needed for Step 9-10)

Start directly from Step 2's `β` formula and isolate `y_t` on its own — numerator and
denominator each need their own simplification.

**Numerator** — substitute `n*x̄*ȳ = x̄*Σy_t = Σ(x̄*y_t)`, then combine and factor:

```
Σx_t*y_t - n*x̄*ȳ  =  Σx_t*y_t - Σ(x̄*y_t)  =  Σ(x_t - x̄)*y_t
```

**Denominator** — prove `Σx_t² - n*x̄² = Σ(x_t-x̄)²` by expanding the right side:

```
Σ(x_t-x̄)² = Σ(x_t² + x̄² - 2*x_t*x̄)
          = Σx_t² + n*x̄² - 2*x̄*Σx_t
          = Σx_t² + n*x̄² - 2*x̄*(n*x̄)
          = Σx_t² + n*x̄² - 2n*x̄²
          = Σx_t² - n*x̄²
```

Combining both (this is the `Sxx = Σ(x_t-x̄)²` notation used from here on):

```
β  = Σ(x_t-x̄)*y_t / Sxx  =  Σ w_t * y_t,     w_t = (x_t - x̄) / Sxx

ȳ  = Σ v_t * y_t,     v_t = 1/n     (no derivation needed — direct from the definition of the mean)
```

Both `β` and `ȳ` are weighted sums of the same underlying `y_t`'s, but with different, distinct
weights — `w_t` varies per `t` (depends on that point's own `x_t`); `v_t` is the same constant
for every `t`.

---

### Step 8. Variance and covariance rules (each provable directly from Step 5's definition)

```
Var(k * B)     = k² * Var(B)                          for constant k

Cov(A, k * B)  = k * Cov(A,B)                          for constant k — same "pull the
                                                        constant out" logic, one power of k
                                                        instead of two, since Cov is only
                                                        linear in each argument, not squared

Var(A + B)     = Var(A) + Var(B) + 2*Cov(A,B)          general case

Var(A + B)     = Var(A) + Var(B)                       simplified — ONLY if Cov(A,B) = 0
```

---

### Step 9. Prove `Cov(ȳ, β) = 0` (using Step 7's weights + independence of the `y_t`'s)

```
Cov(ȳ, β) = (σ²/n) * Σ w_t
          = (σ²/n) * ( Σ(x_t - x̄) / Sxx )
          = (σ²/n) * (0 / Sxx)
          = 0
```

(the same "deviations from a mean sum to zero" fact, reused)

---

### Step 10. Get `Var(ȳ)` and `Var(β)` individually

```
Var(ȳ) = Var( Σ v_t*y_t )
       = Σ v_t² * Var(error)
       = Var(error) / n
```

```
Var(β) = Var( Σ w_t*y_t )
       = Σ w_t² * Var(error)
       = Var(error) * ( Σ(x_t-x̄)² / Sxx² )
       = Var(error) / Sxx
```

---

### Step 11. Combine — general SE at any point `x0`

`SE` is mathematically just `sqrt(variance)` — same operation as standard deviation, just applied
here to an *estimator's* own uncertainty (ȳ, β, ŷ(x0)) rather than to raw data.

Rewrite the fitted line at any point `x0`: `ŷ(x0) = ȳ + β*(x0-x̄)` (substituting Step 1's
`α = ȳ - β*x̄` into `ŷ(x0) = α + β*x0`). Apply Step 8's rules
with Step 9 (cross term = 0) and Step 10 (the two individual variances):

```
Var(ŷ(x0)) = Var(ȳ) + (x0-x̄)² * Var(β)
           = Var(error) * ( 1/n + (x0-x̄)²/Sxx )
```

```
SE(ŷ at x0) = sqrt( Var(error) * ( 1/n + (x0-x̄)²/Sxx ) )
```

---

### Step 12. `SE(α)` — the special case `x0 = 0` (since `α` IS the line's height at `x=0`)

```
SE(α) = sqrt( Var(error) * ( 1/n + x̄²/Sxx ) )
```

---

### Step 13. t-statistic

```
t = α / SE(α)
```

---

### Step 14. p-value

```
p-value = P(|T| > |t|),   T ~ t-distribution,  n-2 degrees of freedom
```

---

## Map back to `52_alpha_beta_formulas.md`

| This file's step | Corresponds to formulas.md step |
|---|---|
| 1, 2 (derivation) | 1, 2 (result only) |
| 3 | 3 |
| 5 | 4 |
| 6 | 5 |
| 7-11 (derivation) | (not shown there — new here) |
| 12 | 6 |
| 13 | 7 |
| 14 | 8 |
