"""
Verification — do our hand-derived methods reproduce sklearn's exact Model A weights?

Pulls the ACTUAL Train portion of Model A's real data (same dropna + 75/25 split as
backtest_model() uses internally, from 18_regime_change_author_reference_code.py) and
computes w, b two ways by hand, then compares against sklearn's LinearRegression.

  Method 1: Two-step approach   -> w = cov(x,y)/var(x), b = mean(y) - w*mean(x)
  Method 2: Normal Equation     -> beta = (X^T X)^-1 X^T y  (explicit matrix inversion)
  Reference: sklearn LinearRegression().fit()

All three should match to floating-point precision, confirming sklearn's SVD-based
solver (scipy.linalg.lstsq internally) arrives at the identical answer as the textbook
closed-form OLS formulas -- it just gets there via a more numerically stable route.

Data: BTCUSDT_1d_author_original.csv (author's exact recovered source file,
2020-08-19 to 2026-05-16, 2097 rows).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

btcusdt = pd.read_csv('BTCUSDT_1d_author_original.csv')
btcusdt['t'] = pd.to_datetime(btcusdt['t'])
btcusdt.set_index('t', inplace=True)

btcusdt['close_log_return'] = np.log(btcusdt['c'] / btcusdt['c'].shift())
btcusdt['close_log_return_lag_1'] = btcusdt['close_log_return'].shift()

df_a_only = btcusdt[['close_log_return', 'close_log_return_lag_1']].dropna()
df_train_a, df_test_a = train_test_split(df_a_only, test_size=0.25, shuffle=False)

x_tr = df_train_a['close_log_return_lag_1'].to_numpy()
y_tr = df_train_a['close_log_return'].to_numpy()
print('Train rows used for fitting:', len(x_tr))

# --- Method 1: Two-step approach ---
mean_x, mean_y = x_tr.mean(), y_tr.mean()
cov_xy = np.mean((x_tr - mean_x) * (y_tr - mean_y))
var_x = np.mean((x_tr - mean_x) ** 2)
w_twostep = cov_xy / var_x
b_twostep = mean_y - w_twostep * mean_x
print()
print('=== Method 1: Two-step (cov/var) ===')
print('w =', w_twostep)
print('b =', b_twostep)

# --- Method 2: Normal Equation via explicit matrix inversion ---
X = np.column_stack([np.ones(len(x_tr)), x_tr])
XtX = X.T @ X
Xty = X.T @ y_tr
beta = np.linalg.inv(XtX) @ Xty
print()
print('=== Method 2: Normal Equation (matrix inversion) ===')
print('b =', beta[0])
print('w =', beta[1])

# --- sklearn's actual answer, for comparison ---
model_a = LinearRegression()
model_a.fit(df_train_a[['close_log_return_lag_1']], df_train_a['close_log_return'])
print()
print('=== sklearn (LinearRegression.fit()) ===')
print('w =', model_a.coef_[0])
print('b =', model_a.intercept_)
