# Step 50 — Model C: formulas only

Passive-Aggressive online learning (`SGDRegressor`, `loss="epsilon_insensitive"`,
`learning_rate="pa1"`), one tick at a time. No prose, math only, in the order applied per tick.

---

**1. Feature scaling (running, incremental)**

$$
x_{scaled} = \frac{x - \mu_{running}}{\sigma_{running}}
$$

---

**2. Prediction (using pre-update weights)**

$$
\hat{y} = w \cdot x_{scaled} + b
$$

---

**3. Error**

$$
error = y - \hat{y}
$$

---

**4. Loss (epsilon-insensitive)**

$$
loss = \max(0,\ |error| - \epsilon)
$$

$$
loss = 0 \implies \text{passive (no update)} \qquad loss > 0 \implies \text{aggressive (update)}
$$

---

**5. Step size (PA-I cap)**

$$
\tau = \min\left(\eta_0,\ \frac{loss}{\lVert x_{scaled} \rVert^2}\right)
$$

---

**6. Weight update**

$$
w_{new} = w_{old} + \tau \cdot \operatorname{sign}(error) \cdot x_{scaled}
$$

---

**7. Bias update**

$$
b_{new} = b_{old} + \tau \cdot \operatorname{sign}(error) \cdot 1
$$

---

**Initial condition (tick 0)**

$$
w_0 = 0, \qquad b_0 = 0
$$

---

**5b. Step size — PA-II variant (`learning_rate="pa2"`)**

Replaces step 5 above when using `pa2` instead of `pa1`. No hard cap — `eta0` softens the
denominator instead:

$$
\tau = \frac{loss}{\lVert x_{scaled} \rVert^2 + \dfrac{1}{2\eta_0}}
$$

Steps 6–7 (weight/bias update) are unchanged, using this τ instead.
