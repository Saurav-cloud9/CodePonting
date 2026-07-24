# Iteration Log — MA Baseline Locked (ZPF Edition)
**Universe:** 30 NSE stocks · 5-min bars · DS3 parquets 2015–2025
**Charges:** Zerodha intraday (ZPF = PF after full Zerodha charges)
**Scripts:** baseline_reserve_lock/ (this folder)
**Prior log (raw PF / monthly Sharpe):** `../iteration_log.md` — kept as reference

---

## What Changed vs Prior Log

Prior log (`iteration_log.md`) used:
- Raw PF (no charges)
- Monthly Sharpe (annualised ×√12)

This log uses:
- **ZPF** = PF after full Zerodha intraday charges (primary metric)
- **ZSh(D)** = daily zpnl mean/std × √252 (primary Sharpe metric)
- Raw PF retained as reference column

Charge formula (per trade, qty=1):
```
brok  = min(0.03% × entry, ₹20) + min(0.03% × exit, ₹20)
stt   = sell_side × 0.025%   [entry for SHORT, exit for LONG]
txn   = (entry + exit) × 0.00307%
sebi  = (entry + exit) × 0.0001%
stamp = buy_side × 0.0003%   [exit for SHORT, entry for LONG]
gst   = 18% × (brok + txn + sebi)
total = brok + stt + txn + sebi + stamp + gst
```

---

## Summary

| Run | Signal | Direction | Locked Combo | N | PF | ZPF | ZSh(D) | Edge? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Baseline (multi-bar) | SHORT | SL=1.5 · TP=4.0 | 172,360 | 1.116 | 0.737 | -5.596 | ❌ |
| 1 | Baseline (multi-bar) | LONG | SL=1.5 · TP=3.5 | 186,478 | 0.910 | 0.592 | -10.704 | ❌ |
| 1-sweep best ZPF | Baseline (multi-bar) | SHORT | SL=6.0 · TP=6.0 | 91,878 | 1.112 | 0.851 | -1.894 | ❌ |
| 1-sweep best ZPF | Baseline (multi-bar) | LONG | SL=6.0 · TP=6.0 | 92,356 | 0.877 | 0.672 | -4.816 | ❌ |

**Key finding:** Raw PF > 1.0 for SHORT baseline, but ZPF = 0.737 after Zerodha charges.
Charges consume ~0.38 PF points on the SHORT strategy. No combo achieves ZPF > 1.0.

---

## Run 1 — Baseline SHORT (MA Rejection) — ZPF Re-run

**Signal:** `high >= MA20` → `close < MA20` within 3 bars → SHORT at next bar open
**Script:** `ma_30_rejection.py` (fixed SL=1.5×ATR, TP=4.0×ATR)
**Sweep:** `sl_tgt_sweep_baseline_short.py` (90 combos: 10 SL × 9 TP)

### Fixed Combo (SL=1.5 · TP=4.0) — per stock

| Symbol | N | Prof_WR% | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|
| BANDHANBNK | 4,104 | 39.3 | 1.339 | 0.994 | -0.050 |
| NATIONALUM | 5,651 | 38.2 | 1.229 | 0.920 | -0.671 |
| PNB | 5,594 | 38.8 | 1.220 | 0.900 | -0.881 |
| VEDL | 5,663 | 38.1 | 1.180 | 0.875 | -1.166 |
| TATAMOTORS | 5,684 | 39.8 | 1.277 | 0.866 | -1.240 |
| ASHOKLEY | 5,895 | 36.5 | 1.202 | 0.852 | -1.464 |
| TATASTEEL | 5,725 | 37.4 | 1.197 | 0.836 | -1.516 |
| ONGC | 5,552 | 38.3 | 1.223 | 0.825 | -1.651 |
| ADANIPORTS | 5,827 | 37.5 | 1.161 | 0.816 | -1.702 |
| NTPC | 5,834 | 37.2 | 1.216 | 0.804 | -1.787 |
| HINDALCO | 5,795 | 36.7 | 1.133 | 0.790 | -2.040 |
| INDUSINDBK | 5,864 | 36.7 | 1.158 | 0.787 | -2.195 |
| SBIN | 5,852 | 38.1 | 1.193 | 0.773 | -2.306 |
| DIVISLAB | 5,849 | 37.3 | 1.133 | 0.758 | -2.249 |
| COALINDIA | 5,858 | 37.0 | 1.143 | 0.747 | -2.569 |
| CIPLA | 5,675 | 37.8 | 1.128 | 0.733 | -2.834 |
| AXISBANK | 5,977 | 36.9 | 1.100 | 0.727 | -2.982 |
| BAJFINANCE | 6,434 | 29.3 | 1.072 | 0.716 | -2.806 |
| TECHM | 5,870 | 36.8 | 1.045 | 0.705 | -3.088 |
| SUNPHARMA | 5,855 | 37.7 | 1.083 | 0.704 | -3.124 |
| RELIANCE | 5,717 | 38.8 | 1.164 | 0.701 | -2.970 |
| ITC | 5,744 | 37.7 | 1.170 | 0.700 | -3.324 |
| POWERGRID | 5,812 | 35.1 | 1.077 | 0.698 | -2.990 |
| JSWSTEEL | 5,970 | 35.5 | 1.006 | 0.695 | -3.084 |
| DABUR | 5,963 | 36.2 | 1.087 | 0.694 | -3.297 |
| WIPRO | 5,585 | 36.1 | 1.081 | 0.683 | -3.179 |
| BHARTIARTL | 5,906 | 36.6 | 1.034 | 0.674 | -3.238 |
| ICICIBANK | 5,776 | 36.0 | 1.046 | 0.652 | -3.572 |
| INFY | 5,473 | 36.8 | 1.046 | 0.628 | -3.850 |
| HDFCBANK | 5,856 | 33.5 | 0.962 | 0.552 | -5.145 |

**TOTAL: N=172,360  Prof_WR=36.9%  PF=1.116  ZPF=0.737  ZSh(D)=-5.596**

Year-wise (fixed combo SL=1.5 · TP=4.0):

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 14,533 | 1.153 | 0.794 | -5.350 | ❌ |
| 2016 | 15,730 | 1.111 | 0.744 | -6.842 | ❌ |
| 2017 | 15,418 | 1.118 | 0.712 | -8.484 | ❌ |
| 2018 | 15,788 | 1.194 | 0.825 | -4.394 | ❌ |
| 2019 | 16,139 | 1.143 | 0.777 | -5.640 | ❌ |
| 2020 | 15,516 | 1.150 | 0.860 | -2.593 | ❌ |
| 2021 | 15,545 | 1.159 | 0.791 | -4.349 | ❌ |
| 2022 | 15,478 | 1.100 | 0.727 | -5.767 | ❌ |
| 2023 | 15,576 | 1.014 | 0.614 | -10.559 | ❌ |
| 2024 | 15,907 | 1.117 | 0.725 | -6.150 | ❌ |
| 2025 | 16,730 | 1.070 | 0.648 | -8.744 | ❌ |

**Note:** All 11 years fail ZPF < 0.9. Zerodha charges destroy the raw edge entirely.

---

### SHORT Sweep — ZPF Grid (SL rows × TP cols)

```
  SL\TP    2.0    2.5    3.0    3.5    4.0    4.5    5.0    5.5    6.0
     1.5  0.645  0.682  0.707  0.724  0.737  0.742  0.749  0.752  0.755
     2.0  0.681  0.720  0.744  0.762  0.774  0.778  0.786  0.788  0.792
     2.5  0.704  0.744  0.767  0.784  0.796  0.800  0.807  0.809  0.813
     3.0  0.718  0.758  0.780  0.797  0.809  0.812  0.818  0.820  0.824
     3.5  0.726  0.766  0.788  0.806  0.818  0.821  0.826  0.828  0.832
     4.0  0.732  0.771  0.793  0.811  0.824  0.826  0.831  0.833  0.837
     4.5  0.736  0.776  0.799  0.817  0.829  0.832  0.837  0.838  0.841
     5.0  0.739  0.780  0.802  0.821  0.834  0.837  0.842  0.843  0.846
     5.5  0.741  0.782  0.804  0.823  0.836  0.839  0.844  0.846  0.849
     6.0  0.743  0.784  0.806  0.825  0.838  0.841  0.846  0.848  0.851 ★
```
★ Best ZPF: SL=6.0 · TP=6.0

Top 5 by ZPF:

| Rank | SL | TP | N | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|---|
| 1 | 6.0 | 6.0 | 91,878 | 1.112 | 0.851 | -1.894 |
| 2 | 5.5 | 6.0 | 93,447 | 1.112 | 0.849 | -1.958 |
| 3 | 6.0 | 5.5 | 93,614 | 1.111 | 0.848 | -1.964 |
| 4 | 6.0 | 5.0 | 95,826 | 1.113 | 0.846 | -2.031 |
| 5 | 5.0 | 6.0 | 95,524 | 1.112 | 0.846 | -2.026 |

Best combo (ZPF) year-wise — SL=6.0 · TP=6.0:

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 7,564 | 1.185 | 0.934 | -0.948 | 🟡 |
| 2016 | 8,323 | 1.117 | 0.865 | -1.989 | ❌ |
| 2017 | 8,297 | 1.148 | 0.860 | -2.335 | ❌ |
| 2018 | 8,458 | 1.167 | 0.924 | -1.107 | 🟡 |
| 2019 | 8,350 | 1.183 | 0.926 | -0.979 | 🟡 |
| 2020 | 8,434 | 1.126 | 0.936 | -0.727 | 🟡 |
| 2021 | 8,431 | 1.148 | 0.897 | -1.362 | ❌ |
| 2022 | 8,376 | 1.094 | 0.840 | -2.033 | ❌ |
| 2023 | 8,287 | 1.025 | 0.734 | -4.262 | ❌ |
| 2024 | 8,615 | 1.094 | 0.826 | -2.268 | ❌ |
| 2025 | 8,743 | 1.061 | 0.764 | -3.463 | ❌ |

**Verdict:** Best ZPF = 0.851. No combo achieves ZPF ≥ 1.0. 5 of 11 years hit ZPF ≥ 0.9 but none ≥ 1.0.
Heatmap: `outputs/reports/sl_tgt_sweep_baseline_short_zpf.png`

---

## Run 1 — Baseline LONG (MA Bounce) — ZPF Re-run

**Signal:** `low <= MA20` → `close > MA20` within 3 bars → LONG at next bar open
**Script:** `ma_30_bounce.py` (fixed SL=1.5×ATR, TP=3.5×ATR)
**Sweep:** `sl_tgt_sweep_baseline_long.py` (90 combos: 10 SL × 9 TP)

### Fixed Combo (SL=1.5 · TP=3.5) — overall

**TOTAL: N=186,478  Prof_WR=33.3%  PF=0.910  ZPF=0.592  ZSh(D)=-10.704**

Year-wise (fixed combo SL=1.5 · TP=3.5):

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 15,280 | 0.896 | 0.607 | -12.707 | ❌ |
| 2016 | 16,805 | 0.876 | 0.578 | -13.077 | ❌ |
| 2017 | 17,145 | 0.874 | 0.550 | -17.344 | ❌ |
| 2018 | 17,202 | 0.884 | 0.598 | -11.973 | ❌ |
| 2019 | 17,432 | 0.882 | 0.593 | -11.506 | ❌ |
| 2020 | 17,027 | 0.931 | 0.686 | -7.666 | ❌ |
| 2021 | 17,083 | 0.878 | 0.591 | -11.658 | ❌ |
| 2022 | 17,053 | 0.951 | 0.620 | -10.206 | ❌ |
| 2023 | 16,774 | 0.898 | 0.532 | -15.464 | ❌ |
| 2024 | 16,931 | 0.914 | 0.588 | -10.777 | ❌ |
| 2025 | 17,746 | 0.957 | 0.570 | -13.879 | ❌ |

### LONG Sweep — ZPF Grid (SL rows × TP cols)

```
  SL\TP    2.0    2.5    3.0    3.5    4.0    4.5    5.0    5.5    6.0
     1.5  0.533  0.561  0.581  0.592  0.596  0.601  0.603  0.608  0.608
     2.0  0.561  0.589  0.609  0.620  0.625  0.630  0.632  0.637  0.637
     2.5  0.575  0.603  0.623  0.635  0.639  0.644  0.645  0.650  0.651
     3.0  0.582  0.609  0.628  0.640  0.646  0.650  0.652  0.657  0.658
     3.5  0.587  0.613  0.633  0.645  0.650  0.655  0.656  0.661  0.663
     4.0  0.588  0.616  0.635  0.646  0.651  0.656  0.657  0.662  0.664
     4.5  0.591  0.619  0.639  0.650  0.655  0.659  0.660  0.665  0.667
     5.0  0.592  0.619  0.640  0.651  0.656  0.660  0.661  0.666  0.668
     5.5  0.593  0.621  0.642  0.652  0.657  0.662  0.663  0.668  0.670
     6.0  0.595  0.622  0.643  0.655  0.660  0.664  0.665  0.670  0.672 ★
```
★ Best ZPF: SL=6.0 · TP=6.0

Top 5 by ZPF:

| Rank | SL | TP | N | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|---|
| 1 | 6.0 | 6.0 | 92,356 | 0.877 | 0.672 | -4.816 |
| 2 | 6.0 | 5.5 | 93,927 | 0.877 | 0.670 | -4.922 |
| 3 | 5.5 | 6.0 | 94,214 | 0.876 | 0.670 | -4.942 |
| 4 | 5.0 | 6.0 | 96,564 | 0.877 | 0.668 | -5.075 |
| 5 | 5.5 | 5.5 | 95,806 | 0.876 | 0.668 | -5.052 |

Best combo (ZPF) year-wise — SL=6.0 · TP=6.0:

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 7,547 | 0.826 | 0.651 | -6.039 | ❌ |
| 2016 | 8,337 | 0.861 | 0.668 | -5.592 | ❌ |
| 2017 | 8,416 | 0.851 | 0.641 | -7.302 | ❌ |
| 2018 | 8,501 | 0.829 | 0.659 | -5.697 | ❌ |
| 2019 | 8,375 | 0.816 | 0.642 | -5.802 | ❌ |
| 2020 | 8,541 | 0.845 | 0.703 | -4.007 | ❌ |
| 2021 | 8,528 | 0.856 | 0.671 | -5.274 | ❌ |
| 2022 | 8,462 | 0.897 | 0.686 | -4.566 | ❌ |
| 2023 | 8,360 | 0.941 | 0.672 | -5.650 | ❌ |
| 2024 | 8,496 | 0.902 | 0.683 | -4.597 | ❌ |
| 2025 | 8,793 | 0.936 | 0.675 | -5.282 | ❌ |

**Verdict:** Best ZPF = 0.672. No combo achieves ZPF ≥ 1.0 across all 90 combos or any single year.
Heatmap: `outputs/reports/sl_tgt_sweep_baseline_long_zpf.png`

---

## Key Takeaways

1. **Charges crush the SHORT edge:** PF=1.116 → ZPF=0.737 at SL=1.5/TP=4.0. ~0.38 ZPF gap.
2. **LONG has no raw edge either:** PF=0.910 → ZPF=0.592. Doubly dead.
3. **Best combo by ZPF (SHORT):** SL=6.0/TP=6.0 → ZPF=0.851. Still well below 1.0.
4. **ZPF gap narrows with wider SL/TP:** ZPF rises from 0.645 (SL=1.5/TP=2.0) to 0.851 (SL=6.0/TP=6.0). Charges are fixed per trade but wider combos capture more pnl per win.
5. **Signal redesign required:** Even the best combo needs +0.15 ZPF to break even. No filter will close this gap — the signal needs genuine edge.
