"""
Step 52 — the "normal equations" geometric interpretation: OLS as orthogonal projection.

Toy n=3 example (small enough to actually draw in 3D). Shows:
  - the 1's-vector and x-vector spanning a flat plane through the origin
  - y as a point off that plane
  - y_hat (= alpha_hat*ones + beta_hat*x) as y's orthogonal projection ONTO the plane
  - the residual vector (y - y_hat) drawn perpendicular to the plane

This is the SAME two equations as Steps 1-2 (sum(error)=0, sum(error*x)=0), just viewed as
vector dot-products (= 0) instead of calculus derivatives (= 0). "Normal" = perpendicular here,
unrelated to "normal distribution." Built at Saurav's request, fv2 session, while tracing why
the normal equations are named that.
"""
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('dark_background')

# --- Toy n=3 dataset (small enough to live in 3D and be drawn) ---
ones = np.array([1.0, 1.0, 1.0])
x = np.array([0.5, 1.5, 2.5])

# Build y as an on-plane point PLUS an explicit, clearly-visible perpendicular offset
# (the plane's normal direction = cross(ones, x)), so the residual is unmistakable to see.
plane_normal = np.cross(ones, x)
plane_normal = plane_normal / np.linalg.norm(plane_normal)
on_plane_point = 0.4 * ones + 0.9 * x
y = on_plane_point + 1.6 * plane_normal

# --- Solve the normal equations directly (same result as Steps 1-2's alpha/beta formulas) ---
# alpha, beta minimize ||y - (alpha*ones + beta*x)||^2
A = np.column_stack([ones, x])
coeffs, *_ = np.linalg.lstsq(A, y, rcond=None)
alpha_hat, beta_hat = coeffs
y_hat = alpha_hat * ones + beta_hat * x
residual = y - y_hat

print(f"alpha_hat = {alpha_hat:.4f}, beta_hat = {beta_hat:.4f}")
print(f"sum(error)   = {residual.sum():.10f}  (should be ~0 — dot product with ones-vector)")
print(f"sum(error*x) = {(residual * x).sum():.10f}  (should be ~0 — dot product with x-vector)")
print(f"residual . ones = {np.dot(residual, ones):.10f}")
print(f"residual . x    = {np.dot(residual, x):.10f}")

# --- Build the plane (span of ones & x) as a mesh for plotting ---
a_range = np.linspace(-0.3, 1.0, 10)
b_range = np.linspace(-0.3, 1.3, 10)
A_grid, B_grid = np.meshgrid(a_range, b_range)
plane_x = A_grid * ones[0] + B_grid * x[0]
plane_y = A_grid * ones[1] + B_grid * x[1]
plane_z = A_grid * ones[2] + B_grid * x[2]

# palette.md categorical slots (dark-surface steps): 1=blue, 2=orange, 3=aqua
COLOR_PLANE = '#3987e5'
COLOR_ONES = '#c98500'   # yellow-ish (slot 4 dark step) — spanning vector 1
COLOR_X = '#d95926'      # orange (slot 2) — spanning vector 2
COLOR_Y = '#e66767'      # red (slot 8) — the actual data point, off the plane
COLOR_YHAT = '#199e70'   # aqua (slot 3) — the projection, on the plane
COLOR_RESIDUAL = '#c3c2b7'  # secondary ink — the perpendicular connector

fig = plt.figure(figsize=(11, 10))
ax = fig.add_subplot(111, projection='3d')

ax.plot_surface(plane_x, plane_y, plane_z, color=COLOR_PLANE, alpha=0.35, edgecolor='#5598e7',
                 linewidth=0.3, shade=False)

origin = np.zeros(3)
def arrow(vec, color, label, label_offset=1.12):
    ax.quiver(*origin, *vec, color=color, arrow_length_ratio=0.06, linewidth=2.6)
    ax.text(*(vec * label_offset), label, color=color, fontsize=10, weight='bold')

arrow(ones, COLOR_ONES, "1's-vector (1,1,1)", 1.25)
arrow(x, COLOR_X, f"x-vector ({x[0]},{x[1]},{x[2]})", 1.1)
arrow(y, COLOR_Y, f"y (data)\n({y[0]:.2f},{y[1]:.2f},{y[2]:.2f})", 1.08)
arrow(y_hat, COLOR_YHAT, f"ŷ = α̂·1+β̂·x\n(projection, ON plane)", 1.15)

# Residual: dashed line from y_hat to y — now a clearly visible perpendicular segment
ax.plot([y_hat[0], y[0]], [y_hat[1], y[1]], [y_hat[2], y[2]],
        color='white', linestyle='--', linewidth=3, zorder=10,
        label='residual = y − ŷ  (⊥ to the plane)')
ax.scatter(*y_hat, color=COLOR_YHAT, s=90, depthshade=False, zorder=11, edgecolor='white')
ax.scatter(*y, color=COLOR_Y, s=90, depthshade=False, zorder=11, edgecolor='white')

ax.set_xlabel('day 1 axis')
ax.set_ylabel('day 2 axis')
ax.set_zlabel('day 3 axis')
ax.set_title("OLS as orthogonal projection — why they're called 'normal' equations\n"
             "(residual ⊥ both the 1's-vector and the x-vector)", fontsize=13)
ax.legend(loc='upper left', fontsize=9)
ax.view_init(elev=18, azim=-55)

plt.tight_layout()
plt.savefig('52_mathmode_normal_equations_projection_example.png', dpi=130)
plt.show()
print('Saved 52_mathmode_normal_equations_projection_example.png')
