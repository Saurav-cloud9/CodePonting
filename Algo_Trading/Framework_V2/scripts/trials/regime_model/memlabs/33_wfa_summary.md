# 33 — WFA NIFTY50 Model B gate on SHORT trades

Generated: 2026-08-06 19:17:31

## Setup

- **Signal**: NIFTY50 daily Model B (`close_log_return_lag_1` + `close_log_return_ma_lag_1` → `close_log_return`), fit **per fold on Train only**, `signal = sign(y_hat)`.
- **Gate**: count a stock SHORT trade only if NIFTY signal that day is Sell (−1).
- **Trades**: full-history SHORT log once per stock via `ma_rejection_v1_core.py`; filtered by Test `entry_dt` per fold.
- **Costs**: `zerodha_short()` same as scripts 25–29/32.
- **Data end**: 2026-07-31 (final fold Test may be partial).

### Config 1 folds (9) — 3yr Train / 1yr Test, slide 1yr

- Fold 1: Train 2015-02-01 → 2018-02-01, Test 2018-02-01 → 2019-01-31
- Fold 2: Train 2016-02-01 → 2019-02-01, Test 2019-02-01 → 2020-01-31
- Fold 3: Train 2017-02-01 → 2020-02-01, Test 2020-02-01 → 2021-01-31
- Fold 4: Train 2018-02-01 → 2021-02-01, Test 2021-02-01 → 2022-01-31
- Fold 5: Train 2019-02-01 → 2022-02-01, Test 2022-02-01 → 2023-01-31
- Fold 6: Train 2020-02-01 → 2023-02-01, Test 2023-02-01 → 2024-01-31
- Fold 7: Train 2021-02-01 → 2024-02-01, Test 2024-02-01 → 2025-01-31
- Fold 8: Train 2022-02-01 → 2025-02-01, Test 2025-02-01 → 2026-01-31
- Fold 9: Train 2023-02-01 → 2026-02-01, Test 2026-02-01 → 2026-07-31

### Config 2 folds (4) — 5yr Train / 20mo Test, slide 20mo

- Fold 1: Train 2015-02-01 → 2020-02-01, Test 2020-02-01 → 2021-09-30
- Fold 2: Train 2016-10-01 → 2021-10-01, Test 2021-10-01 → 2023-05-31
- Fold 3: Train 2018-06-01 → 2023-06-01, Test 2023-06-01 → 2025-01-31
- Fold 4: Train 2020-02-01 → 2025-02-01, Test 2025-02-01 → 2026-07-31

CONFIG 1 (3yr/1yr, 9 folds) -- pooled across all 30 stocks per fold:
 fold_num test_start   test_end  total_n  total_zpnl  pooled_zpf
        1 2018-02-01 2019-01-31     2694     -283.45       0.492
        2 2019-02-01 2020-01-31     2483     -841.99       0.225
        3 2020-02-01 2021-01-31     4473    -1241.07       0.092
        4 2021-02-01 2022-01-31     2843    -2184.61       0.008
        5 2022-02-01 2023-01-31     2681    -1887.32       0.025
        6 2023-02-01 2024-01-31     1515    -1122.46       0.004
        7 2024-02-01 2025-01-31      455     -396.06       0.339
        8 2025-02-01 2026-01-31     1477    -1110.60       0.059
        9 2026-02-01 2026-07-31      116      -11.29       0.913

CONFIG 2 (5yr/20mo, 4 folds) -- pooled across all 30 stocks per fold:
 fold_num test_start   test_end  total_n  total_zpnl  pooled_zpf
        1 2020-02-01 2021-09-30     8692    -2850.12       0.023
        2 2021-10-01 2023-05-31     3669    -2650.80       0.011
        3 2023-06-01 2025-01-31     1783    -1285.72       0.078
        4 2025-02-01 2026-07-31     3026    -3180.78       0.007

## Consistency table

Per stock, per config: how many folds have **ZPF ≥ 1.0**, mean/median ZPF, and whether edge is concentrated (max fold ZPF share of positive-ZPF mass, or top-2 folds dominate).

### Config 1 (3yr/1yr)

| symbol | folds | n_folds_zpf>=1 | mean_zpf | median_zpf | mean_n | total_zpnl | concentration |
|--------|------:|---------------:|---------:|-----------:|-------:|-----------:|---------------|
| BANDHANBNK | 9 | 5 | 1.223 | 1.281 | 65.1 | 85.64 | 1-fold (114% zpnl) |
| POWERGRID | 9 | 4 | 1.093 | 0.875 | 64.4 | -22.61 | none/neg |
| TATAMOTORS | 9 | 4 | 0.932 | 0.925 | 70.0 | -2.57 | none/neg |
| ONGC | 9 | 4 | 0.782 | 0.785 | 64.7 | -36.14 | none/neg |
| COALINDIA | 9 | 3 | 1.348 | 0.869 | 68.8 | -62.58 | none/neg |
| INDUSINDBK | 9 | 3 | 1.061 | 0.759 | 72.1 | -173.25 | none/neg |
| NTPC | 9 | 3 | 0.909 | 0.951 | 67.1 | -16.87 | none/neg |
| DABUR | 9 | 3 | 0.879 | 0.526 | 69.4 | -250.58 | none/neg |
| NATIONALUM | 9 | 3 | 0.852 | 0.834 | 69.3 | -19.16 | none/neg |
| WIPRO | 9 | 3 | 0.830 | 0.796 | 65.3 | -86.73 | none/neg |
| ASHOKLEY | 9 | 3 | 0.742 | 0.696 | 71.7 | -12.20 | none/neg |
| AXISBANK | 9 | 2 | 5.827 | 0.667 | 71.4 | -339.04 | none/neg |
| SBIN | 9 | 2 | 1.103 | 0.862 | 70.3 | -150.76 | none/neg |
| PNB | 9 | 2 | 0.921 | 0.892 | 69.1 | -22.32 | none/neg |
| RELIANCE | 9 | 2 | 0.912 | 0.730 | 70.8 | -436.99 | none/neg |
| DIVISLAB | 9 | 2 | 0.884 | 0.695 | 70.2 | -1611.77 | none/neg |
| BAJFINANCE | 9 | 2 | 0.846 | 0.774 | 70.2 | -205.06 | none/neg |
| BHARTIARTL | 9 | 2 | 0.749 | 0.668 | 71.0 | -490.63 | none/neg |
| INFY | 9 | 2 | 0.723 | 0.646 | 67.6 | -725.84 | none/neg |
| VEDL | 9 | 1 | 0.790 | 0.889 | 69.2 | -87.52 | none/neg |
| ITC | 9 | 1 | 0.730 | 0.787 | 71.4 | -154.40 | none/neg |
| HDFCBANK | 9 | 1 | 0.727 | 0.793 | 68.9 | -312.02 | none/neg |
| ICICIBANK | 9 | 1 | 0.714 | 0.552 | 73.4 | -593.35 | none/neg |
| TECHM | 9 | 1 | 0.631 | 0.616 | 66.9 | -691.15 | none/neg |
| JSWSTEEL | 9 | 1 | 0.594 | 0.550 | 70.9 | -518.74 | none/neg |
| CIPLA | 9 | 1 | 0.585 | 0.538 | 71.3 | -654.07 | none/neg |
| TATASTEEL | 9 | 0 | 0.655 | 0.700 | 70.1 | -60.27 | none/neg |
| ADANIPORTS | 9 | 0 | 0.603 | 0.687 | 69.9 | -507.22 | none/neg |
| SUNPHARMA | 9 | 0 | 0.580 | 0.648 | 72.1 | -596.12 | none/neg |
| HINDALCO | 9 | 0 | 0.537 | 0.581 | 69.0 | -324.53 | none/neg |

### Config 2 (5yr/20mo)

| symbol | folds | n_folds_zpf>=1 | mean_zpf | median_zpf | mean_n | total_zpnl | concentration |
|--------|------:|---------------:|---------:|-----------:|-------:|-----------:|---------------|
| NATIONALUM | 4 | 3 | 1.098 | 1.107 | 136.2 | 12.23 | 1-fold (129% zpnl) |
| BANDHANBNK | 4 | 2 | 0.894 | 1.004 | 146.2 | -16.09 | none/neg |
| ADANIPORTS | 4 | 2 | 0.828 | 0.768 | 143.2 | -463.31 | none/neg |
| NTPC | 4 | 1 | 0.947 | 0.875 | 138.2 | -37.26 | none/neg |
| TATAMOTORS | 4 | 1 | 0.881 | 0.840 | 141.2 | -67.08 | none/neg |
| RELIANCE | 4 | 1 | 0.875 | 0.851 | 143.5 | -309.31 | none/neg |
| WIPRO | 4 | 1 | 0.861 | 0.767 | 136.5 | -80.93 | none/neg |
| PNB | 4 | 1 | 0.824 | 0.853 | 137.2 | -18.24 | none/neg |
| TATASTEEL | 4 | 1 | 0.786 | 0.737 | 144.2 | -38.13 | none/neg |
| POWERGRID | 4 | 1 | 0.764 | 0.681 | 135.0 | -87.64 | none/neg |
| COALINDIA | 4 | 1 | 0.761 | 0.722 | 144.8 | -104.14 | none/neg |
| ASHOKLEY | 4 | 1 | 0.756 | 0.659 | 140.2 | -29.64 | none/neg |
| INDUSINDBK | 4 | 1 | 0.726 | 0.664 | 149.0 | -404.97 | none/neg |
| ICICIBANK | 4 | 1 | 0.685 | 0.612 | 146.8 | -508.26 | none/neg |
| DABUR | 4 | 1 | 0.556 | 0.450 | 146.2 | -287.82 | none/neg |
| VEDL | 4 | 0 | 0.831 | 0.851 | 140.2 | -83.15 | none/neg |
| DIVISLAB | 4 | 0 | 0.776 | 0.784 | 144.5 | -1714.93 | none/neg |
| AXISBANK | 4 | 0 | 0.733 | 0.773 | 147.2 | -356.29 | none/neg |
| BAJFINANCE | 4 | 0 | 0.722 | 0.742 | 146.2 | -252.81 | none/neg |
| TECHM | 4 | 0 | 0.716 | 0.732 | 140.2 | -637.55 | none/neg |
| ONGC | 4 | 0 | 0.698 | 0.700 | 133.8 | -81.89 | none/neg |
| SBIN | 4 | 0 | 0.691 | 0.747 | 142.8 | -236.26 | none/neg |
| CIPLA | 4 | 0 | 0.681 | 0.706 | 148.5 | -530.64 | none/neg |
| JSWSTEEL | 4 | 0 | 0.652 | 0.671 | 146.0 | -477.25 | none/neg |
| INFY | 4 | 0 | 0.640 | 0.608 | 139.5 | -837.20 | none/neg |
| HINDALCO | 4 | 0 | 0.628 | 0.580 | 142.2 | -336.41 | none/neg |
| HDFCBANK | 4 | 0 | 0.614 | 0.595 | 147.0 | -419.51 | none/neg |
| ITC | 4 | 0 | 0.611 | 0.582 | 142.0 | -143.27 | none/neg |
| SUNPHARMA | 4 | 0 | 0.581 | 0.574 | 152.8 | -743.90 | none/neg |
| BHARTIARTL | 4 | 0 | 0.581 | 0.580 | 150.8 | -675.77 | none/neg |

## Bottom line (does any edge survive WFA?)

**No robust, book-wide edge.** Gated SHORT ZPnL is negative for almost every stock when summed across folds. Consistency counts are low:

| Config | Best consistency | Notes |
|--------|------------------|--------|
| Config 1 (9 folds) | **BANDHANBNK 5/9**, then POWERGRID / TATAMOTORS / ONGC at 4/9 | Only BANDHANBNK has **positive total ZPnL** (+85.6). Others with 4/9 still have **negative** cumulative ZPnL. |
| Config 2 (4 folds) | **NATIONALUM 3/4** (only name with mean ZPF > 1 and small +total ZPnL) | BANDHANBNK 2/4; most names 0–1/4. |

**Caveats that reinforce fragility (same story as single-split):**

1. **Sell days shrink in later folds** (Config1 fold7 = 11 Sell days, fold9 = 3). Tiny-N folds inflate ZPF (e.g. AXISBANK fold9 ZPF≈46 on n=4) — ignore fold9 ranks.
2. **Fold-level book ZPnL is negative every fold** in both configs (Config1 fold totals roughly −0.3k to −2.2k ZPnL across 30 stocks).
3. Names that looked good on one fixed Test window (e.g. TATAMOTORS 4/9 ZPF≥1) still **do not clear costs overall** (TATAMOTORS total ZPnL ≈ −2.6 on Config1).
4. **BANDHANBNK** is the only Config1 candidate worth a second look (5/9, +ZPnL), but listing starts 2018 and edge still fails several folds (3,4,6,7) — not a stable live gate.

**Answer to the analysis question:** the NIFTY50 Model B Sell-gate on fv2 SHORT does **not** produce a consistent multi-window edge. Apparent single-split winners do not survive rolling WFA.

## Reading notes

- **Consistency count** (folds with ZPF ≥ 1.0) is the primary question — not just average ZPF.
- **concentration = 1-fold / 2-fold** means most positive ZPnL came from one or two windows (fragile edge).
- **spread** means ZPnL is distributed across more folds (more robust).
- Stocks with few trades in a fold (low `mean_n`) have noisy ZPF; treat carefully.
- Config1 **fold 9** (2026-02→2026-07, only 3 Sell days) is partial and high-variance — do not rank stocks on it alone.

## Files

- `33_wfa_config1_results.csv`
- `33_wfa_config2_results.csv`
- `33_wfa_summary.md` (this file)
