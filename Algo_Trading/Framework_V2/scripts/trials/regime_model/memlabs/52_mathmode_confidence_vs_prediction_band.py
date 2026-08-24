"""
Step 52 [MATH-MODE] — standalone comparison: confidence band vs. prediction band, on the SAME
toy dataset used in 52_alpha_beta_concept_and_powergrid.ipynb's Steps 5-6 cell (identical seed,
n, TRUE_ALPHA/BETA, noise), so this is a true apples-to-apples visual comparison.

Confidence band = SE(yhat at x0) = sqrt(Var(error) * (1/n + (x0-xbar)^2/Sxx))
    -> uncertainty about where the TRUE LINE ITSELF sits (what we actually derived, Steps 7-12).

Prediction band = same formula + one extra "+1" term inside the sqrt
    -> uncertainty about where ONE NEW individual data point would land (wider; not derived in
       the main chat/file derivation — built here purely to build visual intuition per Saurav's
       request, does not modify the notebook or any other file).

Standalone script — does NOT touch 52_alpha_beta_concept_and_powergrid.ipynb.
"""
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('dark_background')

# --- Identical toy data setup to the notebook's Part 1 cell ---
rng = np.random.default_rng(7)
n = 15
TRUE_ALPHA = 0.01
TRUE_BETA = 0.6
NOISE_SIGMA = 0.02

market_return = rng.normal(0, 0.03, n)
strategy_return = TRUE_ALPHA + TRUE_BETA * market_return + rng.normal(0, NOISE_SIGMA, n)

# --- Steps 1-2: beta, alpha ---
x_bar = market_return.mean()
y_bar = strategy_return.mean()
cov_xy = np.mean((market_return - x_bar) * (strategy_return - y_bar))
var_x = np.mean((market_return - x_bar) ** 2)
beta = cov_xy / var_x
alpha = y_bar - beta * x_bar

x_line = np.linspace(market_return.min() - 0.01, market_return.max() + 0.01, 100)
y_line = alpha + beta * x_line

# --- Step 3: residuals ---
fitted = alpha + beta * market_return
error = strategy_return - fitted

# --- Steps 5-6: Var(error), Sxx, SE(alpha) ---
var_error = np.sum(error ** 2) / (n - 2)
Sxx = np.sum((market_return - x_bar) ** 2)
se_alpha = np.sqrt(var_error * (1 / n + x_bar ** 2 / Sxx))

# --- Confidence band (derived in this thread) vs. Prediction band (extra "+1" term) ---
se_confidence = np.sqrt(var_error * (1 / n + (x_line - x_bar) ** 2 / Sxx))
se_prediction = np.sqrt(var_error * (1 + 1 / n + (x_line - x_bar) ** 2 / Sxx))

print(f"n = {n}, beta = {beta:.4f} (true {TRUE_BETA}), alpha = {alpha:.4f} (true {TRUE_ALPHA})")
print(f"Var(error) = {var_error:.6f}, SE(alpha) [confidence] = {se_alpha:.4f}")
se_alpha_pred = np.sqrt(var_error * (1 + 1 / n + x_bar ** 2 / Sxx))
print(f"Prediction SE at x0=0                                  = {se_alpha_pred:.4f}  <- wider")

fig, axes = plt.subplots(2, 1, figsize=(8, 10), sharex=True)

# --- Top: confidence band ---
ax = axes[0]
ax.scatter(market_return, strategy_return, color='#4fc3f7', s=60, zorder=3, label='data points')
ax.plot(x_line, y_line, color='#ff8a65', lw=2, label='fitted line')
ax.fill_between(x_line, y_line - se_confidence, y_line + se_confidence, color='#ff8a65', alpha=0.25, label='+/- 1 SE (confidence)')
ax.fill_between(x_line, y_line - 2 * se_confidence, y_line + 2 * se_confidence, color='#ff8a65', alpha=0.12, label='+/- 2 SE (confidence)')
ax.axvline(0, color='gray', lw=0.8, ls='--')
ax.errorbar([0], [alpha], yerr=[se_alpha], fmt='D', color='#ffca28', ecolor='#ffca28',
            capsize=5, zorder=4, label=f'alpha +/- SE(alpha) = {alpha:.4f} +/- {se_alpha:.4f}')
ax.set_ylabel('strategy_return')
ax.set_title('CONFIDENCE band — uncertainty about where the TRUE LINE sits (what we derived)')
ax.legend(fontsize=8, loc='upper left')

# --- Bottom: prediction band (same data, same fitted line, wider band) ---
ax = axes[1]
ax.scatter(market_return, strategy_return, color='#4fc3f7', s=60, zorder=3, label='data points')
ax.plot(x_line, y_line, color='#ff8a65', lw=2, label='fitted line')
ax.fill_between(x_line, y_line - se_prediction, y_line + se_prediction, color='#66bb6a', alpha=0.25, label='+/- 1 SE (prediction)')
ax.fill_between(x_line, y_line - 2 * se_prediction, y_line + 2 * se_prediction, color='#66bb6a', alpha=0.12, label='+/- 2 SE (prediction)')
ax.axvline(0, color='gray', lw=0.8, ls='--')
ax.errorbar([0], [alpha], yerr=[se_alpha_pred], fmt='D', color='#ffca28', ecolor='#ffca28',
            capsize=5, zorder=4, label=f'alpha +/- pred.SE = {alpha:.4f} +/- {se_alpha_pred:.4f}')
ax.set_xlabel('market_return')
ax.set_ylabel('strategy_return')
ax.set_title('PREDICTION band — uncertainty about where ONE NEW point would land (wider, not derived here)')
ax.legend(fontsize=8, loc='upper left')

plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=130)
print(f"Saved: {out_path}")
