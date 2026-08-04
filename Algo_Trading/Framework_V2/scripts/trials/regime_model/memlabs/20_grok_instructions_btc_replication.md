# MemLabs Model Replication on Real BTCUSDT Data — Instructions for Grok

## Goal
Replicate the MemLabs author's exact code on his actual intended dataset (BTCUSDT daily,
Binance), since his original GitHub-hosted CSV URL 404'd. His exact date range is now
confirmed on-screen (frame-by-frame): **2020-08-19 to 2026-05-16**. Cross-check our output
against his own exact printed numbers using this exact date range as the primary
comparison — our numbers should land close to his, not just "same ballpark," since we now
have his real date bounds rather than an estimate.

**Exactly 3 models to build. Do not build anything else.** Out of the 5 concepts in the
video, 2 are explicitly excluded:
- **Sliding Window** — discussed conceptually only, the author never backtests it. Skip.
- **Reinforcement Learning (REINFORCE)** — a separate toy coin-toss demo, never applied to
  BTC price data at all. Skip — not relevant to this exercise.

## Data source
Binance public REST API, no auth needed:
`https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=<ms>&limit=1000`
- Confirmed reachable and returns data back to **2017-08-17**.
- Paginate with `startTime` in milliseconds since epoch, 1000 rows per call, until you
  reach today. Each row: `[open_time, open, high, low, close, volume, close_time, ...]`
  (Binance kline format) — use `close_time` or `open_time` as the date, `close` (index 4)
  as the closing price.
- Save the assembled daily OHLC to a CSV in this folder: `BTCUSDT_1d_binance.csv`
  (columns: `date, open, high, low, close, volume`).

## Reference code — build from this, do not deviate from the math
`18_regime_change_author_reference_code.py` (this same folder) contains the author's
verbatim extracted code.

**Shared setup (lines 39-41):**
```
close_log_return = np.log(close / close.shift())
close_log_return_lag_1 = close_log_return.shift()
```

### Model A — Base AR (line 65)
`backtest_model(df, features=['close_log_return_lag_1'], target='close_log_return')`
using the `backtest_model()` function verbatim from lines 44-62 (train_test_split
`shuffle=False`, `test_split=0.25`, LinearRegression, `signal=sign(y_hat)`,
`trade_log_return = close_log_return * signal`, cumulative sum, predicted over the
**full** df — train+test combined, per his own code).

### Model B — Encoding Memory / combined (line 83)
Same `backtest_model()` function, but features =
`['close_log_return_lag_1', 'close_log_return_ma_lag_1']` (BOTH together — this is his
"relative memory" step, ~12:25 in the transcript, NOT the MA-alone intermediate at line 77).
`close_log_return_ma_lag_1` = `rolling(40).mean()` of the **lag** series (not of
`close_log_return` directly — his own transcript flags this as a data-leakage trap).
Do not separately build the MA-alone-only variant (line 77) — we have no clean reference
number for it, only for this combined version.

### Model C — Online Learning (lines 91-166, a DIFFERENT algorithm, not backtest_model())
This is NOT a LinearRegression / backtest_model() call. Copy the actual streaming loop:
`SGDRegressor(loss="epsilon_insensitive", epsilon=0.0002, penalty=None,
learning_rate="pa1", eta0=0.01, random_state=69)` + `StandardScaler()`, feature =
`close_log_return_lag_1` only, target = `close_log_return`. Per-row loop: `partial_fit`
the scaler, transform, predict (cold-start pred=0.0 at t=0), record sign_match, THEN
`partial_fit` the model on that same row. Compute `sign_match` hit rate exactly as his
code does (excluding the `t==0` warmup row from the hit-rate calculation).

## Where to save your work — explicit filenames (do not run ad-hoc/unsaved)
Save ALL of the following in this same folder
(`Algo_Trading/Framework_V2/scripts/trials/regime_model/memlabs/`), nowhere else:
- `20_fetch_btc_data.py` — the Binance-pagination fetch script, producing `BTCUSDT_1d_binance.csv`
- `20_btc_models_replication.py` — the model-building script (data load, feature
  engineering, Models A/B/C, metric computation, saves the 3 PNGs)
- `20_btc_models_results.md` — the results doc (see "Required" section below)
- `20_btc_model_A.png` / `20_btc_model_B.png` / `20_btc_model_C.png` — one plot per model
Do not run any of this as a one-off inline command without saving the script first — we've
already lost work this way earlier in this project and don't want a repeat.

## What to report for each of the 3 models
1. Model A & B: `model.coef_` and `model.intercept_`. Model C: N/A (weights change every
   tick — instead report the final tick's weight/bias as a snapshot).
2. Signal value_counts (+1 vs -1 vs 0)
3. Final cumulative `trade_log_return` (equity curve endpoint)
4. Model A & B: win rate = `(np.sign(trade_log_return) > 0).mean()`. Model C: the exact
   `sign_match` hit rate his code computes (`% of 'YES' among evaluated rows`).
5. Save one equity-curve PNG per model (cumulative `trade_log_return` vs raw close price
   for comparison), dark-background style: `20_btc_model_A.png` / `_B.png` / `_C.png`

## What we're checking this against — his EXACT printed numbers (extracted from video, not paraphrased)

| Model | Weights (coef_, intercept_) | Signal value_counts | Hit rate |
|---|---|---|---|
| A (base AR) | `[-0.02902972]`, `0.0014044601590437902` | Buy(+1)=1991, Sell(-1)=104 | — (95.0% buy) |
| B (memory, combined) | `[-0.03820892, 0.32349523]`, `0.0010550240542074694` | Buy(+1)=1612, Sell(-1)=444 | ~50.97% |
| C (online PA1) | dynamic, changes per-tick | Sell(-1)=1036, Buy(+1)=1017 | **50.82%** (his exact printed value) |

*(CORRECTED 2026-08-03: Models A and B above were originally misread by Google AI Studio's
frame extraction — see `19_memlabs_btc_numbers_reference.md` and
`20_btc_models_results.md` for the full correction. Model C's numbers have not yet been
screenshot-verified and may still contain a similar error.)*

**His exact dataset date range is now confirmed (frame-by-frame, on-screen), not estimated:**
`2020-08-19` to `2026-05-16`, 2,097 raw rows. Run the 3 models TWICE:
1. **Exact date-matched run**: filter our Binance pull to `2020-08-19` through `2026-05-16`
   inclusive, before doing anything else (dropna, feature engineering, etc.). This should
   land very close to his 2,097 raw row count — if it doesn't (off by more than ~5-10 rows),
   flag this explicitly, don't silently proceed.
2. **Full-history run**: 2017-08-17 to today, for context/completeness.
Report both sets of numbers side by side. The exact date-matched run is the PRIMARY
comparison — it should be much closer to his numbers than a full-history run would be,
since the fitted data now matches his as closely as we can get it. Note: even with exact
matching dates, our numbers may not be byte-identical to his (Binance's own price series
may differ slightly from whatever exchange/aggregator his source CSV pulled from) — but
they should be very close, not just "same neighborhood."

He explicitly states **no hyperparameter optimization was done** on any of these — don't
tune anything, run the code as-is.

**Required in `20_btc_models_results.md`**: an explicit comparison table, one row per
model, with columns `Metric | His exact value | Ours (exact date-matched 2020-08-19 to 2026-05-16) | Ours (full 2017-2026) | Match? (Y/N/Partial)`.
This is not optional background — it's the actual point of this exercise. Do not just
report our numbers in isolation; state directly whether each model's behavior matches the
qualitative pattern he describes, or diverges from it (and if it diverges, note that
plainly rather than glossing over it).

## UPDATE — his actual literal source CSV has been recovered, use this instead of Binance

The original URL 404'd because of two errors: wrong filename (`BTCUSDT_1d.csv` vs actual
`BTCUSDT-1d.csv`, underscore vs hyphen) and wrong path format (`refs/heads/main` instead of
just `main`). Correct working URL:
`https://raw.githubusercontent.com/memlabs-research/datasets/main/BTCUSDT-1d.csv`

This is confirmed to be his exact file: 2,097 rows, exact date range 2020-08-19 to
2026-05-16, columns `t,T,s,i,o,c,h,l,v,n` (t=date, c=close — use `c` as the close price,
matching his own code's column name exactly, no renaming needed).

**Re-run all 3 models using THIS file as the sole data source** (drop the Binance
date-matched run — keep Binance only for the full-history/context run if you want, but the
primary comparison now uses this file directly, no date filtering needed since it's already
exactly his window).

**Preliminary spot-check already run (quick, not exhaustive) — for your awareness:**
- Model A intercept now matches his to 12 decimal places (`0.00140446015...`), sell count
  matches exactly (104=104). Coef and buy count are closer but still not exact
  (-0.029 vs his -0.0296; 1991 vs 1891 buys) — **investigate**: possible causes include
  exact `train_test_split` boundary (his `test_split=0.25` on which exact n?), float
  precision/dtype, or whether he dropna's on the full multi-column df vs just the two
  columns needed for Model A.
- Model B **still shows a coefficient sign flip on the MA term** even with his exact file
  (ours positive, his `-3.2349553`) — this means the earlier "Binance data difference"
  theory does NOT fully explain Model B's gap, since we now have his literal data and the
  flip persists. This points more toward an order-of-operations or precision difference in
  how the two-feature regression is set up, not a data-source issue. **This is the priority
  item to debug** — check dropna order (does he dropna the whole notebook-state df including
  columns not yet used elsewhere?), check float64 vs any rounding, check exact
  `train_test_split` row split point matches his (same `test_split=0.25`, but is `n` before
  or after dropna the same as his?).

Do this investigation methodically and document what you tried and what changed the result,
even partial progress — don't just report final numbers again without showing the debugging
trail this time.

## NEW REQUIREMENT — produce an exact step-by-step math trail (separate file)

We're going to hand your output to a second AI (Google AI Studio) that has actual
frame-by-frame visual access to the source video — it can see his real notebook cell
execution order, which we can't from a transcript alone. For it to spot what differs, it
needs YOUR exact process laid out the same granular way a notebook would show it, not a
narrative summary.

Produce a new file `20_btc_model_B_math_trail.md` containing, in strict execution order,
for Model B specifically (since that's the unresolved one):
1. Every dataframe operation performed, in the exact order run (e.g. "df['close_log_return']
   = ...", "df['close_log_return_lag_1'] = ...", "df['close_log_return_ma_lag_1'] = ...",
   "df_b = df[[...]].copy()", "df_b = df_b.dropna()", "train_test_split(...)", etc.) —
   literally the sequence of code statements, not a description of what they accomplish.
2. After each step, the resulting row count and, for the first/last 3 rows, the actual
   numeric values of every column at that point (so the shape of the data at each stage is
   fully visible, not just the final fitted model).
3. The exact `LinearRegression().fit()` call — what X/y arrays go in, their shapes, and
   their dtypes.
4. The final `coef_` / `intercept_`, and immediately below them, a plain-English one-line
   description of anything in steps 1-3 that could plausibly differ from a "straight port"
   of his notebook if his cells were run in a different order or against a differently-
   mutated shared dataframe (this is speculative reasoning, so label it as such — not a
   confirmed finding).

Keep this file focused only on Model B's trail — don't repeat A/C here.

## Rules
- Don't add filters, don't tune SL/TP-style parameters (there are none here, this is pure
  price-return AR, not our trading strategy) — this is a data source / methodology
  cross-check, nothing else.
- Do not build Sliding Window or the RL coin-toss demo — explicitly out of scope (see Goal).
- Do not build the MA-alone-only variant (reference code line 77) — only the combined
  version (line 83) has a matching reference number to check against.
- If the Binance API pagination or rate-limiting causes issues, flag it rather than
  silently truncating the date range — we want the full 2017-present history the author's
  chart implies he had access to.
