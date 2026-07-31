# Iteration Log — MA Bounce / Rejection Baseline Explorations
**Universe:** 30 NSE stocks · 5-min bars  
**Signal:** MA20 touch → bounce/rejection within MAX_GAP=3 bars → entry next bar open  
**Scripts:** ma_30_rejection.py (SHORT) · ma_30_bounce.py (LONG)

---

## Fixes Applied (vs initial run)
- Next-day bleed fix — date-change exits at prev bar's close, not next bar's open
- Timezone strip — BAJFINANCE CSV had +05:30 aware datetimes causing false 9:30 AM exits
- BAJFINANCE CSV indicators — ma20/atr14 recomputed from DS3 parquet (pre-warmed, was blank for first 19 rows)
- Exit priority — SL checked before TP (conservative: same-bar ambiguity resolved to loss)
- Naming — MAX_TB_GAP → MAX_TR_GAP in rejection file

---

## SL/TP Sweep
**Date:** 2026-07-09 · **Scripts:** sweep/sl_tp_sweep_short.py · sweep/sl_tp_sweep_long.py  
**Range:** SL ∈ [1.5–6.0] · TP ∈ [2.0–6.0] · 90 combinations each · Data: 4-yr CSVs (combo validated on DS3 in Run 1 — delta <0.3%)

### SHORT sweep
Grid flat (PF 1.062–1.086). TP=4.0 consistently peaks across all SL values.

| Combo | N | PF | Sharpe | Decision |
|---|---|---|---|---|
| SL=2.5 · TP=4.5 (original) | 47,933 | 1.081 | 1.516 | replaced |
| SL=2.5 · TP=4.0 | 49,600 | 1.083 | 1.583 | ✅ locked |
| SL=5.0 · TP=4.0 (grid best PF) | 39,432 | 1.086 | 1.329 | ❌ −18% trades, worst Sharpe |

### LONG sweep
No profitable combo anywhere in the grid. Max PF = 0.933.

| Combo | N | PF | Sharpe | Decision |
|---|---|---|---|---|
| SL=2.5 · TP=4.5 (original) | 49,269 | 0.922 | -1.468 | replaced |
| SL=2.0 · TP=5.5 | 52,887 | 0.933 | -1.310 | ✅ locked (best available) |

---

## Run 1 — 4-Year (2022–2025) · DS3 Parquets · Best Combos
**Date:** 2026-07-09 · **Data:** intraday_5min_DS3 parquets filtered to 2022-01-01+

### SHORT — SL=2.5 · TP=4.0
| Metric | Value |
|---|---|
| N | 49,473 |
| PF | 1.080 |
| Sharpe | +1.546 |
| Net (pts) | +8,263.68 |
| Prof_WR | 45.8% |
| Pure_WR (TP hit) | 20.0% |
| BE_pure needed | 38.5% |

| Year | N | PF | Sharpe | Net |
|---|---|---|---|---|
| 2022 | 11,986 | 1.127 | +2.315 | +2,852.53 |
| 2023 | 11,988 | 1.033 | +0.645 | +641.22 |
| 2024 | 12,422 | 1.095 | +1.736 | +2,912.33 |
| 2025 | 13,077 | 1.062 | +1.314 | +1,857.59 |

### LONG — SL=2.0 · TP=5.5
| Metric | Value |
|---|---|
| N | 52,687 |
| PF | 0.934 |
| Sharpe | -1.319 |
| Net (pts) | -7,176.37 |
| Prof_WR | 37.4% |
| Pure_WR (TP hit) | 9.8% |
| BE_pure needed | 26.7% |

| Year | N | PF | Sharpe | Net |
|---|---|---|---|---|
| 2022 | 13,166 | 0.924 | -1.884 | -1,915.02 |
| 2023 | 12,933 | 0.918 | -1.352 | -1,724.79 |
| 2024 | 13,005 | 0.927 | -1.297 | -2,406.14 |
| 2025 | 13,583 | 0.963 | -0.860 | -1,130.42 |

---

## Run 2 — 11-Year (2015–2025) · DS3 Parquets · Best Combos ✅ FINAL BASELINE
**Date:** 2026-07-09 · **Data:** intraday_5min_DS3 parquets  
**Why switched:** CSVs missing Dec 31 2025 · parquets identical OHLCV + 7 extra years + indicators pre-warmed

### SHORT — SL=2.5 · TP=4.0
| Metric | Value |
|---|---|
| N | 133,696 |
| PF | 1.116 |
| Sharpe | +2.049 |
| Net (pts) | +24,300.35 |
| Prof_WR | 46.0% |
| Pure_WR (TP hit) | 20.8% |
| BE_pure needed | 38.5% |
| Stocks profitable | 29/30 (only HDFCBANK 0.976) |

| Year | N | PF | Sharpe | Net |
|---|---|---|---|---|
| 2015 | 11,163 | 1.175 | +2.818 | +1,883.06 |
| 2016 | 12,065 | 1.137 | +2.231 | +1,455.04 |
| 2017 | 11,944 | 1.129 | +2.438 | +1,331.86 |
| 2018 | 12,347 | 1.180 | +2.996 | +2,701.06 |
| 2019 | 12,495 | 1.157 | +2.653 | +2,394.48 |
| 2020 | 12,078 | 1.137 | +1.937 | +2,772.44 |
| 2021 | 12,131 | 1.147 | +3.326 | +3,498.71 |
| 2022 | 11,986 | 1.127 | +2.315 | +2,852.53 |
| 2023 | 11,988 | 1.033 | +0.645 | +641.22 |
| 2024 | 12,422 | 1.095 | +1.736 | +2,912.33 |
| 2025 | 13,077 | 1.062 | +1.314 | +1,857.59 |

### LONG — SL=2.0 · TP=5.5
| Metric | Value |
|---|---|
| N | 142,759 |
| PF | 0.907 |
| Sharpe | -1.801 |
| Net (pts) | -21,252.88 |
| Prof_WR | 35.9% |
| Pure_WR (TP hit) | 9.8% |
| BE_pure needed | 26.7% |
| Stocks profitable | 0/30 |

| Year | N | PF | Sharpe | Net |
|---|---|---|---|---|
| 2015 | 11,701 | 0.885 | -3.258 | -1,335.27 |
| 2016 | 12,760 | 0.902 | -1.920 | -1,135.39 |
| 2017 | 13,057 | 0.861 | -3.162 | -1,640.36 |
| 2018 | 13,131 | 0.885 | -2.290 | -1,953.78 |
| 2019 | 13,141 | 0.851 | -2.700 | -2,569.37 |
| 2020 | 13,072 | 0.907 | -1.433 | -2,039.82 |
| 2021 | 13,210 | 0.873 | -3.213 | -3,402.50 |
| 2022 | 13,166 | 0.924 | -1.884 | -1,915.02 |
| 2023 | 12,933 | 0.918 | -1.352 | -1,724.79 |
| 2024 | 13,005 | 0.927 | -1.297 | -2,406.14 |
| 2025 | 13,583 | 0.963 | -0.860 | -1,130.42 |

**Notes:**  
SHORT — PF>1.0 all 11 years. Edge structural, not period-specific. 2023 weakest (1.033) but still positive.  
LONG — PF<1.0 all 11 years. No combo profitable. MA acts as resistance in this universe, not support.

---

## v1 — ma_30_rejection_v1.py
*Pending.*
