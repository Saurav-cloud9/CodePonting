# ATR Formula Exploration — Results

**Script:** `scripts/trials/ATR_exploration/atr_formula_exploration.py`  
**Run date:** 2026-07-30  
**Baseline reference:** `ma_30_rejection_v1.py`  
**Rules:** Zerodha ZPF / ZSh(D) primary (same charge model as SL/TP sweep)

---

## 1. Strategy definition

| Item | Detail |
|---|---|
| **Side** | SHORT |
| **Signal (v1 clean-touch)** | Single bar where `high >= MA20` AND `open < MA20` AND `close < MA20` |
| **Entry** | Open of next bar (`i+1`), same trading day; skipped if date changes |
| **Signal hour filter** | Signal bar must have `hour < 15` |
| **SL** | `entry + 2.0 × ATR_variant` **(locked)** |
| **TP** | `entry − 4.5 × ATR_variant` **(locked)** |
| **Exit priority** | (1) Date change → prior close · (2) `hour >= 15` → bar open · (3) SL hit · (4) TP hit |
| **Position guard** | Single-pass; resume at `i = k + 1` after each trade |
| **Universe** | 30 DS3 stocks, 5-min bars, 2015–2025 |
| **Data path** | `data/historical/intraday_5min_DS3/*.parquet` |
| **What varies** | ATR formula (Simple / Wilder) × period (10 / 14 / 20) × source bar (Signal / Entry) — **12 variants** |

### ATR formulas

| # | Formula | Period | Definition |
|---|---|---|---|
| 1 | Simple | 10 | Rolling mean of TR |
| 2 | Simple | 14 | Rolling mean of TR *(= baseline atr14 formula)* |
| 3 | Simple | 20 | Rolling mean of TR |
| 4 | Wilder | 10 | RMA: `ATR_t = (ATR_{t-1}×(N-1) + TR_t)/N`, seed = mean of first N TR |
| 5 | Wilder | 14 | same |
| 6 | Wilder | 20 | same |

`TR = max(high − low, |high − prev_close|, |low − prev_close|)`  
Bar-0 TR = NaN (no prev close) — same warm-up convention as precomputed `atr14`.

### ATR source

| Source | Meaning |
|---|---|
| Signal | ATR at the touch/signal bar `i` (baseline behavior) |
| Entry | ATR at the entry bar `i+1` |

Variant numbering for the 12-row table: **#1–6 = formulas 1–6 at Signal**, **#7–12 = formulas 1–6 at Entry**.

### Zerodha charge model (per trade, qty = 1, SHORT)

```
brok  = min(0.0003 × entry, 20) + min(0.0003 × exit, 20)
stt   = entry × 0.00025                    # sell (entry) side
txn   = (entry + exit) × 0.0000307
sebi  = (entry + exit) × 0.000001
stamp = exit × 0.000003                    # buy (exit) side
gst   = 0.18 × (brok + txn + sebi)
total = brok + stt + txn + sebi + stamp + gst
zpnl  = raw_pnl - total
```

### Primary metrics

- **ZPF** = sum(winning zpnl) / abs(sum(losing zpnl))
- **ZSh(D)** = (mean(daily_zpnl) / std(daily_zpnl)) × √252
- **PF / Sh(D)** = raw (pre-charge) reference only
- **%ProfDays** = % of trading days with daily_zpnl > 0

---

## 2. Summary table — all 12 variants (sorted by ZPF descending)

| # | Formula | Period | Source | N | PF | ZPF | Sh(D) | ZSh(D) | %ProfDays |
|---:|---|---:|---|---:|---:|---:|---:|---:|---:|
| 2 | Simple | 14 | Signal | 110,641 | 1.135 | **0.767** | 1.949 | -4.180 | 34.8% |
| 4 | Wilder | 10 | Signal | 109,276 | 1.125 | 0.765 | 1.811 | -4.189 | 34.5% |
| 10 | Wilder | 10 | Entry | 109,392 | 1.124 | 0.765 | 1.801 | -4.208 | 34.4% |
| 5 | Wilder | 14 | Signal | 109,677 | 1.124 | 0.764 | 1.817 | -4.258 | 34.6% |
| 11 | Wilder | 14 | Entry | 109,720 | 1.124 | 0.764 | 1.806 | -4.249 | 34.0% |
| 6 | Wilder | 20 | Signal | 110,400 | 1.126 | 0.763 | 1.860 | -4.302 | 34.0% |
| 8 | Simple | 14 | Entry | 110,889 | 1.127 | 0.762 | 1.850 | -4.301 | 34.0% |
| 3 | Simple | 20 | Signal | 109,670 | 1.122 | 0.762 | 1.767 | -4.242 | 34.4% |
| 12 | Wilder | 20 | Entry | 110,424 | 1.124 | 0.762 | 1.837 | -4.349 | 34.3% |
| 1 | Simple | 10 | Signal | 111,689 | 1.129 | 0.761 | 1.891 | -4.331 | 34.4% |
| 9 | Simple | 20 | Entry | 109,695 | 1.120 | 0.761 | 1.741 | -4.282 | 33.9% |
| 7 | Simple | 10 | Entry | 111,720 | 1.128 | 0.760 | 1.861 | -4.328 | 34.2% |

**Best by ZPF:** #2 **Simple14/Signal** — ZPF=0.767, ZSh(D)=-4.180, N=110,641

**Spread:** ZPF only spans **0.760 – 0.767** across all 12 variants. ATR formula/source choice does not meaningfully change viability at the locked 2.0/4.5 combo.

---

## 3. Sanity check — Simple14/Signal vs precomputed atr14

Variant **#2** (Simple, period=14, source=Signal) must reproduce the existing baseline `atr14` numbers.

| Source | N | PF | ZPF | Sh(D) | ZSh(D) | %ProfDays |
|---|---:|---:|---:|---:|---:|---:|
| Simple14/Signal (recomputed) | 110,641 | 1.135 | 0.767 | 1.949 | -4.180 | 34.8% |
| Precomputed atr14/Signal | 110,641 | 1.135 | 0.767 | 1.949 | -4.180 | 34.8% |

**Exact match:** ✅ YES  
Per-bar Simple14 vs precomputed `atr14` also matched at **1.000000** on every stock.

---

## 4. Year-wise breakdown — best variant (#2 Simple14/Signal)

Flag: ✅ ZPF ≥ 1.0 · 🟡 ZPF 0.90–0.99 · ❌ ZPF < 0.90

| Year | N | PF | ZPF | Sh(D) | ZSh(D) | Flag |
|---:|---:|---:|---:|---:|---:|:---:|
| 2015 | 9,203 | 1.181 | 0.833 | 2.904 | -3.299 | ❌ |
| 2016 | 9,994 | 1.152 | 0.787 | 2.743 | -4.811 | ❌ |
| 2017 | 10,032 | 1.162 | 0.756 | 3.064 | -5.935 | ❌ |
| 2018 | 10,340 | 1.213 | 0.858 | 3.617 | -2.981 | ❌ |
| 2019 | 10,380 | 1.182 | 0.820 | 2.906 | -3.571 | ❌ |
| 2020 | 10,236 | 1.157 | 0.881 | 2.003 | -1.789 | ❌ |
| 2021 | 9,974 | 1.198 | 0.837 | 2.870 | -2.932 | ❌ |
| 2022 | 10,070 | 1.071 | 0.730 | 0.996 | -4.720 | ❌ |
| 2023 | 9,893 | 1.026 | 0.635 | 0.444 | -8.267 | ❌ |
| 2024 | 10,020 | 1.130 | 0.750 | 2.012 | -4.897 | ❌ |
| 2025 | 10,499 | 1.102 | 0.683 | 1.646 | -6.696 | ❌ |
| **All** | **110,641** | **1.135** | **0.767** | **1.949** | **-4.180** | ❌ |

**Notes:**
- No year achieves ZPF ≥ 1.0 (or even 🟡 0.90).
- Best year after charges: **2020** (ZPF 0.881).
- Worst year: **2023** (ZPF 0.635, ZSh(D) -8.267).
- ZSh(D) is negative in every year.

---

## 5. Notes

- SL/TP locked at **2.0 / 4.5** (live-deployed combo); this study isolates ATR formula + source only.
- Do **not** compare these ZPF numbers to the SL=6.0/TP=6.0 sweep champion — different risk parameters.
- **Baseline atr14 (Simple14/Signal) is already the best of the 12** — no alternate formula or Entry-bar source improves ZPF.
- Wilder variants cluster just behind (ZPF 0.762–0.765); Entry source is flat-to-slightly-worse vs Signal for every formula.
- Conclusion: changing ATR formula/period/source is **not** a path to viability at 2.0/4.5.

---

## 6. Raw console output

```
ATR Formula Exploration — SL=2.0 TP=4.5
Stocks: 30
Simple14 vs precomputed atr14: match=1.000000 on all 30 stocks

 #  Formula  Per  Source         N      PF     ZPF    Sh(D)   ZSh(D)   %ProfD
 2  Simple    14  Signal   110,641   1.135   0.767    1.949   -4.180    34.8%
 4  Wilder    10  Signal   109,276   1.125   0.765    1.811   -4.189    34.5%
10  Wilder    10  Entry    109,392   1.124   0.765    1.801   -4.208    34.4%
 5  Wilder    14  Signal   109,677   1.124   0.764    1.817   -4.258    34.6%
11  Wilder    14  Entry    109,720   1.124   0.764    1.806   -4.249    34.0%
 6  Wilder    20  Signal   110,400   1.126   0.763    1.860   -4.302    34.0%
 8  Simple    14  Entry    110,889   1.127   0.762    1.850   -4.301    34.0%
 3  Simple    20  Signal   109,670   1.122   0.762    1.767   -4.242    34.4%
12  Wilder    20  Entry    110,424   1.124   0.762    1.837   -4.349    34.3%
 1  Simple    10  Signal   111,689   1.129   0.761    1.891   -4.331    34.4%
 9  Simple    20  Entry    109,695   1.120   0.761    1.741   -4.282    33.9%
 7  Simple    10  Entry    111,720   1.128   0.760    1.861   -4.328    34.2%

SANITY CHECK — Simple14/Signal vs precomputed atr14/Signal
  Simple14/Signal : N=110,641  PF=1.135  ZPF=0.767  Sh(D)=1.949  ZSh(D)=-4.180
  Baseline atr14  : N=110,641  PF=1.135  ZPF=0.767  Sh(D)=1.949  ZSh(D)=-4.180
  Exact match: YES

BEST by ZPF: #2 Simple14/Signal  ZPF=0.767  ZSh(D)=-4.180

YEAR-WISE — #2 Simple14/Signal
  2015   N=   9,203  PF=1.181  ZPF=0.833  Sh(D)=2.904  ZSh(D)=-3.299  ❌
  2016   N=   9,994  PF=1.152  ZPF=0.787  Sh(D)=2.743  ZSh(D)=-4.811  ❌
  2017   N=  10,032  PF=1.162  ZPF=0.756  Sh(D)=3.064  ZSh(D)=-5.935  ❌
  2018   N=  10,340  PF=1.213  ZPF=0.858  Sh(D)=3.617  ZSh(D)=-2.981  ❌
  2019   N=  10,380  PF=1.182  ZPF=0.820  Sh(D)=2.906  ZSh(D)=-3.571  ❌
  2020   N=  10,236  PF=1.157  ZPF=0.881  Sh(D)=2.003  ZSh(D)=-1.789  ❌
  2021   N=   9,974  PF=1.198  ZPF=0.837  Sh(D)=2.870  ZSh(D)=-2.932  ❌
  2022   N=  10,070  PF=1.071  ZPF=0.730  Sh(D)=0.996  ZSh(D)=-4.720  ❌
  2023   N=   9,893  PF=1.026  ZPF=0.635  Sh(D)=0.444  ZSh(D)=-8.267  ❌
  2024   N=  10,020  PF=1.130  ZPF=0.750  Sh(D)=2.012  ZSh(D)=-4.897  ❌
  2025   N=  10,499  PF=1.102  ZPF=0.683  Sh(D)=1.646  ZSh(D)=-6.696  ❌
  All    N= 110,641  PF=1.135  ZPF=0.767  Sh(D)=1.949  ZSh(D)=-4.180  ❌
```
