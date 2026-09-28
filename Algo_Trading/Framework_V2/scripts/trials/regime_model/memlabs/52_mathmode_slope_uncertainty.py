"""
Step 52 [MATH-MODE] — isolating SLOPE uncertainty (SE(b1)), companion to
52_mathmode_confidence_vs_prediction_band.py.

That script's confidence band combines two sources of uncertainty: the ybar term
(1/n) and the slope term ((x0-xbar)^2/Sxx, the part that makes the band flare wider
away from xbar). This script isolates the slope term alone: refit OLS on 2,000 fresh
datasets (SAME x-values every time, only the noise redrawn) and look directly at how
much b1 itself varies.

Standalone script — does NOT touch 52_alpha_beta_concept_and_powergrid.ipynb, or any
#54/#55 file.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

plt.style.use('dark_background')

# --- Identical toy setup to 52_mathmode_confidence_vs_prediction_band.py ---
rng = np.random.default_rng(7)
n = 15
TRUE_ALPHA = 0.01
TRUE_BETA = 0.6
NOISE_SIGMA = 0.02

# x generated ONCE, held fixed across every simulation -- SE(b1)=sigma/sqrt(Sxx) is
# conditional on the design (the x-values), so a fixed design is what makes the
# empirical spread of b1 comparable to the formula.
x = rng.normal(0, 0.03, n)
x_bar = x.mean()
Sxx = np.sum((x - x_bar) ** 2)

# --- 2,000 refits, fresh noise each time, x held fixed ---
N_SIM = 2000
b1_samples = np.empty(N_SIM)
se_b1_samples = np.empty(N_SIM)
lines_b0b1 = []

for i in range(N_SIM):
    noise = rng.normal(0, NOISE_SIGMA, n)
    y = TRUE_ALPHA + TRUE_BETA * x + noise
    y_bar = y.mean()
    Sxy = np.sum((x - x_bar) * (y - y_bar))
    b1 = Sxy / Sxx
    b0 = y_bar - b1 * x_bar
    yhat = b0 + b1 * x
    e = y - yhat
    sigma2_hat = np.sum(e ** 2) / (n - 2)
    se_b1 = np.sqrt(sigma2_hat / Sxx)

    b1_samples[i] = b1
    se_b1_samples[i] = se_b1
    if i < 150:
        lines_b0b1.append((b0, b1))

empirical_std_b1 = b1_samples.std(ddof=1)
theoretical_se = NOISE_SIGMA / np.sqrt(Sxx)
mean_estimated_se = se_b1_samples.mean()
mean_b1 = b1_samples.mean()

print(f"x_bar = {x_bar:.5f}, Sxx = {Sxx:.6f}")
print(f"mean of 2,000 b1 values      = {mean_b1:.4f}  (true beta = {TRUE_BETA})")
print(f"(a) empirical std of b1      = {empirical_std_b1:.5f}")
print(f"(b) theoretical SE = sigma/sqrt(Sxx) = {theoretical_se:.5f}")
print(f"(c) mean of per-run estimated SE(b1) = {mean_estimated_se:.5f}")
gap_pct = (theoretical_se - mean_estimated_se) / theoretical_se * 100
print(f"    gap (b vs c): {gap_pct:.2f}% -- expected direction is (c) slightly BELOW "
      f"(b) (Jensen's inequality on sqrt of sigma2_hat), flag only if this is large.")

# --- Figure: 2 panels ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel 1: spaghetti plot
ax = axes[0]
x_line = np.linspace(x.min() - 0.01, x.max() + 0.01, 100)
for b0, b1 in lines_b0b1:
    ax.plot(x_line, b0 + b1 * x_line, color='#4fc3f7', alpha=0.12, linewidth=0.6)
ax.plot(x_line, TRUE_ALPHA + TRUE_BETA * x_line, color='#ff8a65', linewidth=3,
        label=f'TRUE line (beta={TRUE_BETA})', zorder=5)
pivot_y = TRUE_ALPHA + TRUE_BETA * x_bar
ax.scatter([x_bar], [pivot_y], color='#ffca28', marker='D', s=100, zorder=6,
           label=f'pivot (x_bar, alpha+beta*x_bar)')
ax.axhline(0, color='gray', lw=0.6, ls='--')
ax.set_xlabel('market_return (x)'); ax.set_ylabel('strategy_return (y)')
ax.set_title(f'Slope uncertainty: {len(lines_b0b1)} refits rotate around (x_bar, y_bar)')
ax.legend(fontsize=9, loc='upper left')

# Panel 2: histogram of b1 with theoretical normal overlay
ax = axes[1]
ax.hist(b1_samples, bins=50, density=True, color='#66bb6a', alpha=0.65, label='2,000 fitted b1 values')
ax.axvline(TRUE_BETA, color='#ff8a65', linewidth=2, label=f'TRUE beta = {TRUE_BETA}')
xs = np.linspace(b1_samples.min(), b1_samples.max(), 300)
ax.plot(xs, stats.norm.pdf(xs, TRUE_BETA, theoretical_se), color='#ffca28', linewidth=2,
        label=f'N(beta, sigma/sqrt(Sxx))')
ax.set_xlabel('b1 (fitted slope)'); ax.set_ylabel('density')
ax.set_title('Distribution of fitted slopes across 2,000 refits')
ax.legend(fontsize=9, loc='upper left')
ax.text(0.02, 0.70,
        f"(a) empirical std(b1)      = {empirical_std_b1:.5f}\n"
        f"(b) theoretical SE=sigma/sqrt(Sxx) = {theoretical_se:.5f}\n"
        f"(c) mean per-run est. SE(b1) = {mean_estimated_se:.5f}",
        transform=ax.transAxes, fontsize=9, color='white',
        bbox=dict(facecolor='black', alpha=0.6, edgecolor='#66bb6a'))

plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=130)
print(f"Saved: {out_path}")
