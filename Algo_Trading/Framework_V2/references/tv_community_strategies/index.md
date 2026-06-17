# TV Community Strategies — fv2 Reference

Strategies sourced from TradingView community for study and adaptation into fv2.

---

## 0. Baseline (Reference Point)
- **Signal**: MA20 Bounce, no volume filter — touch (low≤MA20, open>MA20) → bounce (close>MA20 within tb3) → entry bounce+1 open
- **Script**: Algo_Trading/Framework_V2/scripts/_temp_per_stock_baseline.py
- **Backtest** (fv2 CSV, 30 stocks, 2022–2025, SL=2.5×ATR, TGT=4.5×ATR, EOD=15:00):
  N=136,849 | WR=42.6% | BE=45.0% | **PF=0.932** | Net PnL=-16,525.7
- Every TV community strategy below is compared against this baseline.

**Per-stock (sorted by PF) — 6/30 stocks PF≥1:**

| Stock | N | WR% | BE% | PF | Net PnL |
|---|---|---|---|---|---|
| ASHOKLEY | 4,500 | 42.8% | 40.3% | 1.108 | 110.0 |
| SUNPHARMA | 4,652 | 46.9% | 44.9% | 1.084 | 980.5 |
| BHARTIARTL | 4,726 | 44.4% | 43.9% | 1.020 | 215.1 |
| HDFCBANK | 4,831 | 44.9% | 44.5% | 1.017 | 106.8 |
| ICICIBANK | 4,704 | 47.3% | 47.0% | 1.015 | 132.6 |
| INDUSINDBK | 4,501 | 44.5% | 44.4% | 1.003 | 36.5 |

**Cumulative Top-N stacking (best PF first):**

| Combo | N | WR% | BE% | PF | Net PnL |
|---|---|---|---|---|---|
| Top 1 | 4,500 | 42.8% | 40.3% | 1.108 | 110.0 |
| Top 3 | 13,878 | 44.7% | 43.4% | 1.055 | 1,305.6 |
| **Top 6** | **27,914** | **45.1%** | **44.4%** | **1.030** | **1,581.5** |
| Top 9 | 42,020 | 44.6% | 44.1% | 1.022 | 1,315.5 |
| Top 13 | 59,952 | 44.3% | 44.3% | 1.000 | -0.9 |
| Top 30 (all) | 136,849 | 42.6% | 44.3% | 0.932 | -16,525.7 |

Top 6 is the sweet spot — peak net PnL, PF holds just above breakeven, before more stocks dilute it back under 1.0 by Top 13.

---

## 1. Daily Kijun with Bounce Alerts
- **Author**: Pine Wizard
- **Boosts**: 663
- **URL**: https://in.tradingview.com/script/booX2yrR-Daily-Kijun-with-Bounce-Alerts/
- **Signal**: 2-bar bounce off 50-period Kijun-Sen (daily timeframe)
- **Formula**: Kijun-HL — (highest HIGH + lowest LOW) / 2 over 50 days (our adaptation; original uses CLOSE/CLOSE)
- **Pine Script saved**: "Kijun fv2 Bounce" (USER;745732681f7340468f00a6d0bbead6ff)
- **Python backtest**: Algo_Trading/Framework_V2/scripts/kijun_bounce_backtest.py
- **Subset analysis**: Algo_Trading/Framework_V2/scripts/_kijun_subset_analysis.py

### Backtest Results (fv2 CSV, 2022–2025, SL=2.5× ATR, TGT=3.0× ATR, EOD=15:00)

**Full 30-stock universe (Kijun-HL):**
- Total trades: 790 | WR: 45.6% | PF: 0.848 | Net PnL: -321.01
- 11/30 stocks profitable (PF>1 and WR>BE)

**11-stock winner subset (Kijun-HL, sorted by PF):**

| Stock | N | WR% | BE% | PF | Net PnL |
|---|---|---|---|---|---|
| VEDL | 24 | 54.2% | 30.9% | 2.637 | 28.13 |
| SBIN | 21 | 61.9% | 47.6% | 1.791 | 22.58 |
| NTPC | 32 | 53.1% | 44.2% | 1.432 | 7.58 |
| BHARTIARTL | 29 | 55.2% | 46.3% | 1.425 | 34.51 |
| ICICIBANK | 32 | 59.4% | 51.4% | 1.380 | 29.38 |
| ADANIPORTS | 19 | 47.4% | 41.0% | 1.294 | 20.78 |
| NATIONALUM | 25 | 52.0% | 46.5% | 1.249 | 3.34 |
| PNB | 29 | 55.2% | 51.0% | 1.183 | 1.47 |
| ITC | 28 | 50.0% | 46.9% | 1.134 | 2.82 |
| ASHOKLEY | 11 | 36.4% | 34.1% | 1.102 | 0.27 |
| JSWSTEEL | 29 | 51.7% | 51.5% | 1.011 | 0.69 |

**Best 5-stock combo**: VEDL + SBIN + NTPC + BHARTIARTL + ICICIBANK
- N=138 | WR=56.5% | BE=45.6% | PF=1.551 | Net PnL=122.18

**Year-by-year trade count (Top 11):**

| Stock | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|
| VEDL | 4 | 7 | 8 | 5 | 24 |
| SBIN | 4 | 8 | 6 | 3 | 21 |
| NTPC | 10 | 6 | 3 | 13 | 32 |
| BHARTIARTL | 9 | 4 | 1 | 15 | 29 |
| ICICIBANK | 5 | 10 | 11 | 6 | 32 |
| ADANIPORTS | 5 | 5 | 6 | 3 | 19 |
| NATIONALUM | 4 | 12 | 1 | 8 | 25 |
| PNB | 4 | 2 | 14 | 9 | 29 |
| ITC | 6 | 3 | 6 | 13 | 28 |
| ASHOKLEY | 2 | 7 | 0 | 2 | 11 |
| JSWSTEEL | 5 | 8 | 10 | 6 | 29 |
| **TOTAL** | **58** | **72** | **66** | **83** | **279** |

**Cumulative portfolio analysis (stacking by PF rank, best first):**

| Combo | N | WR% | BE% | PF | Net PnL | Stock added |
|---|---|---|---|---|---|---|
| Top 1 | 24 | 54.2% | 30.9% | 2.637 | 28.13 | VEDL |
| Top 2 | 45 | 57.8% | 39.4% | 2.109 | 50.71 | +SBIN |
| Top 3 | 77 | 55.8% | 39.7% | 1.921 | 58.29 | +NTPC |
| Top 4 | 106 | 55.7% | 43.3% | 1.643 | 92.80 | +BHARTIARTL |
| **Top 5** | **138** | **56.5%** | **45.6%** | **1.551** | **122.18** | **+ICICIBANK** |
| Top 6 | 157 | 55.4% | 45.5% | 1.489 | 142.96 | +ADANIPORTS |
| Top 7 | 182 | 54.9% | 45.2% | 1.478 | 146.30 | +NATIONALUM |
| Top 8 | 211 | 55.0% | 45.4% | 1.471 | 147.77 | +PNB |
| Top 9 | 239 | 54.4% | 45.1% | 1.450 | 150.59 | +ITC |
| Top 10 | 250 | 53.6% | 44.4% | 1.447 | 150.86 | +ASHOKLEY |
| Top 11 | 279 | 53.4% | 45.4% | 1.378 | 151.55 | +JSWSTEEL |

### Verdict
- Edge is real but trade frequency is too low (~70 trades/year across 11 stocks = ~6-7/stock/year)
- Not viable as standalone strategy — needs higher frequency signal
- Best use: as a quality filter on top of a higher-frequency strategy (e.g. MA20 Bounce or HMA Bounce)
- Next step: explore HMA Bounce as primary frequency generator

---

## 2. Trading ABC
- **Status**: Backtested on BHARTIARTL + scaled to 30 stocks — PF below baseline at full universe
- **Signal**: Trend cloud (6 MAs) + ZigZag(8) ABC pattern + Fib retracement check (38.2-61.8% ±5%) + MA bounce confirmation, long only
- **Script**: Algo_Trading/Framework_V2/scripts/trading_abc_backtest.py
- **Entry**: next bar's open after the triangle (bounce-confirmed) bar

### Backtest Results (fv2 CSV, 2022–2025, EOD=15:00)

**BHARTIARTL only — SL/TGT sweep:**

| SL | TGT | R:R | N | PFT-WR | TGT-WR | BE% | PF | NetPnL |
|---|---|---|---|---|---|---|---|---|
| 2.0 | 3.0 | 1.50 | 99 | 45.5% | 33.3% | 44.4% | 1.045 | 11.27 |
| 2.0 | 4.0 | 2.00 | 96 | 43.8% | 25.0% | 41.0% | 1.119 | 29.87 |
| **2.5** | **3.5** | **1.40** | 96 | 50.0% | 31.2% | 46.4% | **1.156** | **40.73** |
| 2.5 | 4.5 | 1.80 | 95 | 48.4% | 17.9% | 45.9% | 1.106 | 28.17 |
| 2.0 | 5.0 | 2.50 | 96 | 43.8% | 13.5% | 42.2% | 1.067 | 16.72 |
| 3.0 | 4.5 | 1.50 | 94 | 50.0% | 18.1% | 48.8% | 1.050 | 14.03 |
| 1.5 | 3.0 | 2.00 | 104 | 40.4% | 30.8% | 37.9% | 1.108 | 24.12 |

BHARTIARTL year-by-year (SL=2.5/TGT=3.5, best combo): 2022 PF=1.571, 2023 PF=2.479, 2024 PF=1.438, **2025 PF=0.558** (regime break, not target-distance related — held even after tightening target).

**Full 30-stock universe:**

| Combo | N | PFT-WR | TGT-WR | BE% | PF | NetPnL |
|---|---|---|---|---|---|---|
| 2.5/4.5 (1.8R) | 3,006 | 41.7% | 13.3% | 45.7% | 0.849 | -901.64 |
| 2.5/3.5 (1.4R) | 3,049 | 43.2% | 20.8% | 46.4% | 0.878 | -725.95 |

**Per-stock (SL=2.5/TGT=3.5, sorted by PF) — 9/30 stocks PF≥1:**

| Stock | N | WR% | BE% | PF | Net PnL |
|---|---|---|---|---|---|
| DABUR | 105 | 56.2% | 43.0% | 1.702 | 78.23 |
| CIPLA | 78 | 53.8% | 46.7% | 1.329 | 59.91 |
| VEDL | 97 | 49.5% | 44.0% | 1.249 | 23.59 |
| BHARTIARTL | 96 | 50.0% | 46.4% | 1.156 | 40.73 |
| TATASTEEL | 108 | 41.7% | 39.4% | 1.099 | 3.39 |
| NATIONALUM | 115 | 44.3% | 42.3% | 1.087 | 4.27 |
| RELIANCE | 94 | 47.9% | 46.7% | 1.048 | 10.23 |
| SBIN | 114 | 44.7% | 44.3% | 1.018 | 2.85 |
| ASHOKLEY | 104 | 46.2% | 46.1% | 1.003 | 0.07 |

**Cumulative Top-N stacking (best PF first):**

| Combo | N | WR% | BE% | PF | Net PnL |
|---|---|---|---|---|---|
| Top 1 | 105 | 56.2% | 43.0% | 1.702 | 78.23 |
| Top 4 | 376 | 52.4% | 45.6% | 1.312 | 202.46 |
| Top 6 | 599 | 48.9% | 42.7% | 1.287 | 210.12 |
| **Top 9** | **911** | **48.0%** | **43.5%** | **1.197** | **223.26** |
| Top 13 | 1,325 | 47.0% | 45.1% | 1.082 | 166.23 |
| Top 14 | 1,417 | 46.9% | 46.7% | 1.009 | 27.73 |
| Top 30 (all) | 3,049 | 43.2% | 46.4% | 0.878 | -725.95 |

Top 9 is the sweet spot — peak net PnL, PF=1.197 with comfortable WR/BE margin. PF crosses below 1.0 after Top 14.

### Verdict
- Single-stock promise (PF 1.1–1.16 on BHARTIARTL) does **not** survive scaling to 30 stocks unfiltered
- Raw 30-stock PF (0.849-0.878) lands below baseline (0.932) and Kijun-HL (0.848)
- **But the Top-9 subset (PF=1.197) beats both the baseline's Top-6 subset (PF=1.030) and Kijun-HL's Top-11 subset (PF=1.378 is higher, but only 279 trades/4yr — Trading ABC Top-9 has 911, ~3x the frequency)**
- Same pattern as fv1/fv2 history: stock-specific edge ≠ universe-wide edge, but subset filtering recovers an edge here too
- Next: could combine with Kijun as a quality filter, or test subset stability with walk-forward (is Top-9 stock list stable out-of-sample, or overfit to these 4 years)

---

_Add new entries below as we reference more community strategies._
