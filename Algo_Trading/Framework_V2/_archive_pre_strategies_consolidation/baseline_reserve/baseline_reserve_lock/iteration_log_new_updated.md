# Iteration Log — MA Baseline Locked (ZPF Edition) — UPDATED

**Universe:** 30 NSE stocks · 5-min bars · DS3 parquets 2015–2026 (extended, was 2015–2025)
**Charges:** Zerodha intraday (ZPF = PF after full Zerodha charges)
**Scripts:** baseline_reserve_lock/ (this folder)
**Prior log:** `iteration_log_new.md` — kept as-is, untouched. This file supersedes its numbers only.

---

## What Changed vs `iteration_log_new.md`

Two independent changes since that log was written, both applied together here:

1. **DS3 data refresh** — extended from 2015–2025 to 2015–2026 (Jan–Jul added), plus a
   2-row `atr14` boundary fix (DIVISLAB file-start, INFY post-gap resume). See prior
   session for detail — negligible on its own (2 rows / 210k×30), but the 2026
   extension adds ~5-9% more trades per run.
2. **EOD touch/entry cutoff added** — all 4 scripts now match the live bot's
   (`ma_rejection_v1_core.py`) stricter timing gate instead of the old `hour < 15` check:
   - `LAST_TOUCH_TIME = 14:45` — touch/signal bar must be `<= 14:45` (old check allowed
     touches anywhere in the 14:00–14:55 window)
   - `ENTRY_CUTOFF_TIME = 14:50` — entry bar (rejection/bounce bar + 1) must be `<= 14:50`,
     else the signal is cancelled outright (no trade, no charges)
   - Also documented in `backtesting_rules.md` §2.

Both changes are additive to the locked strategy definition — SL/TP multipliers, exit
priority, position guard, and charge formula are all unchanged.

---

## Summary

| Run | Signal | Direction | Locked Combo | N | PF | ZPF | ZSh(D) | Edge? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Baseline (multi-bar) | SHORT | SL=1.5 · TP=4.0 | 177,171 | 1.107 | 0.734 | -5.654 | ❌ |
| 1 | Baseline (multi-bar) | LONG | SL=1.5 · TP=3.5 | 191,316 | 0.919 | 0.601 | -10.499 | ❌ |
| 1-sweep best ZPF | Baseline (multi-bar) | SHORT | SL=6.0 · TP=6.0 | 95,962 | 1.096 | 0.838 | -2.079 | ❌ |
| 1-sweep best ZPF | Baseline (multi-bar) | LONG | SL=6.0 · TP=6.0 | 96,430 | 0.890 | 0.682 | -4.646 | ❌ |

**Key finding: verdict unchanged from prior log.** No combo achieves ZPF > 1.0. Numbers
shifted by ~1-2 ZPF points overall (see comparison table below) but the conclusion holds.

---

## Comparison vs prior log (`iteration_log_new.md`)

| Run | Metric | Prior log | This run | Δ |
|---|---|---:|---:|---:|
| SHORT fixed (1.5/4.0) | N | 172,360 | 177,171 | +4,811 |
| | PF / ZPF | 1.116 / 0.737 | 1.107 / 0.734 | -0.009 / -0.003 |
| | ZSh(D) | -5.596 | -5.654 | worse |
| LONG fixed (1.5/3.5) | N | 186,478 | 191,316 | +4,838 |
| | PF / ZPF | 0.910 / 0.592 | 0.919 / 0.601 | +0.009 / +0.009 |
| | ZSh(D) | -10.704 | -10.499 | better |
| SHORT sweep best (6.0/6.0) | N | 91,878 | 95,962 | +4,084 |
| | PF / ZPF | 1.112 / 0.851 | 1.096 / 0.838 | -0.016 / -0.013 |
| | ZSh(D) | -1.894 | -2.079 | worse |
| LONG sweep best (6.0/6.0) | N | 92,356 | 96,430 | +4,074 |
| | PF / ZPF | 0.877 / 0.672 | 0.890 / 0.682 | +0.013 / +0.010 |
| | ZSh(D) | -4.816 | -4.646 | better |

N rose despite the stricter 14:45/14:50 cutoff removing some late-day trades — because
the 2026 extension (7 new months × 30 stocks) added more trades than the cutoff removed.
Net effect on ZPF is small either way (≤0.016), well within noise of a signal that's
structurally dead regardless.

---

## Run 1 — Baseline SHORT (MA Rejection) — Fixed Combo (SL=1.5 · TP=4.0)

**Signal:** `high >= MA20` (touch bar `<= 14:45`) → `close < MA20` within 3 bars → SHORT
at next bar open (entry bar `<= 14:50`)
**Script:** `ma_30_rejection.py`

### Per-stock breakdown

| Symbol | N | Prof_WR% | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|
| BANDHANBNK | 4,320 | 39.5 | 1.319 | 0.985 | -0.123 |
| PNB | 5,786 | 39.2 | 1.214 | 0.895 | -0.924 |
| VEDL | 5,804 | 38.4 | 1.173 | 0.873 | -1.184 |
| NATIONALUM | 5,811 | 38.4 | 1.167 | 0.871 | -1.058 |
| TATAMOTORS | 5,853 | 40.3 | 1.275 | 0.869 | -1.210 |
| ASHOKLEY | 6,072 | 36.7 | 1.170 | 0.832 | -1.578 |
| TATASTEEL | 5,879 | 37.8 | 1.182 | 0.824 | -1.628 |
| ONGC | 5,723 | 38.4 | 1.204 | 0.817 | -1.727 |
| ADANIPORTS | 6,016 | 37.7 | 1.123 | 0.789 | -1.924 |
| NTPC | 6,014 | 37.4 | 1.179 | 0.782 | -2.023 |
| INDUSINDBK | 6,016 | 36.9 | 1.140 | 0.782 | -2.246 |
| HINDALCO | 5,921 | 37.0 | 1.107 | 0.774 | -2.156 |
| SBIN | 5,992 | 38.2 | 1.175 | 0.765 | -2.349 |
| COALINDIA | 6,044 | 37.3 | 1.144 | 0.754 | -2.501 |
| DIVISLAB | 6,007 | 37.6 | 1.122 | 0.754 | -2.281 |
| AXISBANK | 6,118 | 37.3 | 1.108 | 0.735 | -2.858 |
| CIPLA | 5,859 | 37.9 | 1.114 | 0.726 | -2.901 |
| TECHM | 5,977 | 37.5 | 1.058 | 0.719 | -2.895 |
| RELIANCE | 5,877 | 39.4 | 1.180 | 0.716 | -2.789 |
| ITC | 5,888 | 38.3 | 1.165 | 0.702 | -3.296 |
| BAJFINANCE | 6,591 | 29.8 | 1.045 | 0.700 | -2.952 |
| DABUR | 6,146 | 36.6 | 1.079 | 0.695 | -3.285 |
| JSWSTEEL | 6,137 | 36.0 | 1.006 | 0.694 | -3.112 |
| WIPRO | 5,729 | 36.7 | 1.091 | 0.693 | -3.074 |
| SUNPHARMA | 6,031 | 37.9 | 1.065 | 0.692 | -3.275 |
| POWERGRID | 5,991 | 35.2 | 1.046 | 0.683 | -3.159 |
| BHARTIARTL | 6,077 | 36.9 | 1.028 | 0.670 | -3.257 |
| ICICIBANK | 5,909 | 36.3 | 1.039 | 0.649 | -3.598 |
| INFY | 5,598 | 37.4 | 1.060 | 0.645 | -3.648 |
| HDFCBANK | 5,985 | 34.3 | 0.979 | 0.567 | -4.899 |

**TOTAL: N=177,171  Prof_WR=37.2%  PF=1.107  ZPF=0.734  ZSh(D)=-5.654**

### Year-wise

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 14,124 | 1.155 | 0.802 | -5.078 | ❌ |
| 2016 | 15,370 | 1.113 | 0.751 | -6.597 | ❌ |
| 2017 | 15,010 | 1.120 | 0.720 | -8.213 | ❌ |
| 2018 | 15,383 | 1.194 | 0.831 | -4.200 | ❌ |
| 2019 | 15,693 | 1.144 | 0.785 | -5.405 | ❌ |
| 2020 | 15,181 | 1.151 | 0.867 | -2.460 | ❌ |
| 2021 | 15,135 | 1.161 | 0.799 | -4.138 | ❌ |
| 2022 | 15,103 | 1.101 | 0.733 | -5.595 | ❌ |
| 2023 | 15,233 | 1.015 | 0.619 | -10.342 | ❌ |
| 2024 | 15,514 | 1.115 | 0.730 | -5.996 | ❌ |
| 2025 | 16,398 | 1.072 | 0.654 | -8.503 | ❌ |
| 2026 | 9,027 | 1.002 | 0.642 | -9.622 | ❌ (partial year, Jan–Jul) |

---

## Run 1 — Baseline LONG (MA Bounce) — Fixed Combo (SL=1.5 · TP=3.5)

**Signal:** `low <= MA20` (touch bar `<= 14:45`) → `close > MA20` within 3 bars → LONG at
next bar open (entry bar `<= 14:50`)
**Script:** `ma_30_bounce.py`

**TOTAL: N=191,316  Prof_WR=33.8%  PF=0.919  ZPF=0.601  ZSh(D)=-10.499**

### Year-wise

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 14,888 | 0.898 | 0.613 | -12.388 | ❌ |
| 2016 | 16,332 | 0.878 | 0.585 | -12.753 | ❌ |
| 2017 | 16,670 | 0.875 | 0.555 | -17.015 | ❌ |
| 2018 | 16,664 | 0.883 | 0.604 | -11.692 | ❌ |
| 2019 | 16,953 | 0.882 | 0.598 | -11.308 | ❌ |
| 2020 | 16,600 | 0.930 | 0.689 | -7.559 | ❌ |
| 2021 | 16,631 | 0.880 | 0.597 | -11.413 | ❌ |
| 2022 | 16,574 | 0.951 | 0.626 | -9.990 | ❌ |
| 2023 | 16,368 | 0.897 | 0.537 | -15.188 | ❌ |
| 2024 | 16,527 | 0.914 | 0.593 | -10.560 | ❌ |
| 2025 | 17,283 | 0.956 | 0.575 | -13.628 | ❌ |
| 2026 | 9,826 | 1.019 | 0.643 | -11.246 | ❌ (partial year, Jan–Jul) |

---

## SHORT Sweep — ZPF Grid (SL rows × TP cols)

```
  SL\TP    2.0    2.5    3.0    3.5    4.0    4.5    5.0    5.5    6.0
     1.5  0.646  0.683  0.706  0.724  0.734  0.739  0.746  0.748  0.749
     2.0  0.681  0.719  0.742  0.760  0.771  0.775  0.781  0.783  0.785
     2.5  0.702  0.740  0.763  0.780  0.791  0.795  0.801  0.802  0.804
     3.0  0.714  0.753  0.775  0.792  0.802  0.806  0.811  0.812  0.814
     3.5  0.722  0.761  0.782  0.800  0.811  0.814  0.818  0.820  0.822
     4.0  0.726  0.765  0.786  0.803  0.815  0.818  0.822  0.824  0.825
     4.5  0.729  0.768  0.790  0.808  0.819  0.823  0.826  0.828  0.829
     5.0  0.732  0.771  0.793  0.812  0.823  0.826  0.830  0.832  0.834
     5.5  0.734  0.773  0.795  0.814  0.826  0.828  0.833  0.834  0.836
     6.0  0.735  0.775  0.797  0.816  0.827  0.830  0.835  0.837  0.838 ★
```
★ Best ZPF: SL=6.0 · TP=6.0

Top 5 by ZPF:

| Rank | SL | TP | N | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|---|
| 1 | 6.0 | 6.0 | 95,962 | 1.096 | 0.838 | -2.079 |
| 2 | 6.0 | 5.5 | 97,682 | 1.095 | 0.837 | -2.139 |
| 3 | 5.5 | 6.0 | 97,547 | 1.095 | 0.836 | -2.143 |
| 4 | 6.0 | 5.0 | 99,916 | 1.097 | 0.835 | -2.207 |
| 5 | 5.0 | 6.0 | 99,639 | 1.096 | 0.834 | -2.213 |

Best combo (ZPF) year-wise — SL=6.0 · TP=6.0:

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 7,493 | 1.184 | 0.935 | -0.939 | 🟡 |
| 2016 | 8,259 | 1.118 | 0.868 | -1.949 | ❌ |
| 2017 | 8,223 | 1.149 | 0.862 | -2.288 | ❌ |
| 2018 | 8,369 | 1.167 | 0.926 | -1.076 | 🟡 |
| 2019 | 8,272 | 1.183 | 0.928 | -0.954 | 🟡 |
| 2020 | 8,370 | 1.127 | 0.939 | -0.698 | 🟡 |
| 2021 | 8,355 | 1.149 | 0.899 | -1.323 | ❌ |
| 2022 | 8,294 | 1.094 | 0.841 | -2.010 | ❌ |
| 2023 | 8,231 | 1.025 | 0.735 | -4.230 | ❌ |
| 2024 | 8,538 | 1.092 | 0.827 | -2.256 | ❌ |
| 2025 | 8,674 | 1.061 | 0.766 | -3.425 | ❌ |
| 2026 | 4,884 | 0.926 | 0.691 | -5.025 | ❌ |

**Verdict:** Best ZPF = 0.838 (was 0.851). Still no combo achieves ZPF ≥ 1.0.
Heatmap: `outputs/reports/sl_tp_sweep_baseline_short_zpf.png` (regenerated, overwrites prior)

---

## LONG Sweep — ZPF Grid (SL rows × TP cols)

```
  SL\TP    2.0    2.5    3.0    3.5    4.0    4.5    5.0    5.5    6.0
     1.5  0.541  0.569  0.589  0.601  0.606  0.612  0.614  0.619  0.619
     2.0  0.568  0.597  0.618  0.630  0.635  0.641  0.643  0.648  0.649
     2.5  0.583  0.611  0.632  0.645  0.649  0.655  0.657  0.662  0.663
     3.0  0.590  0.617  0.637  0.650  0.656  0.661  0.662  0.668  0.669
     3.5  0.594  0.621  0.642  0.654  0.660  0.665  0.667  0.672  0.673
     4.0  0.595  0.622  0.643  0.655  0.660  0.666  0.667  0.672  0.674
     4.5  0.598  0.625  0.647  0.659  0.664  0.670  0.671  0.676  0.678
     5.0  0.599  0.626  0.648  0.659  0.665  0.671  0.671  0.676  0.679
     5.5  0.600  0.627  0.649  0.661  0.666  0.672  0.673  0.678  0.680
     6.0  0.602  0.628  0.651  0.663  0.669  0.675  0.675  0.680  0.682 ★
```
★ Best ZPF: SL=6.0 · TP=6.0

Top 5 by ZPF:

| Rank | SL | TP | N | PF | ZPF | ZSh(D) |
|---|---|---|---|---|---|---|
| 1 | 6.0 | 6.0 | 96,430 | 0.890 | 0.682 | -4.646 |
| 2 | 6.0 | 5.5 | 97,973 | 0.890 | 0.680 | -4.758 |
| 3 | 5.5 | 6.0 | 98,299 | 0.889 | 0.680 | -4.766 |
| 4 | 5.0 | 6.0 | 100,663 | 0.890 | 0.679 | -4.893 |
| 5 | 4.5 | 6.0 | 103,715 | 0.893 | 0.678 | -5.017 |

Best combo (ZPF) year-wise — SL=6.0 · TP=6.0:

| Year | N | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|---|
| 2015 | 7,478 | 0.827 | 0.653 | -6.028 | ❌ |
| 2016 | 8,237 | 0.861 | 0.670 | -5.544 | ❌ |
| 2017 | 8,321 | 0.851 | 0.643 | -7.248 | ❌ |
| 2018 | 8,400 | 0.829 | 0.661 | -5.657 | ❌ |
| 2019 | 8,297 | 0.816 | 0.642 | -5.784 | ❌ |
| 2020 | 8,469 | 0.845 | 0.704 | -3.995 | ❌ |
| 2021 | 8,440 | 0.857 | 0.673 | -5.227 | ❌ |
| 2022 | 8,376 | 0.897 | 0.688 | -4.536 | ❌ |
| 2023 | 8,298 | 0.941 | 0.674 | -5.615 | ❌ |
| 2024 | 8,434 | 0.902 | 0.684 | -4.571 | ❌ |
| 2025 | 8,701 | 0.936 | 0.677 | -5.241 | ❌ |
| 2026 | 4,979 | 1.043 | 0.785 | -3.319 | ❌ |

**Verdict:** Best ZPF = 0.682 (was 0.672). Still no combo achieves ZPF ≥ 1.0 across all
90 combos or any single year.
Heatmap: `outputs/reports/sl_tp_sweep_baseline_long_zpf.png` (regenerated, overwrites prior)

---

## Key Takeaways

1. **Verdict unchanged.** Neither the DS3 refresh (2026 extension + 2-row atr14 fix) nor
   the EOD touch/entry cutoff alignment (matching the live bot) moves ZPF enough to
   change the strategy's viability conclusion.
2. **Charges still crush the SHORT edge:** PF=1.107 → ZPF=0.734 at SL=1.5/TP=4.0.
3. **LONG still has no raw edge:** PF=0.919 → ZPF=0.601.
4. **Best combo by ZPF (SHORT):** SL=6.0/TP=6.0 → ZPF=0.838 (prior: 0.851). Still well
   below 1.0.
5. **2026 partial-year data (new):** consistent with the rest of the series — no
   improvement signal there either (SHORT fixed-combo ZPF=0.642, LONG=0.643).
6. **This log now reflects the same methodology as the live bot** (EOD cutoff) and
   current DS3 — safe to treat as the up-to-date reference over `iteration_log_new.md`.
