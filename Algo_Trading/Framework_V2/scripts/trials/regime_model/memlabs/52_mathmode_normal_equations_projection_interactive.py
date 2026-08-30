"""
Step 52 — interactive (rotatable) version of the normal-equations projection example.
Same data/vectors as 52_mathmode_normal_equations_projection_example.py, rendered with Plotly
so it can be freely rotated/zoomed in a browser instead of viewed from one fixed matplotlib angle.
"""
import numpy as np
import plotly.graph_objects as go

# --- Same toy n=3 dataset as the matplotlib version ---
ones = np.array([1.0, 1.0, 1.0])
x = np.array([0.5, 1.5, 2.5])

plane_normal = np.cross(ones, x)
plane_normal = plane_normal / np.linalg.norm(plane_normal)
on_plane_point = 0.4 * ones + 0.9 * x
y = on_plane_point + 1.6 * plane_normal

A = np.column_stack([ones, x])
coeffs, *_ = np.linalg.lstsq(A, y, rcond=None)
alpha_hat, beta_hat = coeffs
y_hat = alpha_hat * ones + beta_hat * x
residual = y - y_hat

print(f"alpha_hat = {alpha_hat:.4f}, beta_hat = {beta_hat:.4f}")
print(f"residual . ones = {np.dot(residual, ones):.10f}")
print(f"residual . x    = {np.dot(residual, x):.10f}")

# --- Plane mesh (span of ones & x) ---
a_range = np.linspace(-0.3, 1.0, 15)
b_range = np.linspace(-0.3, 1.3, 15)
A_grid, B_grid = np.meshgrid(a_range, b_range)
plane_x = A_grid * ones[0] + B_grid * x[0]
plane_y = A_grid * ones[1] + B_grid * x[1]
plane_z = A_grid * ones[2] + B_grid * x[2]

COLOR_PLANE = '#3987e5'
COLOR_ONES = '#c98500'
COLOR_X = '#d95926'
COLOR_Y = '#e66767'
COLOR_YHAT = '#199e70'

fig = go.Figure()

fig.add_trace(go.Surface(x=plane_x, y=plane_y, z=plane_z, colorscale=[[0, COLOR_PLANE], [1, COLOR_PLANE]],
                          opacity=0.35, showscale=False, name='plane = span(1s, x)'))

def add_vector(vec, color, name):
    fig.add_trace(go.Scatter3d(x=[0, vec[0]], y=[0, vec[1]], z=[0, vec[2]], mode='lines+markers+text',
                                line=dict(color=color, width=8), marker=dict(size=3, color=color),
                                text=['', name], textposition='top center', textfont=dict(color=color, size=13),
                                name=name))

add_vector(ones, COLOR_ONES, "1's-vector (1,1,1)")
add_vector(x, COLOR_X, f"x-vector ({x[0]},{x[1]},{x[2]})")
add_vector(y, COLOR_Y, f"y (data) ({y[0]:.2f},{y[1]:.2f},{y[2]:.2f})")
add_vector(y_hat, COLOR_YHAT, "ŷ = α̂·1+β̂·x (projection, ON plane)")

fig.add_trace(go.Scatter3d(x=[y_hat[0], y[0]], y=[y_hat[1], y[1]], z=[y_hat[2], y[2]],
                            mode='lines', line=dict(color='white', width=6, dash='dash'),
                            name='residual = y − ŷ (⊥ to the plane)'))
fig.add_trace(go.Scatter3d(x=[y_hat[0]], y=[y_hat[1]], z=[y_hat[2]], mode='markers',
                            marker=dict(size=6, color=COLOR_YHAT, line=dict(color='white', width=1)), showlegend=False))
fig.add_trace(go.Scatter3d(x=[y[0]], y=[y[1]], z=[y[2]], mode='markers',
                            marker=dict(size=6, color=COLOR_Y, line=dict(color='white', width=1)), showlegend=False))

fig.update_layout(
    template='plotly_dark',
    title="OLS as orthogonal projection — why they're called 'normal' equations<br>"
          "(residual ⊥ both the 1's-vector and the x-vector) — drag to rotate, scroll to zoom",
    scene=dict(xaxis_title='day 1 axis', yaxis_title='day 2 axis', zaxis_title='day 3 axis',
               aspectmode='cube'),
    legend=dict(x=0.01, y=0.99),
    width=1000, height=900,
)

out_path = __file__.replace('.py', '.html').replace('interactive', 'interactive')
fig.write_html('52_mathmode_normal_equations_projection_interactive.html')
print('Saved 52_mathmode_normal_equations_projection_interactive.html')
