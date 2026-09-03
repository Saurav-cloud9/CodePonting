"""
Step 52 -- toy/dummy illustration (not real data) of an XOR-style interaction effect: a case
where each individual feature's correlation with the outcome is ~0, yet the outcome is PERFECTLY
separable once both features are viewed together.

Rule used to label each dummy point:
    buy (+1)  when x1 and x2 have the SAME sign   (both quadrant 1 or both quadrant 3)
    sell(-1)  when x1 and x2 have OPPOSITE signs  (quadrant 2 or quadrant 4)

Built at Saurav's request while discussing why 32_model_b_actual_direction_only.py's near-zero
individual feature correlations don't, on their own, rule out a combination/interaction effect --
this is the general-principle toy example, separate from the real Model B data.
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

plt.style.use('dark_background')

rng = np.random.default_rng(42)
n = 400
x1 = rng.uniform(-3, 3, n)
x2 = rng.uniform(-3, 3, n)
buy = (np.sign(x1) == np.sign(x2))   # same sign -> buy, opposite sign -> sell

corr_x1 = np.corrcoef(x1, buy.astype(float))[0, 1]
corr_x2 = np.corrcoef(x2, buy.astype(float))[0, 1]
print(f"corr(x1, buy) = {corr_x1:.4f}   corr(x2, buy) = {corr_x2:.4f}   (both ~0, by construction)")

# --- Hypothetical fitted line: what a straight-line (linear) model would produce ---
# Fit buy(0/1) ~ a + b1*x1 + b2*x2 by OLS, then draw its y_hat=0.5 boundary -- same recipe as
# Model B's y_hat=0 boundary in 32_model_b_actual_direction_quadrant.png.
lin_model = LinearRegression()
lin_model.fit(np.column_stack([x1, x2]), buy.astype(float))
b1, b2 = lin_model.coef_
a = lin_model.intercept_
print(f"fitted line: a={a:.4f}, b1={b1:.4f}, b2={b2:.4f}")

fit_x1 = np.linspace(x1.min(), x1.max(), 200)
fit_x2 = (0.5 - a - b1 * fit_x1) / b2
mask_fit = (fit_x2 >= x2.min()) & (fit_x2 <= x2.max())

COLOR_BUY = '#2ecc71'
COLOR_SELL = '#e74c3c'

fig, ax = plt.subplots(figsize=(8, 8))

ax.scatter(x1[buy], x2[buy], color=COLOR_BUY, s=22, label=f'buy (same sign, n={buy.sum()})', alpha=0.85)
ax.scatter(x1[~buy], x2[~buy], color=COLOR_SELL, s=22, label=f'sell (opposite sign, n={(~buy).sum()})', alpha=0.85)

ax.plot(fit_x1[mask_fit], fit_x2[mask_fit], color='#5b9bd5', linewidth=2.5,
        label='hypothetical fitted line (straight-line model, y_hat=0.5)')

ax.axhline(0, color='white', linewidth=1, linestyle='--', alpha=0.6)
ax.axvline(0, color='white', linewidth=1, linestyle='--', alpha=0.6)

ax.set_xlim(-4, 4)
ax.set_ylim(-4, 4)

# Quadrant labels
ax.text(2.0, 3.6, 'Q1: buy', color=COLOR_BUY, fontsize=11, ha='center', weight='bold')
ax.text(-2.0, 3.6, 'Q2: sell', color=COLOR_SELL, fontsize=11, ha='center', weight='bold')
ax.text(-2.0, -3.8, 'Q3: buy', color=COLOR_BUY, fontsize=11, ha='center', weight='bold')
ax.text(2.0, -3.8, 'Q4: sell', color=COLOR_SELL, fontsize=11, ha='center', weight='bold')

ax.set_xlabel('x1')
ax.set_ylabel('x2')
ax.set_title(f"Interaction effect (XOR pattern): individual correlations ~0, but perfectly\n"
             f"separable once both features are viewed together — corr(x1,buy)={corr_x1:.3f}, "
             f"corr(x2,buy)={corr_x2:.3f}", fontsize=11)
ax.legend(loc='upper right', fontsize=9)
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/52_mathmode_xor_interaction_quadrant_example.png', dpi=130)
print('Saved 52_mathmode_xor_interaction_quadrant_example.png')
