# Model B — Exact Step-by-Step Math Trail

**Purpose:** Hand this to a second AI with frame-by-frame video access so it can compare our notebook-order execution against his real cell outputs.

**Scope:** Model B only (encoding memory, combined features).  
**Data:** Author's recovered file `BTCUSDT-1d_author.csv`  
(= `https://raw.githubusercontent.com/memlabs-research/datasets/main/BTCUSDT-1d.csv`)  
**Environment:** sklearn 1.8.0, numpy 2.4.1, pandas 2.3.3, Python 3.14  
**Reference code:** `18_regime_change_author_reference_code.py` lines 40–41, 74, 44–62, 83

His printed target for Model B (from video reference notes):

```text
coef_  = [-0.03028802, -3.2349553]
intercept_ = 0.00585814582674094
signal: Buy(+1)=1680, Sell(-1)=307
```

Our result from this trail:

```text
coef_  = [-0.03820891898454995, 0.32349523294151594]
intercept_ = 0.0010550240542074696
signal: Buy(+1)=1612, Sell(-1)=444
```

---

## Step 0 — Load CSV

```python
btcusdt = pd.read_csv('BTCUSDT-1d_author.csv')   # or the raw GitHub URL
btcusdt['t'] = pd.to_datetime(btcusdt['t'])
btcusdt.set_index('t', inplace=True)
```

**Row count:** 2097  
**Index span:** 2020-08-19 → 2026-05-16  
**Columns:** `T, s, i, o, c, h, l, v, n` (index = `t`)  
**`c` dtype:** float64

| | c | o | h | l | v |
|---|---|---|---|---|---|
| **first 3** | | | | | |
| 2020-08-19 | 11763.9 | 11962.0 | 12037.1 | 11574.8 | 0.0 |
| 2020-08-20 | 11857.9 | 11763.9 | 11888.0 | 11676.0 | 0.0 |
| 2020-08-21 | 11538.5 | 11858.5 | 11882.7 | 11491.0 | 0.0 |
| **last 3** | | | | | |
| 2026-05-14 | 81044.0 | 79283.0 | 81992.0 | 78880.0 | 36390.98195 |
| 2026-05-15 | 79063.0 | 81044.0 | 81623.0 | 78608.0 | 29636.44619 |
| 2026-05-16 | 78021.0 | 79062.0 | 79177.0 | 77600.0 | 14030.40537 |

Note: early `v` is 0.0 through 2023-02-25 (921 zero-volume rows). Author code never filters on volume.

---

## Step 1 — Log return + lag (author lines 40–41)

```python
btcusdt['close_log_return'] = np.log(btcusdt['c'] / btcusdt['c'].shift())
btcusdt['close_log_return_lag_1'] = btcusdt['close_log_return'].shift()
```

**Row count:** still 2097 (NaNs introduced, not dropped yet)

| date | c | close_log_return | close_log_return_lag_1 |
|---|---|---|---|
| 2020-08-19 | 11763.9 | NaN | NaN |
| 2020-08-20 | 11857.9 | 0.00795879197871233 | NaN |
| 2020-08-21 | 11538.5 | -0.02730504216180389 | 0.00795879197871233 |
| 2020-08-22 | 11670.5 | 0.011375… | -0.027305… |
| 2020-08-23 | 11654.0 | -0.001415… | 0.011375… |
| … | | | |
| 2026-05-14 | 81044.0 | 0.021968487193022558 | -0.014724008037606586 |
| 2026-05-15 | 79063.0 | -0.02474721405139055 | 0.021968487193022558 |
| 2026-05-16 | 78021.0 | -0.013266981789791518 | -0.02474721405139055 |

---

## Step 2 — MA of the **lag** series (author line 74)

```python
btcusdt['close_log_return_ma_lag_1'] = btcusdt['close_log_return_lag_1'].rolling(40).mean()
```

**Row count:** still 2097  
**First valid MA date:** 2020-09-29 (needs 40 non-NaN lag values; lag itself starts 2020-08-21, so first MA = day index of lag_start + 39)

Neighbors around first valid MA:

| date | close_log_return | close_log_return_lag_1 | close_log_return_ma_lag_1 |
|---|---|---|---|
| 2020-09-27 | 0.0038614577279486415 | 0.00401681997351734 | NaN |
| 2020-09-28 | -0.007129739654819151 | 0.0038614577279486415 | NaN |
| 2020-09-29 | 0.013517171693305283 | -0.007129739654819151 | **-0.0023896621724508868** |
| 2020-09-30 | -0.005923201028802653 | 0.013517171693305283 | -0.002250702679586063 |
| 2020-10-01 | -0.015001029468572277 | -0.005923201028802653 | -0.0017161566512610318 |

Last 3:

| date | close_log_return | close_log_return_lag_1 | close_log_return_ma_lag_1 |
|---|---|---|---|
| 2026-05-14 | 0.021968487193022558 | -0.014724008037606586 | 0.004229928925794629 |
| 2026-05-15 | -0.02474721405139055 | 0.021968487193022558 | 0.004659176045235486 |
| 2026-05-16 | -0.013266981789791518 | -0.02474721405139055 | 0.0034078106645840127 |

---

## Step 3 — Enter `backtest_model` → `df.dropna()` (author line 45)

```python
features = ['close_log_return_lag_1', 'close_log_return_ma_lag_1']
target = 'close_log_return'
df = btcusdt.dropna()   # drops any row with NaN in ANY column present
```

**Row count after dropna:** **2056**  
(2097 raw − 2 from return/lag warm-up − 39 additional from rolling(40) on lag = 2056)

First 3 post-dropna:

| date | close_log_return_lag_1 | close_log_return_ma_lag_1 | close_log_return |
|---|---|---|---|
| 2020-09-29 | -0.007129739654819151 | -0.0023896621724508868 | 0.013517171693305283 |
| 2020-09-30 | 0.013517171693305283 | -0.002250702679586063 | -0.005923201028802653 |
| 2020-10-01 | -0.005923201028802653 | -0.0017161566512610318 | -0.015001029468572277 |

Last 3:

| date | close_log_return_lag_1 | close_log_return_ma_lag_1 | close_log_return |
|---|---|---|---|
| 2026-05-14 | -0.014724008037606586 | 0.004229928925794629 | 0.021968487193022558 |
| 2026-05-15 | 0.021968487193022558 | 0.004659176045235486 | -0.02474721405139055 |
| 2026-05-16 | -0.02474721405139055 | 0.0034078106645840127 | -0.013266981789791518 |

Equivalent if we restrict columns first (same n=2056):

```python
df_b = btcusdt[['c', 'close_log_return', 'close_log_return_lag_1', 'close_log_return_ma_lag_1']].copy()
df_b = df_b.dropna()
```

---

## Step 4 — `train_test_split` (author line 47)

```python
df_train, df_test = train_test_split(df, test_size=0.25, shuffle=False)
```

| | n | first date | last date |
|---|---|---|---|
| **df_train** | **1542** | 2020-09-29 | 2024-12-18 |
| **df_test** | **514** | 2024-12-19 | 2026-05-16 |

Check: `1542 + 514 = 2056`, `514/2056 ≈ 0.24999` (sklearn’s floor/ceil split of 0.25).

Train head (features + target):

| date | lag_1 | ma_lag_1 | close_log_return |
|---|---|---|---|
| 2020-09-29 | -0.007129739654819151 | -0.0023896621724508868 | 0.013517171693305283 |
| 2020-09-30 | 0.013517171693305283 | -0.002250702679586063 | -0.005923201028802653 |
| 2020-10-01 | -0.005923201028802653 | -0.0017161566512610318 | -0.015001029468572277 |

Train tail:

| date | lag_1 | ma_lag_1 | close_log_return |
|---|---|---|---|
| 2024-12-16 | 0.030525019423766866 | 0.01026296892210804 | 0.01445863185697168 |
| 2024-12-17 | 0.01445863185697168 | 0.008475937533617285 | -0.00014129549149594377 |
| 2024-12-18 | -0.00014129549149594377 | 0.008378385967790992 | -0.057014902107618226 |

---

## Step 5 — Build X_train / y_train (author lines 49–51)

```python
X_train = df_train[['close_log_return_lag_1', 'close_log_return_ma_lag_1']]
y_train = df_train['close_log_return']
```

| object | shape | dtype(s) |
|---|---|---|
| X_train | **(1542, 2)** | float64, float64 |
| y_train | **(1542,)** | float64 |

X_train first 3 rows as raw arrays:

```text
[[-0.007129739654819151, -0.0023896621724508868],
 [ 0.013517171693305283, -0.002250702679586063 ],
 [-0.005923201028802653, -0.0017161566512610318]]
```

y_train first 3:

```text
[0.013517171693305283, -0.005923201028802653, -0.015001029468572277]
```

X_train last 3:

```text
[[ 0.030525019423766866,  0.01026296892210804  ],
 [ 0.01445863185697168 ,  0.008475937533617285 ],
 [-0.00014129549149594377, 0.008378385967790992]]
```

y_train last 3:

```text
[0.01445863185697168, -0.00014129549149594377, -0.057014902107618226]
```

Train-set correlation (for context, not used in fit):

```text
corr(lag_1, ma_lag_1) ≈ 0.183
cond(X_train) ≈ 5.54   # well-conditioned — not a multicollinearity explosion
```

---

## Step 6 — `LinearRegression().fit` (author lines 51–53)

```python
model = LinearRegression()          # fit_intercept=True (default), positive=False
model.fit(X_train, y_train)
print(model.coef_, model.intercept_)
```

**Result:**

```text
coef_      = [-0.03820891898454995,  0.32349523294151594]
intercept_ =  0.0010550240542074696
coef_.dtype = float64
```

Cross-check with `np.linalg.lstsq` on `[1, X]` — identical beta within float noise:

```text
lstsq beta = [0.00105502, -0.03820892, 0.32349523]
```

### Comparison to his print

| | His print | Ours (this trail) |
|---|---|---|
| coef_[0] (lag) | -0.03028802 | -0.03820892 |
| coef_[1] (MA) | **-3.2349553** | **+0.32349523** |
| intercept_ | 0.00585814582674094 | 0.0010550240542074696 |

**MA term: sign flip and ~10× magnitude.**  
Note: `|ours_MA| * 10 = 3.2349523` vs his `3.2349553` (abs diff ≈ 3e-6). Speculative — see §Speculation below.

---

## Step 7 — Predict full df, signal, equity (author lines 55–59)

```python
backtest = df.copy()
backtest['y_hat'] = model.predict(backtest[features])   # full 2056 rows, train+test
backtest['signal'] = np.sign(backtest['y_hat'])
backtest['trade_log_return'] = backtest['close_log_return'] * backtest['signal']
backtest['cum_trade_log_return'] = backtest['trade_log_return'].cumsum()
backtest['signal'].value_counts()
```

| signal | count |
|---|---|
| +1.0 (Buy) | **1612** |
| -1.0 (Sell) | **444** |
| 0.0 | 0 |

| metric | value |
|---|---|
| final cum trade_log_return | 2.9267968605684933 |
| win rate `(sign(trade_log_return)>0).mean()` | 0.5097276264591439 (50.97%) |

y_hat first 3: `[0.0005543993779308589, -0.0001895440515370713, 0.0007261746667823737]`  
y_hat last 3: `[0.002985974327620232, 0.001722853146905132, 0.0031029988557505547]`

His printed signals for “Model B”: Buy=1680, Sell=307.  
Transcript (~13:56–14:04) says after the *combined* step downs went to **“over 400”** (previously ~300) — our **444** matches that spoken description better than the printed 307.

---

## Speculative: what could differ from a straight notebook port

*(Labeled speculative — not confirmed findings. For the video-AI to check against actual cells.)*

1. **Cell order / which `value_counts` belongs to which model.**  
   Reference code runs MA-alone (line 77) then combined (line 83). Our MA-alone on this file: Buy=1689, Sell=367, coef=`[0.2844]`. Printed “B” signals Buy=1680/Sell=307 are closer in *shape* to MA-alone (still not exact) than to combined (1612/444). Transcript says combined has **>400** sells — conflicts with printed 307 for combined.

2. **MA coefficient decimal / sign misread.**  
   Our MA coef `+0.32349523`; ×10 → `3.2349523` ≈ his `3.2349553` (3e-6 abs). Speculative video OCR / on-screen float formatting issue + sign error. Does **not** explain lag coef or intercept by the same rule.

3. **Shared dataframe mutation.**  
   If he `dropna()`’d in place earlier, or re-filtered `btcusdt` between Model A and B, train n would change. Our trail assumes the reference code’s non-destructive `df = df.dropna()` inside the function only.

4. **Different second feature than `rolling(40).mean()` of lag.**  
   We brute-forced windows, var/std/sum/ewm/zscore/lag−ma, pct vs log, feature order swap, Ridge/Huber, center=True, min_periods, float32, full-sample fit, inverted split. **None** reproduced his full `(coef, intercept)` tuple on this CSV. Variance features can get MA-slot coef ≈ −3.23 but then lag coef and intercept still miss, and that is **not** what his reference code writes.

5. **sklearn / numpy version.**  
   Closed-form OLS should be stable here (`cond(X)≈5.5`). Unlikely source of a sign flip on a well-conditioned 2-feature problem.

6. **He describes combined model as “weighted difference of current log return against MA.”**  
   That is an *interpretation* of signs of `[lag, ma]` coefficients (e.g. positive MA weight = momentum of the smoother), not evidence he engineered `lag - ma` as an input. We did try `lag + (lag - ma)` as features → coefs `[0.285, -0.323]`, still not his print.

---

## End of Model B trail

Next human/AI check on video frames should focus on:

1. The exact `print(model.coef_, model.intercept_)` cell output for the **combined** (two-feature) fit — digits and sign of the second coefficient.  
2. Whether Sell=307 / Buy=1680 is printed after MA-alone or after combined.  
3. Whether `rolling(40).mean()` is literally on `close_log_return_lag_1` in the executed cell (vs a hidden alternate feature).
