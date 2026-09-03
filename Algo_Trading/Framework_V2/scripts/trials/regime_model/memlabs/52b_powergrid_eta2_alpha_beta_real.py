"""
Step 52 Part 2 — Alpha/Beta CAPM regression applied to REAL POWERGRID eta0=2.0 Model C data.
Answers: is eta0=2.0's equity-curve outperformance statistically real skill, or noise/market-
tracking? Replicates the exact online-learning setup from 50c_model_c_powergrid.ipynb (same
DS3 source, same SGDRegressor config, same random_state=69), then applies the full Steps 0-14
CAPM derivation from 52_mathmode_full_derivation_chronological.md.

strategy_return_t = alpha + beta * market_return_t + error_t
  market_return  = POWERGRID's own daily close-to-close log return (raw buy-and-hold return)
  strategy_return = Model C eta0=2.0's daily signal * actual-return (the strategy's own P&L)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

plt.style.use('dark_background')

# --- Replicate 50c's exact data prep ---
DS3_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3/POWERGRID.parquet'
pg_5min = pd.read_parquet(DS3_PATH)
pg_5min['date'] = pg_5min['datetime'].dt.date

pg_daily = pg_5min.groupby('date')['close'].last().to_frame()
pg_daily.index = pd.to_datetime(pg_daily.index)
pg_daily = pg_daily.sort_index()

pg_daily['close_log_return'] = np.log(pg_daily['close'] / pg_daily['close'].shift())
pg_daily['close_log_return_lag_1'] = pg_daily['close_log_return'].shift()

pg_clean = pg_daily.dropna()
X_stream = pg_clean[['close_log_return_lag_1']].to_numpy()
y_stream = pg_clean['close_log_return'].to_numpy()

print(f"trading days used: {len(X_stream)}  date range: {pg_clean.index.min().date()} -> {pg_clean.index.max().date()}")

# --- Replicate 50c's exact eta0=2.0 online run ---
def run_replication(eta0):
    model = SGDRegressor(loss="epsilon_insensitive", epsilon=0.0002, penalty=None,
                          learning_rate="pa1", eta0=eta0, random_state=69)
    scaler = StandardScaler()
    rows = []
    for t in range(len(X_stream)):
        X_t = X_stream[t].reshape(1, -1)
        y_t = np.array([y_stream[t]])
        scaler.partial_fit(X_t)
        X_t_scaled = scaler.transform(X_t)
        pred_y = 0.0 if t == 0 else model.predict(X_t_scaled)[0]
        model.partial_fit(X_t_scaled, y_t)
        signal = np.sign(pred_y)
        rows.append({'tick': t, 'sig': signal, 'true_y': y_t[0], 'trade_log_return': signal * y_t[0]})
    return pd.DataFrame(rows).set_index('tick')

df_eta2 = run_replication(eta0=2.0)
print(f"eta0=2.0 final cumulative return: {df_eta2['trade_log_return'].cumsum().iloc[-1]:.4f}")

# --- CAPM setup ---
market_return = df_eta2['true_y'].to_numpy()          # POWERGRID's own daily return
strategy_return = df_eta2['trade_log_return'].to_numpy()  # eta0=2.0's daily P&L
n = len(market_return)

# --- Steps 1-2: beta, alpha ---
x_bar = market_return.mean()
y_bar = strategy_return.mean()
cov_xy = np.mean((market_return - x_bar) * (strategy_return - y_bar))
var_x = np.mean((market_return - x_bar) ** 2)
beta = cov_xy / var_x
alpha = y_bar - beta * x_bar

# --- Step 3: residuals ---
fitted = alpha + beta * market_return
error = strategy_return - fitted

# --- Step 6: Var(error) ---
var_error = np.sum(error ** 2) / (n - 2)

# --- Steps 11-12: SE(alpha), SE(beta) ---
Sxx = np.sum((market_return - x_bar) ** 2)
se_alpha = np.sqrt(var_error * (1/n + x_bar**2/Sxx))
se_beta = np.sqrt(var_error / Sxx)

# --- Steps 13-14: t-stat, p-value ---
t_alpha = alpha / se_alpha
p_alpha = 2 * stats.t.sf(abs(t_alpha), df=n-2)
t_beta = beta / se_beta
p_beta = 2 * stats.t.sf(abs(t_beta), df=n-2)

print()
print(f"n = {n}")
print(f"alpha (daily)     = {alpha:.6f}   annualized (x252) = {alpha*252:.4f}")
print(f"beta              = {beta:.4f}")
print(f"Var(error)        = {var_error:.6f}")
print()
print(f"SE(alpha) = {se_alpha:.6f}   t(alpha) = {t_alpha:.4f}   p(alpha) = {p_alpha:.4f}")
print(f"SE(beta)  = {se_beta:.4f}     t(beta)  = {t_beta:.4f}   p(beta)  = {p_beta:.4f}")
print()
verdict = "STATISTICALLY SIGNIFICANT" if p_alpha < 0.05 else "NOT statistically significant"
print(f"VERDICT: alpha is {verdict} (p={p_alpha:.4f} {'<' if p_alpha<0.05 else '>='} 0.05)")

# --- Plot: scatter + fitted line + confidence band, same style as the toy example ---
fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(market_return, strategy_return, color='#4fc3f7', s=10, alpha=0.5, zorder=3, label='daily (market_return, strategy_return)')
x_line = np.linspace(market_return.min(), market_return.max(), 200)
y_line = alpha + beta * x_line
se_line = np.sqrt(var_error * (1/n + (x_line - x_bar)**2 / Sxx))
ax.plot(x_line, y_line, color='#ff8a65', lw=2, label=f'fitted line: y = {alpha:.5f} + {beta:.3f}*x')
ax.fill_between(x_line, y_line - se_line, y_line + se_line, color='#ff8a65', alpha=0.25, label='+/- 1 SE band')
ax.fill_between(x_line, y_line - 2*se_line, y_line + 2*se_line, color='#ff8a65', alpha=0.12, label='+/- 2 SE band')
ax.axvline(0, color='gray', lw=0.8, ls='--')
ax.axhline(0, color='gray', lw=0.8, ls='--')
ax.errorbar([0], [alpha], yerr=[se_alpha], fmt='D', color='#ffca28', ecolor='#ffca28', capsize=5, zorder=4,
            label=f'alpha +/- SE(alpha) = {alpha:.5f} +/- {se_alpha:.5f}  (p={p_alpha:.4f})')
ax.set_xlabel('market_return (POWERGRID daily log return)')
ax.set_ylabel('strategy_return (eta0=2.0 daily P&L)')
ax.set_title(f'POWERGRID eta0=2.0 CAPM regression (n={n}) — {verdict}')
ax.legend(fontsize=8, loc='upper left')
plt.tight_layout()
out_path = __file__.replace('.py', '.png')
plt.savefig(out_path, dpi=130)
print(f"\nSaved: {out_path}")
