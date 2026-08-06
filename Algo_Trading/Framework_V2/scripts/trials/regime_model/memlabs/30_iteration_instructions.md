# Iteration Instructions — MemLabs Regime-Signal Exploration (2026-08-05)

## Context
This folder replicates the MemLabs YouTube video's autoregressive/moving-average
models (Model A = lag_1 only, MA-alone = 40-day rolling mean of lag_1, Model B =
both combined) and tests whether they carry real, out-of-sample predictive value —
first on price data directly, then as a day-level regime gate on fv2's real
SHORT (MA-rejection) and LONG (MA-bounce) trade logs.

**Established finding so far (single-stock TATAMOTORS, 30-stock DS3 sweep)**: no
reliable, generalizable edge. Zero of 30 stocks reliably cross ZPF ≥ 1.0; a
flipped-sign-convention control performs statistically the same as the intended
mapping (evidence of noise, not real signal); even the handful of stocks that
crossed 1.0 overall did so only because of one favorable year (2024), not a
consistent year-over-year edge. Full details: `26_regime_gated_analysis_results.md`,
the 28/29 sweep CSVs, and the yearwise breakdown discussed in-session.

This is NOT a dead end — it's evidence the literal video mapping (daily
close-to-close log return, lag-1/40-day-MA features, linear regression) doesn't
transfer cleanly. The unexplored space (different features, different lag
windows, different underlying instruments, non-linear models, soft weighting
instead of a hard gate) is still open.

## The Two-Stage Iteration Pattern

**Stage 1 — Prototype on ONE stock/instrument/feature (notebook, `#24` template)**
`24_fv2_tatamotors_replication.ipynb` is the reference structure:
1. Load daily close price series for the instrument (resample from DS3 5-min if
   it's an individual stock; use directly if already daily, e.g. NIFTY50).
2. Feature engineering: `close_log_return = log(c / c.shift())`,
   `close_log_return_lag_1 = close_log_return.shift()`,
   `close_log_return_ma_lag_1 = close_log_return_lag_1.rolling(40).mean()`.
3. `train_test_curves()` helper: `train_test_split(test_size=0.25, shuffle=False)`
   (chronological, NOT shuffled), fit `LinearRegression()` on Train ONLY, predict
   on Train/Test/combined separately.
4. Run all 3 models (Model A, MA-alone, Model B), report `coef_`/`intercept_`,
   signal `value_counts()`, Train vs Test `cum_trade_log_return` SEPARATELY
   (never blend — Train is in-sample, only Test is genuinely predictive).
5. Plot: equity curve + raw price, both combined-period and Test-only.
6. Summary table: model × Train/Test × n × cum_trade_log_return.

Use this stage to sanity-check a NEW feature or NEW instrument cheaply before
committing to the full sweep. Verify against a known-good number if one exists
(e.g. TATAMOTORS Model A Test cum = 0.1008, N=524 on the 4yr fv2-CSV window —
see notebook 22/24 history) before trusting a new run.

**Stage 2 — Full sweep across all 30 DS3 stocks (`#28`/`#29` template)**
`28_regime_gate_30stock_sweep.py` (original mapping) and
`29_regime_gate_30stock_sweep_flipped.py` (sign-flip control) are the reference
scripts. Structure:
1. Loop over all 30 DS3 symbols (list is in `SYMBOLS` at the top of the script —
   START with `SYMBOLS = ['TATAMOTORS']` and verify against known-good numbers
   before switching to the full 30-symbol list, per the comment in the file).
2. Per symbol: build SHORT trade log (imports `process_bar`/`StockState` from
   `kite_oracle_papertrading/scripts/ma_rejection_v1_core.py` — the ACTUAL live
   bot logic, not a re-implementation), build LONG trade log (hand-rolled,
   matches `Framework_V2/scripts/trials/baseline_explorations/ma_30_bounce_v1.py`'s
   wick-only-touch logic, SL=2.0x/TP=5.5x).
3. Fit the 3 regime models per stock (own coefficients per stock — do NOT reuse
   one stock's coefficients on another).
4. Gate: on Sell-signal days, count only SHORT trades; on Buy-signal days, count
   only LONG trades. Report Train/Test separately, SHORT/LONG/COMBINED
   baseline vs gated, PF and ZPF (Zerodha-cost-adjusted PnL/PF — see
   `zerodha_short()`/`zerodha_long()` in the script for the exact charge
   formula, matches `ma_30_rejection_v1.py`'s cost model).
5. Output: ONE long-format CSV, all stocks stacked with a `symbol` column — NOT
   30 separate files, NOT an Excel workbook with per-stock sheets.
6. Print only a trimmed summary (best gate per stock, ~30 lines) to avoid
   dumping the full 1000+ row table into the terminal/context — full detail
   stays in the saved CSV.

**Known gotcha (bit us twice this session)**: DS3 has bad zero-price ticks on
some stocks (e.g. ICICIBANK, 825 rows). Null out non-positive OHLC values right
at load time (`df.loc[df[col] <= 0, col] = np.nan`) before any log-return or
indicator computation — otherwise `log(price/0)` produces `inf` and crashes
`LinearRegression.fit()`.

## What to try next (open, unexplored)

- **New instruments**: NIFTY50 (daily parquet now at
  `Framework_V2/data/historical/daily/NIFTY50.parquet`, 2016-01-01 → present,
  ~10.5yr — fetched via Kite MCP, Kite's day-candle lookback limit is ~10yr,
  earlier dates fail) as a broader, less noisy regime signal than any single
  stock. Gate ALL 30 stocks' trades using ONE shared NIFTY50-derived signal
  instead of each stock computing its own (noisier) signal — this removes the
  per-stock-signal noise floor as a confound.
- **Different lag windows** for the MA feature (10/20/30/40/50/60/90/120 —
  partially explored already for MA-alone/Model B specifically, see
  `23_ma_window_sweep_results.md`; not yet tried for a NIFTY50-based signal).
- **Different features entirely**: volume, ATR%, realized volatility, or
  cross-sectional features (how a stock is doing relative to NIFTY50) instead
  of pure own-price log-return autocorrelation.
- **Non-linear models**: the video's Model C (Online Learning / Passive-
  Aggressive Regressor) is still unstarted — deprioritized this session in
  favor of exhausting the linear-model space first, and because it's higher
  complexity for likely the same underlying noise ceiling (see in-session
  discussion). Revisit only if a linear approach shows real promise first.
- **Soft weighting instead of hard gate**: instead of a binary
  include/exclude, weight position size by signal confidence — untried.

## Rules for whoever picks this up (Grok or otherwise)

- Always run Stage 1 (single stock/instrument, notebook `#24` template) and
  verify against a known-good number before Stage 2 (30-stock sweep).
- Always report Train and Test separately. Never blend them into one number.
  Train-period signal is fit on that exact data (in-sample) — it is not
  evidence of real predictive power on its own.
- Always check a flipped-sign-convention control (like `#29`) when reporting a
  new "edge" — if flipping the gate direction performs statistically the same,
  that's evidence of noise, not signal (this caught us once already on the
  literal video mapping).
- Always check the yearwise breakdown before trusting an aggregate Test-period
  number ≥ 1.0 — a multi-year aggregate can be carried by one favorable year
  (this also caught us once already — see NATIONALUM/TATAMOTORS/NTPC discussion).
- ZPnL/ZPF = Zerodha-cost-adjusted PnL/Profit Factor (full charges applied),
  NOT the same as raw PF. Report both, but ZPF is the one that matters for
  real tradeability.
- New file = new task/deliverable gets the next sequential number (currently
  at 30/31 as of this doc). Multiple files belonging to ONE task (a script +
  its own output plots/CSVs/docs) share that task's number — don't invent a
  new number for every output file.
