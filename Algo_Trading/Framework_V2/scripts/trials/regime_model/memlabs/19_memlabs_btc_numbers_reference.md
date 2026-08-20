Here are all the results, numerical outputs, and chart descriptions shown by the author for each of the models evaluated in the video. 

*(Note: The author lists 4 methods at the beginning, but skips a full backtest for Method 1: Sliding Window, stating he is not a fan of it. Instead, he establishes a "Base Model" first to show the problem, and then evaluates Methods 2, 3, and 4).*

---

### 0. Base Model (Non-Adaptive Auto-Regressive Model)
Before applying the adaptive techniques, the author tests a standard linear regression model using just the previous day's return (`lag_1`) to predict the next day.

*   **Printed Weights/Bias:** `[-0.02902972] 0.0014044601590437902`
    *(CORRECTED — verified against actual video screenshot 2026-08-03. Original Google AI
    Studio extraction misread this as `[-0.02962972] 0.0014044601596437902`. Independently
    reproduced exactly by our own notebook replication — `21_author_replication_notebook.ipynb`.)*
*   **Signal Value Counts:**
    *   `1.0` (Buy): 1991
    *   `-1.0` (Sell): 104
    *(CORRECTED — Buy count was misread as 1891, should be 1991. Sell count was correct.)*
*   **Chart Description:** The equity curve (`cum_trade_log_return`) looks almost identical to the underlying Bitcoin price chart. It goes up in 2021, suffers a massive drawdown through 2022-2023, and then goes back up. 
*   **Author's Takeaway:** The model is not adaptive. It predicts the market will go up ~95% of the time. When the regime changes to a bear market (2022), the model fails to adapt and loses money.

---

### 1. Sliding Window
*   **Results:** None shown. 
*   **Author's Takeaway:** The author explains the matrix logic but skips backtesting this method. He states he is not a fan of it because it only looks at a localized pattern and is highly sensitive to the chosen window size, making it a "clunky" approach.

---

### 2. Encoding Memory (Moving Average)
The author adds a 40-day moving average of the lagged returns (`ma_lag_1`) — first as a
standalone replacement feature, then combined with the raw lag.

**Step 2a — MA-alone (replaces `lag_1` entirely, single feature):**
*   **Printed Weights/Bias:** `[0.28444309] 0.0010530459416579004`
    *(CONFIRMED via video screenshot — no earlier Studio extraction existed for this step.)*
*   **Signal Value Counts:** `1.0` (Buy): 1689, `-1.0` (Sell): 367

**Step 2b — Combined (`lag_1` + `ma_lag_1` together, "relative memory"):**
*   **Printed Weights/Bias:** `[-0.03820892  0.32349523] 0.0010550240542074694`
    *(CORRECTED — verified against actual video screenshot 2026-08-03. Original Google AI
    Studio extraction badly misread this as `[-0.03028802 -3.2349553] 0.00585814582674094`
    — a digit transposition, wrong sign, and misplaced decimal on the second coefficient.
    Independently reproduced exactly by our own notebook replication.)*
*   **Signal Value Counts:**
    *   `1.0` (Buy): 1612
    *   `-1.0` (Sell): 444
    *(CORRECTED — was misread as 1680/307.)*
*   **Chart Description:** The equity curve is significantly smoother than the base model. It successfully avoids the massive drawdown during the 2022-2023 bear market and trends upwards much more consistently.
*   **Author's Takeaway:** By adding memory, the model becomes more adaptive. It predicts "down" more frequently during the bear market regime, protecting capital. The author notes the win rate is likely around 50.5% to 51%.

---

### 3. Online Learning (Passive Aggressive Regressor)
The author uses a streaming machine learning model that updates its weights tick-by-tick. If the model makes a wrong prediction, it applies an "error correction" to adjust the weights immediately.

*   **Printed Hit Rate:** `Dataframe Evaluated Hit Rate: 50.82%`
*   **Signal Value Counts:**
    *   `-1.0` (Sell): 1036
    *   `1.0` (Buy): 1017
*   **Chart Description:** The equity curve is a very smooth, consistent upward line from 2021 through 2026. 
*   **Author's Takeaway:** This is highly adaptive. The signal distribution is nearly 50/50. The model successfully makes money both when the market is trending downwards and when it is trending upwards because the weights dynamically shift between momentum and mean-reversion strategies based on recent errors.

---

### 4. Policy Gradient Reinforcement Learning
The author frames trading as a "2-Armed Bandit" problem (guessing heads or tails on a biased coin) to demonstrate how RL adapts to regime changes. He tests a coin where the bias switches from 70% Heads to 20% Heads at episode 1000.

**Experiment 1: Vanilla REINFORCE (No Entropy Regularization)**
*   **Printed Results:**
    ```text
    --- VANILLA REINFORCE ---
    Before switch (first 1000): avg=+0.388 (optimal=+0.40, regret=+0.012)
    After switch  (last 1000): avg=-0.552 (optimal=+0.60, regret=+1.152)
    ```
*   **Chart Description:** 
    *   *Probability Chart:* The model quickly learns to guess heads 100% of the time (probability hits 1.0). When the regime switches at episode 1000, the line stays completely flat at 1.0.
    *   *Reward Chart:* The reward is positive before the switch, but immediately drops to negative after episode 1000 and stays there.
*   **Author's Takeaway:** The model gets stuck in a "local optima" of pure exploitation. It stops exploring, so when the regime changes, it never realizes the rules have changed and loses money continuously.

**Experiment 2: REINFORCE with Entropy Bonus (beta=0.1)**
*   **Printed Results:**
    ```text
    --- ENTROPY-REGULARIZED REINFORCE ---
    Before switch (first 1000): avg=+0.350 (optimal=+0.40, regret=+0.050)
    After switch  (last 1000): avg=+0.538 (optimal=+0.60, regret=+0.062)
    ```
*   **Chart Description:** 
    *   *Probability Chart:* The model learns to guess heads ~95% of the time initially (reserving 5% for exploration). At episode 1000, the line plummets rapidly down to ~0.05, meaning it successfully learned to start guessing tails.
    *   *Reward Chart:* The reward is positive initially. At episode 1000, it dips briefly, but quickly recovers back to a high positive reward (~0.6).
*   **Author's Takeaway:** By forcing the model to maintain some uncertainty (entropy), it continues to explore. When the regime changes, it detects the change, adapts its policy, and returns to profitability.


*************************



Based on a frame-by-frame inspection of the video, I can provide the exact date range of the dataset. The author does indeed display the raw dataframe output on screen multiple times.

Here are the exact details visible in the video:

**1. Raw Dataframe Output (The Exact Dates)**
At several points in the video (specifically visible at **01:36**, **01:56**, **09:41**, and **10:57**), the author executes a cell that outputs the `btcusdt` dataframe. The standard Pandas truncated view (showing the first 5 and last 5 rows) is clearly visible. 

Looking directly at the datetime index (`t`) in this output:
*   **Earliest visible date (Row 0):** `2020-08-19`
*   **Latest visible date (Last Row):** `2026-05-16`

Additionally, the text directly below this dataframe output explicitly reads: **`2097 rows × 10 columns`**.

**2. Chart X-Axes**
Whenever the author plots charts with a datetime x-axis (e.g., `btcusdt['c'].plot()` at **03:10**, or the backtest equity curves at **06:57** and **11:32**):
*   The major tick marks labeled on the x-axis are the years: **2021, 2022, 2023, 2024, 2025, 2026**.
*   The plotted line visibly starts slightly to the left of the "2021" tick mark (aligning with August 2020) and ends slightly to the right of the "2026" tick mark (aligning with May 2026).
*   *(Note: Later in the video, during the Online Learning section at 19:28, the x-axis switches to integer index ticks [0, 500, 1000, 1500, 2000] rather than dates).*

**3. Groupby Output**
At **02:48**, the author runs `btcusdt.groupby(btcusdt.index.year)...`. The resulting output explicitly lists the years present in the index: **2020, 2021, 2022, 2023, 2024, 2025, 2026**.

### Conclusion
The exact date range of the `BTCUSDT_1d.csv` dataset shown on screen is **August 19, 2020 to May 16, 2026**.