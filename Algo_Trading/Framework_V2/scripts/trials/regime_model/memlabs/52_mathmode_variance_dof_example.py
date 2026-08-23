"""
Step 52 [MATH-MODE] — standalone dummy example illustrating Var(error) and the n-2
degrees-of-freedom correction, using the same 10-residual example worked through in chat
(8 freely chosen residuals + 2 forced by the Sigma-error_t=0 and Sigma-error_t*x_t=0
constraints). No trading data — same toy numbers used in conversation.
"""
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('dark_background')

# The 10 residuals from the worked example: e_1..e_8 freely chosen, e_9/e_10 forced
residuals = np.array([1, -2, 3, -1, 0, 2, -3, 1, -9, 8])
n = len(residuals)
free_mask = np.array([True]*8 + [False]*2)  # first 8 free, last 2 forced

squared = residuals ** 2
sum_sq = squared.sum()
var_n = sum_sq / n            # naive divisor (biased, what we'd get ignoring dof loss)
var_n2 = sum_sq / (n - 2)     # correct divisor (Step 6's Var(error))

fig, axes = plt.subplots(2, 1, figsize=(9, 8))

# --- Top panel: raw residuals, free vs forced ---
colors = ['#4fc3f7' if f else '#ff6b6b' for f in free_mask]
axes[0].bar(range(1, n+1), residuals, color=colors, edgecolor='white', linewidth=0.5)
axes[0].axhline(0, color='white', linewidth=1)
axes[0].set_title('10 residuals: 8 freely chosen (blue) + 2 forced by the constraints (red)')
axes[0].set_xlabel('t')
axes[0].set_ylabel('error_t')
axes[0].set_xticks(range(1, n+1))

# --- Bottom panel: squared residuals + the two variance divisors ---
axes[1].bar(range(1, n+1), squared, color=colors, edgecolor='white', linewidth=0.5)
axes[1].axhline(var_n, color='#ffd54f', linestyle='--', linewidth=1.5,
                 label=f'Var using n=10 divisor  =  {sum_sq:.0f}/10  =  {var_n:.2f}')
axes[1].axhline(var_n2, color='#81c784', linestyle='--', linewidth=1.5,
                 label=f'Var using n-2=8 divisor  =  {sum_sq:.0f}/8  =  {var_n2:.2f}  (Step 6, correct)')
axes[1].set_title(f'Squared residuals (Sigma error_t^2 = {sum_sq:.0f}) — two candidate variance estimates')
axes[1].set_xlabel('t')
axes[1].set_ylabel('error_t^2')
axes[1].set_xticks(range(1, n+1))
axes[1].legend(loc='upper left', fontsize=9)

plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
print(f"Sigma error_t    = {residuals.sum()}  (constraint check, should be 0)")
print(f"Sigma error_t^2  = {sum_sq}")
print(f"Var (n=10)       = {var_n:.4f}")
print(f"Var (n-2=8)      = {var_n2:.4f}  <- Step 6's formula, larger & unbiased")
