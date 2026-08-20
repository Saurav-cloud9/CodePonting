# Step 52 — Alpha/Beta CAPM regression: formulas only

Testing whether POWERGRID's eta0=2.0 Model C equity curve is genuine skill or just
asset-trend-tracking. No prose, math only, in the order applied.

---

**-1. Excess returns (subtract the risk-free rate first)**

$$
excess\_market\_return_t = market\_return_t - R_{f,t}
$$

$$
excess\_strategy\_return_t = strategy\_return_t - R_{f,t}
$$

$R_f$ = daily risk-free rate (India T-bill/repo proxy). Every `market_return` / `strategy_return`
in steps 0-8 below refers to these EXCESS versions, not raw returns — this is what makes it a true
CAPM-style fit rather than the simplified version used in the toy notebook.

---

**0. Regression model**

$$
excess\_strategy\_return_t = \alpha + \beta \cdot excess\_market\_return_t + error_t
$$

---

**1. Beta (slope)**

$$
\beta = \frac{Cov(excess\_market\_return,\ excess\_strategy\_return)}{Var(excess\_market\_return)}
$$

---

**2. Alpha (intercept)**

$$
\alpha = mean(excess\_strategy\_return) - \beta \cdot mean(excess\_market\_return)
$$

Forces the fitted line through the "point of averages" $(mean(excess\_market\_return), mean(excess\_strategy\_return))$.

---

**3. Residual (per day, computed AFTER fitting — unlike Model C's live error)**

$$
error_t = excess\_strategy\_return_t - \big(\alpha + \beta \cdot excess\_market\_return_t\big)
$$

---

**4. Variance / Covariance (refresher)**

$$
Var(X) = \frac{1}{n}\sum_{i}\big(x_i - mean(X)\big)^2
$$

$$
Cov(X,Y) = \frac{1}{n}\sum_{i}\big(x_i - mean(X)\big)\big(y_i - mean(Y)\big)
$$

$$
Var(X) = Cov(X,X)
$$

For $\beta$ specifically (a ratio), $n$ vs $n-1$ cancels — only matters for a standalone variance/covariance number.

---

**5. Residual variance (n-2 corrected)**

$$
Var(error) = \frac{1}{n-2}\sum_{t}\big(error_t\big)^2
$$

$n-2$, not $n$ or $n-1$ — the alpha+beta fit forces two exact constraints on the residuals:

$$
\sum_t error_t = 0 \qquad \text{(from } dS/d\alpha=0\text{)}
$$

$$
\sum_t \big(error_t \cdot excess\_market\_return_t\big) = 0 \qquad \text{(from } dS/d\beta=0\text{)}
$$

where $S = \sum_t error_t^2$. Two constraints → only $n-2$ residuals are truly free.

---

**6. Standard error of alpha**

$$
SE(\alpha) = \sqrt{\ Var(error) \cdot \left( \frac{1}{n} + \frac{mean(excess\_market\_return)^2}{\sum_t \big(excess\_market\_return_t - mean(excess\_market\_return)\big)^2} \right)\ }
$$

---

**7. t-statistic**

$$
t = \frac{\alpha}{SE(\alpha)}
$$

---

**8. p-value**

$$
p\text{-value} = P\big(|T| > |t|\big),\quad T \sim t\text{-distribution},\ n-2 \text{ degrees of freedom}
$$
