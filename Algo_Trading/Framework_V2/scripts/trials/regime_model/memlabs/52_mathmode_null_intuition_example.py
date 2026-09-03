"""
Step 52 [MATH-MODE] — intuition-building example for "failing to reject the null != proving the
null," and why a nonzero sample estimate can still be consistent with a true value of zero.

Simulates MANY independent samples, each drawn from a data-generating process with TRUE_ALPHA
EXACTLY ZERO (genuinely no skill), then shows the distribution of the resulting ESTIMATED alphas
across all those samples — visualizing how often pure noise alone produces a nonzero-looking
estimate, purely by chance, even though the truth behind every single one of them is zero.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

plt.style.use('dark_background')

rng = np.random.default_rng(42)
n_per_sample = 15          # same small sample size as the earlier toy example
n_simulations = 5000       # repeat the whole experiment 5000 times
TRUE_ALPHA = 0.0           # genuinely zero skill, every single time
TRUE_BETA = 0.6
NOISE_SIGMA = 0.02

estimated_alphas = np.zeros(n_simulations)
t_stats = np.zeros(n_simulations)

for i in range(n_simulations):
    market_return = rng.normal(0, 0.03, n_per_sample)
    strategy_return = TRUE_ALPHA + TRUE_BETA * market_return + rng.normal(0, NOISE_SIGMA, n_per_sample)

    x_bar = market_return.mean(); y_bar = strategy_return.mean()
    cov_xy = np.mean((market_return - x_bar) * (strategy_return - y_bar))
    var_x = np.mean((market_return - x_bar) ** 2)
    beta = cov_xy / var_x
    alpha = y_bar - beta * x_bar

    fitted = alpha + beta * market_return
    error = strategy_return - fitted
    var_error = np.sum(error ** 2) / (n_per_sample - 2)
    Sxx = np.sum((market_return - x_bar) ** 2)
    se_alpha = np.sqrt(var_error * (1/n_per_sample + x_bar**2 / Sxx))

    estimated_alphas[i] = alpha
    t_stats[i] = alpha / se_alpha if se_alpha > 0 else 0

pct_beyond_005 = np.mean(np.abs(estimated_alphas) > 0.005) * 100
pct_beyond_010 = np.mean(np.abs(estimated_alphas) > 0.010) * 100
pct_wrong_sign_and_notable = np.mean(estimated_alphas < -0.005) * 100

print(f"n_simulations = {n_simulations}, each with n={n_per_sample} data points, TRUE_ALPHA=0 every time")
print(f"estimated alpha: mean={estimated_alphas.mean():.5f}  std={estimated_alphas.std():.5f}")
print(f"% of samples with |estimated alpha| > 0.005: {pct_beyond_005:.1f}%")
print(f"% of samples with |estimated alpha| > 0.010: {pct_beyond_010:.1f}%")
print(f"% of samples with estimated alpha < -0.005 (looks like a real negative effect): {pct_wrong_sign_and_notable:.1f}%")

fig, axes = plt.subplots(3, 1, figsize=(9, 13))

axes[0].hist(estimated_alphas, bins=80, color='#4fc3f7', edgecolor='none', alpha=0.85)
axes[0].axvline(0, color='#ffca28', lw=2, label='TRUE alpha (always exactly 0)')
axes[0].axvline(-0.0041, color='#ff6b6b', lw=1.5, ls='--', label='our earlier toy example\'s estimate (-0.0041)')
axes[0].set_title(f'Distribution of ESTIMATED alpha across {n_simulations} samples — TRUE alpha is 0 in EVERY one')
axes[0].set_xlabel('estimated alpha (alpha-hat)')
axes[0].set_ylabel('count')
axes[0].legend(fontsize=8)

axes[1].hist(t_stats, bins=80, color='#66bb6a', edgecolor='none', alpha=0.85)
axes[1].axvline(0, color='#ffca28', lw=2)
axes[1].axvline(2, color='#ff6b6b', lw=1, ls='--', label='|t|~2 (common "looks significant" threshold)')
axes[1].axvline(-2, color='#ff6b6b', lw=1, ls='--')
axes[1].set_title('Distribution of the resulting t-statistic (this IS the null-hypothesis t-distribution)')
axes[1].set_xlabel('t-statistic')
axes[1].set_ylabel('count')
axes[1].legend(fontsize=8)

axes[2].hist(t_stats, bins=80, color='#66bb6a', edgecolor='none', alpha=0.6, density=True,
             label='our 5000 simulated t-statistics (density-scaled)')
t_range = np.linspace(t_stats.min(), t_stats.max(), 300)
theoretical_pdf = stats.t.pdf(t_range, df=n_per_sample - 2)
axes[2].plot(t_range, theoretical_pdf, color='#ffca28', lw=2.5,
             label=f'theoretical t-distribution PDF (df=n-2={n_per_sample-2})')
axes[2].set_title('Density-scaled t-statistic histogram vs. the actual theoretical t-distribution curve')
axes[2].set_xlabel('t-statistic')
axes[2].set_ylabel('probability density')
axes[2].legend(fontsize=8)

plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=130)
print(f"\nSaved: {out_path}")
