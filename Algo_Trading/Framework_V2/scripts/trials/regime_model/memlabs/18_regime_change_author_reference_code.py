"""
Step 18 - reference code, verbatim from the author (MemLabs channel, video:
"How to handle Regime Changes (by ex HFT quant trader)"). Not our own
implementation - this is the source we've been comparing scripts 01-17
against. Combined file covering all 4 models discussed in the video
(sliding window, memory encoding/relative memory, online learning, RL).

Paste the extracted code below.
"""

# 00:00 - Initial setup and imports
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

seed = 0
torch.manual_seed(seed)
np.random.seed(seed)

# 00:48 - Loading data and calculating log returns
btcusdt = pd.read_csv('https://raw.githubusercontent.com/memlabs-research/datasets/refs/heads/main/BTCUSDT_1d.csv')
btcusdt['t'] = pd.to_datetime(btcusdt['t'])
btcusdt.set_index('t', inplace=True)
btcusdt['close_return'] = btcusdt['c'].pct_change()

# 01:36 - Histogram of close returns
btcusdt['close_return'].hist(bins=200)

# 01:56 - Aggregating moments
btcusdt.aggregate({'close_return': ['mean', 'std', 'skew', 'kurt']})

# 02:48 - Grouping by year and aggregating moments
btcusdt.groupby(btcusdt.index.year).aggregate({'close_return': ['mean', 'std', 'skew', pd.Series.kurtosis]})

# 03:10 - Plotting the close price
btcusdt['c'].plot()

# 04:52 - Preparing data for supervised learning (AR model)
btcusdt['close_log_return'] = np.log(btcusdt['c']/btcusdt['c'].shift())
btcusdt['close_log_return_lag_1'] = btcusdt['close_log_return'].shift()

# 05:33 - backtest_model function
def backtest_model(df, features, target, test_split = 0.25):
    df = df.dropna()
    
    df_train, df_test = train_test_split(df, test_size=test_split, shuffle=False)
    
    X_train, X_test, y_train, y_test = df_train[features], df_test[features], df_train[target], df_test[target]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    print(model.coef_, model.intercept_)
    
    backtest = df.copy()
    backtest['y_hat'] = model.predict(backtest[features])
    backtest['signal'] = np.sign(backtest['y_hat'])
    backtest['trade_log_return'] = backtest['close_log_return'] * backtest['signal']
    backtest['cum_trade_log_return'] = backtest['trade_log_return'].cumsum()
    backtest['cum_trade_log_return'].plot()
    
    return model, backtest

# 06:57 - Running the backtest
model, backtest = backtest_model(btcusdt, ['close_log_return_lag_1'], 'close_log_return')

# 07:15 - Plotting the original close price again for comparison
backtest['c'].plot()

# 07:31 - Value counts of the signal
backtest['signal'].value_counts()

# 09:41 - Encoding memory (moving average)
btcusdt['close_log_return_ma_lag_1'] = btcusdt['close_log_return_lag_1'].rolling(40).mean()

# 10:57 - Running backtest with moving average feature
model, backtest = backtest_model(btcusdt, ['close_log_return_ma_lag_1'], 'close_log_return')

# 11:32 - Value counts of the new signal
backtest['signal'].value_counts()

# 12:25 - Running backtest with both lag and moving average features
model, backtest = backtest_model(btcusdt, ['close_log_return_lag_1', 'close_log_return_ma_lag_1'], 'close_log_return')

# 13:10 - Plotting original close price again
backtest['c'].plot()

# 13:42 - Value counts of the combined signal
backtest['signal'].value_counts()

# 14:35 - Online Learning setup (Passive Aggressive Regressor)
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

# 1. Prepare Data Stream ===
df_clean = btcusdt.dropna()
features = ['close_log_return_lag_1']
target = 'close_log_return'

X_stream = df_clean[features].to_numpy()
y_stream = df_clean[target].to_numpy()

# 2. Initialize Updated Online Learning Components ===
# Using SGDRegressor configured for native Passive-Aggressive updates
model = SGDRegressor(
    loss="epsilon_insensitive", # The acceptable error margin (passive threshold)
    epsilon=0.0002,             # Pure PA doesn't use L1/L2 shrinkage penalties
    penalty=None,               # Uses PA-2 update rules (or "pa1")
    learning_rate="pa1",        # Acts as parameter C (maximum step size cap)
    eta0=0.01,
    random_state=69
)
scaler = StandardScaler()

# List to collect structural and evaluation records row-by-row
records = []

# 16:42 - Online Learning loop
# 3. Pure Streaming Loop ===
for t in range(len(X_stream)):
    X_t = X_stream[t].reshape(1, -1)
    y_t = np.array([y_stream[t]])
    
    # Scale feature vector incrementally based on live variance shifts
    scaler.partial_fit(X_t)
    X_t_scaled = scaler.transform(X_t)
    
    # A. TEST STEP: Predict before updating weights
    if t == 0:
        pred_y = 0.0 # Cold start initialization
    else:
        pred_y = model.predict(X_t_scaled)[0]
        
    # Evaluate Directional Accuracy
    if t > 0 and y_t[0] != 0 and pred_y != 0:
        sign_match = "YES" if np.sign(y_t[0]) == np.sign(pred_y) else "NO"
    else:
        sign_match = "Warmup"
        
    # B. TRAIN STEP: Update weights dynamically via SGD single-sample steps
    model.partial_fit(X_t_scaled, y_t)
    
    # Extract structural components safely from SGDRegressor
    current_weight = model.coef_[0]
    current_bias = model.intercept_[0]
    
    # Calculate signal and if won or not in the tick
    signal = np.sign(pred_y)
    trade_log_return = signal * y_t[0]
    
    # Record the complete state context at this tick
    if sign_match != "Warmup":
        records.append({
            'tick': t,
            'lag_1_x': X_t[0][0],
            'true_y': y_t[0],
            'pred_y_hat': pred_y,
            'sign_match': sign_match,
            'model_weight': current_weight,
            'model_bias': current_bias,
            'signal': signal,
            'trade_log_return': trade_log_return,
            'is_won': np.sign(y_t[0]) == np.sign(pred_y)
        })

# 17:45 - Converting records to DataFrame and calculating hit rate
# Convert Records to Pandas DataFrame
df_results = pd.DataFrame(records)
df_results.set_index('tick', inplace=True)
df_results['cum_trade_log_return'] = df_results['trade_log_return'].cumsum()

# Calculate directional hit rate
evaluated_mask = df_results['sign_match'].isin(['YES', 'NO'])
if evaluated_mask.sum() > 0:
    hit_rate = (df_results[evaluated_mask]['sign_match'] == 'YES').mean() * 100
    print(f"\nDataframe Evaluated Hit Rate: {hit_rate:.2f}%")

# 18:00 - Displaying df_results
df_results

# 19:22 - Value counts of online learning signal
df_results['signal'].value_counts()

# 19:28 - Plotting cumulative return of online learning
df_results['cum_trade_log_return'].plot()

# 19:31 - Plotting original close price
btcusdt['c'].plot()

# 23:23 - Reinforcement Learning - StationaryBiasedCoin environment
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

class StationaryBiasedCoin:
    """Stateless stationary biased-coin environment."""
    def __init__(self, p_heads=0.7):
        self.p_heads = p_heads
        
    def step(self, action):
        outcome = 1 if np.random.random() < self.p_heads else 0
        reward = 1.0 if action == outcome else -1.0
        return reward, outcome

# 23:51 - Reinforcement Learning - Policy network
class Policy(nn.Module):
    """Constant input -> logits over {tails=0, heads=1}."""
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(1, 2)
        
    def forward(self, x):
        return self.fc(x)

# 24:10 - Reinforcement Learning - train function
def train(env, n_episodes=2000, lr=0.05, log_every=200, seed=0):
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    strategy = Policy()
    optimizer = optim.Adam(strategy.parameters(), lr=lr)
    
    state = torch.tensor([1.0]) # constant dummy input
    rewards, p_heads_history = [], []
    
    for episode in range(n_episodes):
        # Forward pass: sample an action from the current policy
        logits = strategy(state)
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        
        # Interact with environment
        reward, _ = env.step(action.item())
        
        # REINFORCE update: maximize E[log pi(a|s) * R]
        # -> minimize negative of that
        loss = -log_prob * reward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Logging
        rewards.append(reward)
        with torch.no_grad():
            probs = torch.softmax(strategy(state), dim=-1)
            p_heads_history.append(probs[1].item())
            
        if (episode + 1) % log_every == 0:
            recent = np.mean(rewards[-log_every:])
            print(f"Ep {episode+1:>5d} | P(guess heads)={probs[1]:.3f} | "
                  f"Avg reward (last {log_every})={recent:+.3f}")
            
    return strategy, rewards, p_heads_history

# 25:46 - Running the RL training on stationary coin
P_TRUE = 0.7
env = StationaryBiasedCoin(P_TRUE)
policy, rewards, p_heads_history = train(env, n_episodes=2000, lr=0.01)

with torch.no_grad():
    final = torch.softmax(policy(torch.tensor([1.0])), dim=-1)
    
optimal = 2 * max(P_TRUE, 1 - P_TRUE) - 1
print("\n--- Results ---")
print(f"True coin bias:           P(heads) = {P_TRUE}")
print(f"Learned policy:           P(guess heads) = {final[1]:.3f}")
print(f"Optimal expected reward/flip: {optimal:+.3f}")
print(f"Avg reward (last 500 episodes): {np.mean(rewards[-500:]):+.3f}")

# 25:58 - Plotting learning curves
# Optional: Plot learning curves
try:
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    window = 100
    
    def smooth(x):
        return np.convolve(x, np.ones(window)/window, mode='valid')
        
    ax1.plot(smooth(rewards), label='reward')
    ax1.axhline(optimal, ls='--', c='r', label=f'optimal ({optimal:+.2f})')
    ax1.set(title=f'Reward (rolling mean, window={window})',
            xlabel='episode', ylabel='reward')
    ax1.legend()
    
    ax2.plot(p_heads_history)
    ax2.axhline(1.0, ls='--', c='g', label='optimal (1.0)')
    ax2.set(title='P(guess heads) over training',
            xlabel='episode', ylabel='probability', ylim=(0, 1.05))
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('coin_toss_training.png', dpi=100)
    print("\nSaved plot to coin_toss_training.png")
except ImportError:
    pass

# 27:16 - NonStationaryBiasedCoin environment
class NonStationaryBiasedCoin:
    """Coin whose bias switches at a fixed episode."""
    def __init__(self, p_before=0.7, p_after=0.2, switch_at=1000):
        self.p_before = p_before
        self.p_after = p_after
        self.switch_at = switch_at
        self.t = 0
        
    def step(self, action):
        p = self.p_before if self.t < self.switch_at else self.p_after
        outcome = 1 if np.random.random() < p else 0
        reward = 1.0 if action == outcome else -1.0
        self.t += 1
        return reward, outcome
        
    def current_p(self):
        return self.p_before if self.t < self.switch_at else self.p_after

# 28:28 - Entropy Regularization math and plot
import numpy as np
import matplotlib.pyplot as plt

# Generate probabilities from 0 to 1
# We use a tiny epsilon offset at the boundaries (0 and 1) to avoid log2(0) errors
p = np.linspace(1e-7, 1 - 1e-7, 500)

# Calculate Shannon Entropy in bits
entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)

# Create the plot
plt.figure(figsize=(9, 5.5))
plt.plot(p, entropy, label="Shannon Entropy $H(X)$", color="#1f77b4", linewidth=2.5)

# Highlight the maximum entropy point (Fair Coin)
plt.axvline(x=0.5, color="red", linestyle="--", alpha=0.7)
plt.axhline(y=1.0, color="red", linestyle="--", alpha=0.7)
plt.scatter([0.5], [1.0], color="red", zorder=5, label="Max Uncertainty (Fair Coin: p=0.5, H=1)")

# Formatting the chart
plt.title("Entropy of a Coin Flip (Binary Information Profile)", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Probability of Heads (p)", fontsize=12)
plt.ylabel("Entropy (Bits)", fontsize=12)
plt.xlim(0, 1)
plt.ylim(0, 1.05)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="lower center", fontsize=10, frameon=True)

# Show the plot
plt.tight_layout()
plt.show()

# 30:23 - train function with entropy regularization
def train(p_before=0.7, p_after=0.2, switch_at=1000, n_episodes=2000,
          lr=0.05, entropy_beta=0.0, log_every=200, seed=0):
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    env = NonStationaryBiasedCoin(p_before, p_after, switch_at)
    policy = Policy()
    optimizer = optim.Adam(policy.parameters(), lr=lr)
    
    state = torch.tensor([1.0])
    rewards, p_heads_history = [], []
    
    for episode in range(n_episodes):
        logits = policy(state)
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        reward, _ = env.step(action.item())
        
        # REINFORCE with entropy bonus:
        # maximize E[log pi * R] + beta * H(pi)
        policy_loss = -log_prob * reward
        entropy_loss = -entropy_beta * entropy
        loss = policy_loss + entropy_loss
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        rewards.append(reward)
        with torch.no_grad():
            probs = torch.softmax(policy(state), dim=-1)
            p_heads_history.append(probs[1].item())
            
        if (episode + 1) % log_every == 0:
            recent = np.mean(rewards[-log_every:])
            marker = " <-- bias switched!" if episode + 1 == switch_at + log_every else ""
            print(f"Ep {episode+1:>5d} | P_true={env.current_p():.1f} | "
                  f"P(guess heads)={probs[1]:.3f} | "
                  f"Avg reward(recent)={recent:+.3f}{marker}")
                  
    return policy, rewards, p_heads_history

# 31:25 - summarize function
def summarize(label, rewards, switch_at):
    pre = np.mean(rewards[:switch_at])
    post = np.mean(rewards[switch_at:])
    # Optimal expected rewards in each phase
    opt_pre, opt_post = 0.40, 0.60
    print(f"\n--- {label} ---")
    print(f"Before switch (first {switch_at}): avg={pre:+.3f} "
          f"(optimal={opt_pre:+.2f}, regret={opt_pre - pre:+.3f})")
    print(f"After switch  (last {len(rewards)-switch_at}): avg={post:+.3f} "
          f"(optimal={opt_post:+.2f}, regret={opt_post - post:+.3f})")

# 31:27 - Running experiments
SWITCH_AT = 1000
N_EPISODES = 2000

print("=" * 70)
print("Experiment 1: Vanilla REINFORCE (no entropy regularization)")
print("=" * 70)
_, rewards_vanilla, p_hist_vanilla = train(
    switch_at=SWITCH_AT, n_episodes=N_EPISODES, entropy_beta=0.0, seed=0,
)
summarize("VANILLA REINFORCE", rewards_vanilla, SWITCH_AT)

print("\n" + "=" * 70)
print("Experiment 2: REINFORCE with entropy bonus (beta=0.1)")
print("=" * 70)
_, rewards_entropy, p_hist_entropy = train(
    switch_at=SWITCH_AT, n_episodes=N_EPISODES, entropy_beta=0.1, seed=0,
)
summarize("ENTROPY-REGULARIZED REINFORCE", rewards_entropy, SWITCH_AT)

# 31:40 - Plotting comparison
# Plot comparison
try:
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    window = 50
    
    def smooth(x):
        return np.convolve(x, np.ones(window)/window, mode='valid')
        
    ax1.plot(smooth(rewards_vanilla), label='vanilla', alpha=0.8)
    ax1.plot(smooth(rewards_entropy), label='entropy bonus', alpha=0.8)
    ax1.axvline(SWITCH_AT, ls='--', c='k', alpha=0.5, label='bias switch')
    ax1.axhline(0.6, ls=':', c='gray', alpha=0.5)
    ax1.axhline(0.4, ls=':', c='gray', alpha=0.5)
    ax1.set(title=f'Reward (rolling mean, window={window})',
            xlabel='episode', ylabel='reward')
    ax1.legend()
    
    ax2.plot(p_hist_vanilla, label='vanilla', alpha=0.8)
    ax2.plot(p_hist_entropy, label='entropy bonus', alpha=0.8)
    ax2.axvline(SWITCH_AT, ls='--', c='k', alpha=0.5, label='bias switch')
    ax2.set(title='P(guess heads) over training',
            xlabel='episode', ylabel='probability', ylim=(0, 1.05))
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('nonstationary_coin.png', dpi=100)
    print("\nSaved plot to nonstationary_coin.png")
except ImportError:
    pass