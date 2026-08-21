# Step 52 — Alpha/Beta CAPM regression: full derivation, chronological order [MATH-MODE]

**Note:** standalone math-mode reference. Unlike `52_alpha_beta_formulas.md` (which lists formulas
in APPLICATION order — the order you'd plug numbers into a spreadsheet), this file lists them in
the order they were actually **derived**, each with the calculation shown, not just the result.
Built entirely from this conversation's own step-by-step derivations.

**Regression, in general:** the technique of fitting the best-fit line/curve that relates one
variable to another, by minimizing total squared error (OLS) between the fit and the actual data —
no notion of time or causation built in, just "best-fit relationship."

This derivation is one **application** of that general math — specifically, regression used for
*inference* (testing whether alpha is real) rather than for prediction, same-day (contemporaneous)
market/strategy returns, not past-predicting-future.

In finance specifically, this exact setup (CAPM alpha/beta) is called a **factor regression** or
**performance-attribution regression**. Same OLS math either way, just a different purpose for
the output.

---

**Step 0. Set up the model and the thing to minimize**

$$
excess\_strategy\_return_t = \alpha + \beta \cdot excess\_market\_return_t + error_t
$$

Rearranged: $error_t = y_t - (\alpha + \beta x_t)$ (using $x_t, y_t$ as shorthand from here on).

We want the $\alpha, \beta$ that make the total squared error as small as possible:

$$
S = \sum_t error_t^2 = \sum_t \big(y_t - \alpha - \beta x_t\big)^2
$$

---

**Step 1. Normal equation 1 — $dS/d\alpha = 0$ — solve for $\alpha$**

$$
\frac{dS}{d\alpha} = -2\sum_t(y_t - \alpha - \beta x_t) = 0 \;\Rightarrow\; \sum_t(y_t-\alpha-\beta x_t)=0
$$

Expand and solve directly (using $\sum y_t = n \cdot \bar{y}$, $\sum x_t = n \cdot \bar{x}$):

$$
\boxed{\alpha = \bar{y} - \beta \bar{x}}
$$

---

**Step 2. Normal equation 2 — $dS/d\beta = 0$ — solve for $\beta$**

$$
\frac{dS}{d\beta} = -2\sum_t x_t(y_t - \alpha - \beta x_t) = 0 \;\Rightarrow\; \sum_t x_t(y_t-\alpha-\beta x_t)=0
$$

Substitute Step 1's $\alpha$ in, expand, and simplify (algebra shown in-conversation):

$$
\beta = \frac{\sum_t x_t y_t - n\bar{x}\bar{y}}{\sum_t x_t^2 - n\bar{x}^2}
$$

Recognize numerator/denominator as $Cov$/$Var$ in disguise (expand $\sum(x_t-\bar x)(y_t-\bar y)$
and $\sum(x_t-\bar x)^2$ — they equal the same expressions):

$$
\boxed{\beta = \frac{Cov(x,y)}{Var(x)}}
$$

(the $1/n$ in $Cov$ and $Var$'s own definitions cancels top/bottom, so it never matters here)

---

**Step 3. Now that $\alpha,\beta$ are known numbers — compute each residual**

$$
error_t = y_t - (\alpha + \beta x_t)
$$

---

**Step 4. Two properties fall out for free (they're just Steps 1 and 2, rearranged)**

$$
\sum_t error_t = 0 \qquad\text{(this IS Step 1's equation, unrearranged)}
$$

$$
\sum_t (error_t \cdot x_t) = 0 \qquad\text{(this IS Step 2's equation, unrearranged)}
$$

---

**Step 5. Variance / Covariance definitions (used throughout)**

$$
Var(X) = \frac{1}{n}\sum_i(x_i-mean(X))^2 \qquad Cov(X,Y) = \frac{1}{n}\sum_i(x_i-mean(X))(y_i-mean(Y))
$$

---

**Step 6. Residual variance — why $n-2$**

$S = \sum_t error_t^2$ has two exact constraints on it (Step 4) — 2 degrees of freedom consumed by
fitting $\alpha$ and $\beta$. Only $n-2$ residuals are truly free, so:

$$
\boxed{Var(error) = \frac{1}{n-2}\sum_t error_t^2}
$$

---

**Step 7. Rewrite $\beta$ and $\bar y$ as weighted sums of the $y_t$'s (needed for Step 9-10)**

Since $\sum_t(x_t-\bar x)\cdot\bar y = \bar y \cdot \sum_t(x_t - \bar x) = \bar y \cdot 0 = 0$, the
$\bar y$ term drops out of $\beta$'s numerator, leaving:

$$
\beta = \sum_t w_t y_t, \quad w_t = \frac{x_t-\bar x}{S_{xx}}, \quad S_{xx}=\sum_t(x_t-\bar x)^2
\qquad\qquad
\bar y = \sum_t \frac{1}{n} y_t
$$

Both $\beta$ and $\bar y$ are just weighted sums of the same underlying $y_t$'s — different weights.

---

**Step 8. Two variance rules (each provable directly from Step 5's definition)**

$$
Var(k \cdot B) = k^2 \cdot Var(B) \quad\text{for constant } k
\qquad\qquad
Var(A+B) = Var(A)+Var(B) \quad\text{if } Cov(A,B)=0
$$

---

**Step 9. Prove $Cov(\bar y, \beta) = 0$ (using Step 7's weights + independence of the $y_t$'s)**

$$
Cov(\bar y,\beta) = \frac{\sigma^2}{n}\sum_t w_t = \frac{\sigma^2}{n}\cdot\frac{\sum_t(x_t-\bar x)}{S_{xx}} = \frac{\sigma^2}{n}\cdot\frac{0}{S_{xx}} = 0
$$

(the same "deviations from a mean sum to zero" fact, reused)

---

**Step 10. Get $Var(\bar y)$ and $Var(\beta)$ individually**

$$
Var(\bar y) = Var\Big(\sum_t \tfrac{1}{n}y_t\Big) = \sum_t \Big(\tfrac{1}{n}\Big)^2 Var(error) = \frac{Var(error)}{n}
$$

$$
Var(\beta) = Var\Big(\sum_t w_t y_t\Big) = \sum_t w_t^2 \cdot Var(error) = Var(error)\cdot\frac{\sum_t(x_t-\bar x)^2}{S_{xx}^2} = \frac{Var(error)}{S_{xx}}
$$

---

**Step 11. Combine — general SE at any point $x_0$**

Rewrite the fitted line at any point $x_0$: $\hat y(x_0) = \bar y + \beta(x_0-\bar x)$. Apply Step
8's rules with Step 9 (cross term = 0) and Step 10 (the two individual variances):

$$
Var(\hat y(x_0)) = Var(\bar y) + (x_0-\bar x)^2 Var(\beta) = Var(error)\left(\frac{1}{n}+\frac{(x_0-\bar x)^2}{S_{xx}}\right)
$$

$$
\boxed{SE(\hat y \text{ at } x_0) = \sqrt{\ Var(error)\left(\frac{1}{n}+\frac{(x_0-\bar x)^2}{S_{xx}}\right)\ }}
$$

---

**Step 12. $SE(\alpha)$ — the special case $x_0 = 0$ (since $\alpha$ IS the line's height at $x=0$)**

$$
\boxed{SE(\alpha) = \sqrt{\ Var(error)\left(\frac{1}{n}+\frac{\bar x^2}{S_{xx}}\right)\ }}
$$

---

**Step 13. t-statistic**

$$
t = \frac{\alpha}{SE(\alpha)}
$$

---

**Step 14. p-value**

$$
p\text{-value} = P(|T|>|t|), \quad T \sim t\text{-distribution},\ n-2 \text{ degrees of freedom}
$$

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
