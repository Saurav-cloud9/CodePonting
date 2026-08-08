# Updated Validation Summary — NIFTY50 Model B Gate on fv2 SHORT (2026-08-06)

Consolidates the post-data-refresh re-validation of the NIFTY50-Model-B-as-gate
finding from step 32, plus the WFA (step 33) results, using pooled (money-
weighted) ZPF throughout — not mean-of-ratios, which we established overstates
how close to breakeven things look.

## Context

Step 32's original 30-stock sweep (mean ZPF=1.008, 10/30 stocks ≥1.0) was run
before Grok's DS3 gap-fill extended NIFTY50/DS3 data through 2026-07-31. Once
the data was extended, the Train/Test split boundary shifted (2023-04-28 →
2023-10-04 for the same 75/25 ratio), and the "best gate" result needed
re-checking — both on the updated single split, and via full Walk-Forward
Analysis (multiple independent rolling windows, not just one arbitrary split).

## 1. Old vs. updated single 75/25 split (pooled, all 30 stocks, SHORT only, gated)

| | Old (step 32, pre-refresh) | Updated (post-refresh) |
|---|---|---|
| Test period | ends 2025-12-31 (split @ 2023-04-28) | ends 2026-07-31 (split @ 2023-10-04) |
| Metric used | mean ZPF (per-stock average) | **pooled ZPF** (money-weighted) |
| Result | mean=1.008, median=0.935, 10/30 ≥1.0 | **pooled_zpf=0.734**, total_zpnl=-894.61, n=1103 |

Note: these aren't directly comparable (different metric, different data) — the
old "mean=1.008" was already shown to overstate reality once pooled properly;
recomputing step 32's old data with pooled ZPF would likely also come in
below 1.0. The updated, properly-pooled, most-current-data number is the one
that matters: **0.734**, i.e. a real net loss (-₹894.61) across 1103 gated
trades, all 30 stocks, Test = 2023-10-04 → 2026-07-31.

## 2. Walk-Forward Analysis (step 33) — per-fold pooled ZPF

Full details: `33_wfa_config1_results.csv`, `33_wfa_config2_results.csv`,
`33_wfa_summary.md`. Both configs use fixed-size rolling windows (NOT
expanding), refit fresh at each fold, no lookahead.

**Config 1 — 3yr Train / 1yr Test, 9 folds:**

| Fold | Test window | Total N (30 stocks) | Total ZPnL | Pooled ZPF |
|---|---|---|---|---|
| 1 | 2018-02→2019-01 | 2694 | -283.45 | 0.492 |
| 2 | 2019-02→2020-01 | 2483 | -841.99 | 0.225 |
| 3 | 2020-02→2021-01 | 4473 | -1241.07 | 0.092 |
| 4 | 2021-02→2022-01 | 2843 | -2184.61 | 0.008 |
| 5 | 2022-02→2023-01 | 2681 | -1887.32 | 0.025 |
| 6 | 2023-02→2024-01 | 1515 | -1122.46 | 0.004 |
| 7 | 2024-02→2025-01 | 455 | -396.06 | 0.339 |
| 8 | 2025-02→2026-01 | 1477 | -1110.60 | 0.059 |
| 9 | 2026-02→2026-07 | 116 | -11.29 | 0.913 |

Every single fold net-negative. (Fold 9 also has very low N=116 — treat with
extra caution, it's the partial final window.)

**Config 2 — 5yr Train / ~20mo Test, 4 folds:**

| Fold | Test window | Total N (30 stocks) | Total ZPnL | Pooled ZPF |
|---|---|---|---|---|
| 1 | 2020-02→2021-09 | 8692 | -2850.12 | 0.023 |
| 2 | 2021-10→2023-05 | 3669 | -2650.80 | 0.011 |
| 3 | 2023-06→2025-01 | 1783 | -1285.72 | 0.078 |
| 4 | 2025-02→2026-07 | 3026 | -3180.78 | 0.007 |

Also every single fold net-negative.

## 3. Conclusion

- Every WFA fold (13 total across both configs) is net-negative when pooled
  by real money. Pooled ZPF never even approaches 1.0 in any fold (best case
  0.913, most folds well under 0.1-0.5).
- The single-split result, recomputed properly on current data, is also
  net-negative (0.734, -₹894.61) — better than most individual WFA folds
  (supports "more training history helps somewhat"), but still clearly a
  losing strategy, not a validated edge.
- **Verdict: the NIFTY50-Model-B-as-day-level-gate approach does not show a
  genuine, repeatable edge on fv2's SHORT strategy.** The earlier single-split
  "winners" (NATIONALUM, PNB, VEDL, BANDHANBNK, TATAMOTORS) were artifacts of
  one favorable split boundary and, in most cases, one single historical
  event (2024-06-04 election-result crash), not real skill.
- Next avenue (per session discussion): Pearson's r feature screening against
  `close_log_return` as the target, and/or Logistic Regression as a
  better-matched method (trained to separate up/down directly, instead of a
  regression-then-threshold approach) — but any new finding from either must
  go through this same WFA rigor before being trusted.
