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

The simplified rule is only legally usable once `Cov(A,B)=0` is proven for the specific `A`, `B`
in question — that's exactly Step 9's job below. The `Cov(A,k*B)` rule is what Step 11 needs to
correctly expand a cross term like `Cov(ȳ, β*(x0-x̄))` into `(x0-x̄)*Cov(ȳ,β)`, before the
zero-cross-term simplification can even apply.

---

### Step 9. Prove `Cov(ȳ, β) = 0` (using Step 7's weights + independence of the `y_t`'s)

**Why the standard sample Cov formula can't be used here:** `Cov(X,Y) = (1/n)*Σ(x_i-x̄)(y_i-ȳ)`
needs multiple *paired* observations of the two variables to average over. We only have ONE `ȳ`
and ONE `β`, computed once from this one dataset — no repeated (ȳ,β) pairs exist to plug into
that formula. So this proof uses the population/theoretical Cov definition instead, applied via
covariance's bilinearity property.

**Substitute `X=ȳ=Σv_t*y_t` and `Y=β=Σw_t*y_t` into `Cov(X,Y) = E[(X-E[X])(Y-E[Y])]`:**

```
Cov(ȳ,β) = E[ (Σv_t*y_t - E[Σv_t*y_t]) * (Σw_t*y_t - E[Σw_t*y_t]) ]
```

Simplify each inner `E[·]` term using expectation's linearity (E distributes over a sum; a
non-random constant like `v_t`/`w_t` — non-random because `x_t` is treated as fixed in this
model, only `y_t` carries randomness via `error_t` — factors out of each E[·]):

```
E[Σv_t*y_t] = Σv_t*E[y_t]          E[Σw_t*y_t] = Σw_t*E[y_t]
```

Substitute back in, then factor the weight back out of each subtraction
(`Σv_t*y_t - Σv_t*E[y_t] = Σv_t*(y_t-E[y_t])`):

```
Cov(ȳ,β) = E[ (Σv_t*(y_t-E[y_t])) * (Σw_t*(y_t-E[y_t])) ]
```

**Relabel the second sum's index from `t` to `s` before multiplying** — required because
multiplying two sums together needs two independent indices to represent every possible pairing;
reusing the same letter for both would only capture the `t=s` matches, silently dropping every
`t≠s` cross-term. Let `d_t = y_t-E[y_t]`, `d_s = y_s-E[y_s]`:

```
Cov(ȳ,β) = E[ (Σv_t*d_t) * (Σw_s*d_s) ]
```

Multiplying two separate sums together expands into a double sum over every (t,s) pair
(`(Σa_t)*(Σb_s) = ΣΣa_t*b_s`):

```
= E[ ΣΣ v_t*d_t*w_s*d_s ]
```

Distribute `E[·]` over the double sum, then recognize `E[d_t*d_s] = E[(y_t-E[y_t])(y_s-E[y_s])]`
is exactly `Cov(y_t,y_s)` by definition:

```
= ΣΣ v_t*w_s*E[d_t*d_s]  =  ΣΣ v_t*w_s*Cov(y_t,y_s)
```

**Collapse the double sum via independence.** The model assumes each data point's noise is
independent of every other's: `Cov(y_t,y_s)=0` whenever `t≠s` (the off-diagonal pairs — most of
the grid — all vanish to exactly zero, regardless of `n`). Only the diagonal (`t=s`) pairs
survive, where `Cov(y_t,y_t)=Var(y_t)=σ²` (constant noise level across all t):

```
ΣΣ v_t*w_s*Cov(y_t,y_s)  =  Σ v_t*w_t*σ²          (n² terms collapse down to n surviving terms)
```

Substitute `v_t=1/n`, factor the constant `σ²/n` out of the sum, then substitute `w_t`'s
definition:

```
= Σ (1/n)*w_t*σ²  =  (σ²/n)*Σw_t  =  (σ²/n)*Σ[(x_t-x̄)/Sxx]
```

`Σ(x_t-x̄)=0` always (deviations from a mean sum to zero — from `x̄=(1/n)Σx_t` rearranged,
already used in Steps 1 and 7), so `Σw_t = (1/Sxx)*Σ(x_t-x̄) = 0` too — a structural fact, true
for any dataset, since it's baked into `w_t`'s own definition:

```
Cov(ȳ,β) = (σ²/n) * 0 = 0
```

**What this means, theoretically:** the uncertainty in estimating the line's overall level (ȳ)
and the uncertainty in estimating its slope (β) are completely unrelated — an unusually high or
low `ȳ` in one hypothetical resample tells you nothing about whether that same sample's `β` came
out unusually high or low too. That's exactly why Step 11 can use Step 8's simplified addition
rule (no cross-term correction needed) when combining `Var(ȳ)` and `Var(β)`.

---

### Step 10. Get `Var(ȳ)` and `Var(β)` individually

Since `Var(X) = Cov(X,X)` (variance is just covariance of something with itself), both derivations
reuse Step 9's exact double-sum machinery — substitute the SAME weighted sum for both sides,
relabel one occurrence's index, expand, then collapse via independence.

**`Var(ȳ)` — full chain, starting from the `Var(X)=Cov(X,X)` identity itself:**

```
Var(ȳ) = Cov(X,X)                                        (X = ȳ)
       = E[(X-E[X])(X-E[X])]                              (substitute Y=X into Cov's definition)
       = E[(X-E[X])²]                                     (same factor twice = squared)
```

Substitute `X = ȳ = Σv_t*y_t`:

```
= E[(Σv_t*y_t - E[Σv_t*y_t])²]
```

Simplify the inner `E[·]` (linearity: distribute over the sum, pull the non-random constant `v_t`
out), then factor `v_t` back out of the subtraction:

```
= E[(Σv_t*y_t - Σv_t*E[y_t])²]  =  E[(Σv_t*(y_t-E[y_t]))²]
```

Substituting `d_t = y_t-E[y_t]`:

```
= E[(Σv_t*d_t)²]
```

Squaring a sum is the same operation as multiplying that sum by itself — needs the same
relabel-then-double-sum move as Step 9 (a single reused index can't represent every possible
pairing; `(Σa_t)² ≠ Σa_t²` — this is the same missing-cross-terms trap as `(a+b)² ≠ a²+b²`).
Relabel one copy's index to `s`:

```
= E[(Σv_t*d_t)*(Σv_s*d_s)]  =  E[ΣΣ v_t*d_t*v_s*d_s]
```

Distribute `E[·]` over the double sum, pull out the non-random `v_t`,`v_s`, then recognize
`E[d_t*d_s] = Cov(y_t,y_s)` by definition:

```
= ΣΣ v_t*v_s*E[d_t*d_s]  =  ΣΣ v_t*v_s*Cov(y_t,y_s)
```

**Now apply independence** — off-diagonal (`t≠s`) terms vanish to 0; only the diagonal (`t=s`)
survives, forcing `s→t`:

```
Var(ȳ) = Σ v_t*v_t*Cov(y_t,y_t)     =  Σ v_t²*Var(y_t)     (v_t*v_t=v_t²; Cov(y_t,y_t)=Var(y_t))
       = Σ (1/n)²*σ²                                          (substituting v_t=1/n, Var(y_t)=σ²)
       = (1/n)²*n*σ²                                           (n identical terms summed)
       = σ²/n
```

**`Var(β)`:** identical route, substituting `w_t` for `v_t` throughout (same `Cov(X,X)` start,
same `E[·]` substitution, same relabel-to-`s`, same double-sum, same independence collapse — not
re-shown line by line since it's a direct swap). One extra care point at the final substitution:
`Sxx²` and `σ²` are constants (don't depend on `t`) and must be factored OUT of the sum *before*
substituting the total identity `Σ(x_t-x̄)²=Sxx` — substituting a per-t term with a grand total
while it's still inside the Σ is invalid (the same error as claiming each individual `x_t` equals
`n*x̄` just because `Σx_t=n*x̄`).

```
Var(β) = Cov(β,β) = Σ w_t*w_t*Cov(y_t,y_t) = Σ w_t²*Var(y_t) = Σ w_t²*σ²
       = Σ [(x_t-x̄)/Sxx]² * σ²
       = Σ [(x_t-x̄)²/Sxx²] * σ²
       = (σ²/Sxx²) * Σ(x_t-x̄)²          (factor the constants Sxx², σ² out of the sum FIRST)
       = (σ²/Sxx²) * Sxx                 (NOW substitute — the full sum equals Sxx)
       = σ²/Sxx
```

**Summary — understanding checkpoint for Steps 9-10:**

- `σ²` (true population noise level) is a notational substitution, not a separately derived
  fact — `σ` is *defined* as `sqrt(Var(y_t))`, so `Var(y_t)=σ²` follows immediately by squaring.
  `Var(y_t)=σ²` for every `t` specifically because of the model's homoscedasticity assumption
  (constant noise level across all data points, not a function of `t` or `x_t`).
- `Var(y_t)` is not the residual/error itself — it's a *summary statistic* describing the error's
  typical squared size (`Var(y_t)=Var(error_t)=E[error_t²]`), not any one realized error value.
- `n` never disappears in these collapses — it resurfaces explicitly: once as "how many diagonal
  terms survive" (n of them, out of n² total pairs), and again inside `v_t=1/n` itself; the two
  combine (`n * (1/n)² = 1/n`) to leave a single `n` in the final denominator.
- `Cov(y_t,y_t)=Var(y_t)` (t=s case) is true unconditionally, by definition — independence is
  NOT what causes this. Independence is only responsible for the *other* fact: `Cov(y_t,y_s)=0`
  when `t≠s` — the off-diagonal terms vanishing is the actual collapse; the diagonal identity was
  always true regardless.
- Both results (`Var(ȳ)=σ²/n`, `Var(β)=σ²/Sxx`) feed directly into Step 11's combination.

---

### Step 11. Combine — general SE at any point `x0`

`SE` is mathematically just `sqrt(variance)` — same operation as standard deviation, just applied
here to an *estimator's* own uncertainty (ȳ, β, ŷ(x0)) rather than to raw data.

**Rewrite the fitted line at any point `x0`**, substituting Step 1's `α = ȳ - β*x̄` into
`ŷ(x0) = α + β*x0`:

```
ŷ(x0) = (ȳ - β*x̄) + β*x0  =  ȳ - β*x̄ + β*x0  =  ȳ + β*(x0 - x̄)
```

(careful with the sign here — combining the two `β` terms gives `+β*(x0-x̄)`, not minus; a common
slip is writing `β*(x̄-x0)`, which is the negative of the correct form)

**Apply `Var(·)` to both sides**, treating this as `A+B` with `A=ȳ`, `B=β*(x0-x̄)` — note `B` is a
*constant* (`x0-x̄`) multiplying `β`, not `β` alone, so both of Step 8's rules are needed:

```
Var(ŷ(x0)) = Var(ȳ) + Var(β*(x0-x̄)) + 2*Cov(ȳ, β*(x0-x̄))
```

Pull the constant `(x0-x̄)` out of the middle term (`Var(k*B)=k²*Var(B)`) and out of the cross
term (`Cov(A,k*B)=k*Cov(A,B)`):

```
Var(ŷ(x0)) = Var(ȳ) + (x0-x̄)²*Var(β) + 2*(x0-x̄)*Cov(ȳ,β)
```

**`Cov(ȳ,β)=0`** (Step 9) — the cross term vanishes entirely:

```
Var(ŷ(x0)) = Var(ȳ) + (x0-x̄)²*Var(β)
```

**Substitute Step 10's results** (`Var(ȳ)=Var(error)/n`, `Var(β)=Var(error)/Sxx` — using
`Var(error)` as the practical, computable stand-in for the theoretical `σ²`):

```
Var(ŷ(x0)) = Var(error)/n + (x0-x̄)²*Var(error)/Sxx  =  Var(error) * ( 1/n + (x0-x̄)²/Sxx )
```

**Square root to get `SE`:**

```
SE(ŷ at x0) = sqrt( Var(error) * ( 1/n + (x0-x̄)²/Sxx ) )
```

---

### Step 12. `SE(α)` — the special case `x0 = 0` (since `α` IS the line's height at `x=0`)

Plug `x0=0` directly into Step 11's general formula — `α` is literally `ŷ(0)` (Step 0's model
structure guarantees this, since `β*0=0` makes the `β` term vanish regardless of `β`'s value):

```
SE(α) = sqrt( Var(error) * ( 1/n + x̄²/Sxx ) )
```

---

### Step 13. t-statistic

```
t = α / SE(α)
```

A ratio of the estimated `α` to its own uncertainty — mechanically identical in form to a
signal-to-noise ratio.

---

### Step 14. p-value

```
p-value = P(|T| > |t|),   T ~ t-distribution,  n-2 degrees of freedom
```

**`T` vs `t` — an important distinction.** `T` (capital) is a *random variable* — the whole range
of possible t-ratios `α̂/SE(α̂)` you'd get across many hypothetical resamples, **assuming the null
hypothesis is true** (true `α_true = 0`). `t` (lowercase) is the *one specific number* actually
computed from real data. `T`'s formula still uses the *estimated* `α̂` (which fluctuates around
zero across noisy resamples even when the true `α` is exactly 0) — not the *true* `α`, which the
null hypothesis fixes at zero throughout.

`P(|T|>|t|)` asks: "what fraction of `T`'s possible outcomes, under the null, are at least as
extreme (far from zero) as our one observed `|t|`?" That fraction is the p-value — the area under
the t-distribution's curve beyond `±|t|` (both tails). A small p-value means our result would be
rare under pure noise — evidence *against* the null, not proof the null is false (statistical
significance is a probabilistic standard of evidence, not certainty — there's always a real,
quantified chance, conventionally 5%, of a false positive even when the test correctly passes).

**Plain-English recap — how to read a p-value, step by step** *(added 2026-08-28 at Saurav's
request, fv2 session, while walking through Part 2's real-data result):*

1. Start by *assuming* the null hypothesis is true: `α_true = 0`, and the only reason `α̂` isn't
   exactly 0 is random noise in the sample.
2. Under that assumption, ask: "what's the probability of getting an `α̂` (equivalently, a `|t|`)
   this far from zero, purely by chance?" — that probability is the p-value.
3. "This far from zero" (`|T| > |t|`) means *at least as extreme in either direction* — a large
   negative `α̂` counts as equally extreme as a large positive one of the same size, since the null
   only claims `α=0`, not a direction.
4. **If p is small (< 5%):** noise alone would rarely produce a result this extreme → the
   noise-only story is implausible → reject the null → there's probably a real, nonzero `α_true`
   driving it. This is an *indication*, not a guarantee, and it says nothing about the *size* of
   `α_true` — only that it's probably not zero. The actual magnitude still carries its own
   uncertainty band (the confidence interval, `α̂ ± ~1.96×SE(α̂)` at large `n` — same 1.96 cutoff
   because it's the same two-tailed 5% boundary on the same t-distribution).
5. **If p is large (as in our real result, p=0.3905):** this does *not* prove `α_true = 0` —
   it means the data isn't strong enough evidence either way. "Failing to reject the null" and
   "proving the null" are different claims; here it means the observed outperformance is not
   distinguishable from what pure noise around a true alpha of zero would produce.

---

*(Derivation complete — Steps 0-14. Applied to real data for the first time in
`52_alpha_beta_concept_and_powergrid.ipynb`'s Part 2: POWERGRID eta0=2.0 Model C, n=2808 real
trading days. Result: alpha NOT statistically significant, p=0.3905 — see that notebook and
PROGRESS_HISTORY.md's 2026-08-27 entry for the full real-data writeup.)*
