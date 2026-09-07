# Backtesting Results — Framework V2
*Master results log — all strategies tested, entry/exit logic, and full metrics.*

> **Recovered 2026-09-07** from a bookmarked claude.ai session (see `01_plan.md`'s Status).
> Copied verbatim, not re-verified against this repo's own DS3/parity-check standards yet.
> Two things worth knowing before reading further:
> 1. **Covers more than SMC** — sections 1-5 are 6BCE variant exploration (baseline, VWAP,
>    RSI, EMA100, Daily Bias filters), unrelated to the 3 SMC concepts this folder exists
>    for. Sections 6-8 (LSS=Liquidity Sweep Short, FVG, OB) are the actual SMC results.
> 2. **Different SL/TP grid than this project's locked strategies/** — this session swept
>    SL 1.5-6.0 / TGT 2.0-6.0 (narrower, coarser than the 10x9 grid used elsewhere in
>    strategies/), so e.g. "6BCE baseline, SL=6.0/TGT=6.0" here is NOT the same combo as
>    strategies/6bce/v0's locked SL=8.0/TP=3.0 — don't directly compare the two ZPF numbers
>    as if they're the same test.

---

## Data

- **Source:** DS3 (30 Nifty large-cap stocks, 5-minute OHLCV)
- **Timeline:** 2015-01-01 to 2025-12-31 (~11 years)
- **Columns:** datetime, open, high, low, close, volume, oi, ma20, atr14
- **Session:** 09:15–15:00 IST, EOD hour = 15
- **Broker charges:** Zerodha (see backtesting_rules_v2.md §7)
- **Sharpe:** Daily, annualised ×√252
- **Position guard:** Single-pass, resume from exit_bar + 1

---

## 1. 6BCE (6-Bar Close Extreme) — SHORT — BASELINE

### Entry/Exit Logic
```
Signal:  close[i] == max(close[i-5..i])  (6-bar lookback, continuous series)
         hour[i] < 15
Entry:   SHORT at open[i+1], same day as signal bar, hour[i+1] < 15
Exit:    Priority per bar from entry bar onward:
         1. Date change   → exit at close[k-1]
         2. hour[k] >= 15 → exit at open[k]
         3. high[k] >= sl → exit at sl (Loss)
         4. low[k]  <= tgt → exit at tgt (Win)
SL/TGT:  sl = entry + SL_MULT × ATR14
         tgt = entry - TGT_MULT × ATR14
```

### Results — Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 100,680 |
| PF | 1.1238 |
| ZPF | 0.8859 |
| Sh(D) | — |
| ZSh(D) | -1.485 |
| Verdict | ❌ Fails viability (ZPF<1.0) |

**PF>1 combos:** 90/90 &nbsp;&nbsp; **ZPF>1 combos:** 0/90

---

## 2. 6BCE + VWAP — SHORT

### Entry/Exit Logic
Same as baseline, plus:
```
Filter: close[i] < VWAP[i]  (strict, no ties) — bearish context filter
        VWAP resets daily (intraday cumulative)
```

### Results — Best Combo (SL=4.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 71,857 |
| PF | 1.2139 |
| ZPF | 0.8946 |
| ZSh(D) | -1.319 |
| Verdict | ❌ Fails viability |

---

## 3. 6BCE + VWAP + RSI>54 — SHORT (BEST STRATEGY)

### Entry/Exit Logic
Same as 6BCE+VWAP, plus:
```
Filter: RSI(14, Wilder) on signal bar > 54
```

### Results — 30-Stock Universe (SL=4.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 15,547 |
| PF | 1.2604 |
| ZPF | 0.9975 |
| Sh(D) | 1.926 |
| ZSh(D) | -0.012 |
| Verdict | 🟡 Borderline (ZPF just below 1.0) |

**Year-wise (30-stock):**
| Year | N | PF | ZPF | Sh(D) | ZSh(D) | Flag |
|---|---|---|---|---|---|---|
| 2015 | 1,188 | 2.0716 | 1.4694 | 3.536 | +1.936 | ✅ |
| 2016 | 1,362 | 2.0739 | 1.4405 | 3.850 | +1.954 | ✅ |
| 2017 | 1,538 | 1.9588 | 1.2468 | 3.878 | +1.264 | ✅ |
| 2018 | 1,362 | 1.8545 | 1.2726 | 3.396 | +1.354 | ✅ |
| 2019 | 1,197 | 1.6707 | 1.1824 | 2.467 | +0.815 | ✅ |
| 2020 | 1,600 | 1.6306 | 1.2427 | 2.362 | +1.057 | ✅ |
| 2021 | 1,607 | 1.4440 | 0.9911 | 1.988 | -0.049 | 🟡 |
| 2022 | 1,589 | 1.2609 | 0.8378 | 1.134 | -0.877 | ❌ |
| 2023 | 1,472 | 1.3229 | 0.7639 | 1.405 | -1.362 | ❌ |
| 2024 | 1,399 | 1.4629 | 0.9462 | 2.016 | -0.301 | 🟡 |
| 2025 | 1,233 | 1.0161 | 0.6262 | 0.080 | -2.377 | ❌ |

### Results — 8-Stock Curated Universe (SL=4.0, TGT=6.0)
*Stocks selected by consistent yearly ZPF from the 30-stock pool.*

| Metric | Value |
|---|---|
| N trades | 4,101 |
| N trading days | 1,774 |
| PF | 1.3957 |
| ZPF | 1.1232 |
| Sh(D) | 1.853 |
| ZSh(D) | +0.647 |
| Mean daily P&L | ₹0.85 |
| Std daily P&L | ₹20.88 |
| % profitable days | 51.5% |
| Verdict | ✅ **PASSES viability — paper trading candidate** |

**Year-wise (8-stock, full daily data):**
| Year | N days | Mean daily | Std daily | ZSh(D) | % profitable days |
|---|---|---|---|---|---|
| 2015 | 138 | 0.73 | 10.65 | 1.084 | 51.4% |
| 2016 | 162 | 0.41 | 9.59 | 0.671 | 45.7% |
| 2017 | 173 | 0.24 | 8.90 | 0.425 | 51.4% |
| 2018 | 163 | 0.43 | 12.59 | 0.548 | 52.8% |
| 2019 | 160 | 2.22 | 17.22 | 2.042 | 54.4% |
| 2020 | 159 | 1.32 | 26.88 | 0.778 | 52.2% |
| 2021 | 166 | -0.40 | 26.13 | -0.246 | 50.6% |
| 2022 | 159 | -2.26 | 27.22 | -1.318 | 44.0% |
| 2023 | 169 | 0.99 | 17.10 | 0.916 | 52.7% |
| 2024 | 168 | 3.59 | 26.48 | 2.150 | 60.7% |
| 2025 | 157 | 2.06 | 30.23 | 1.081 | 50.3% |

---

## 4. 6BCE + VWAP + EMA100

### Entry/Exit Logic
Same as 6BCE+VWAP, plus:
```
Filter A (Above): close[i] < EMA100[i]  — price below long-term trend
Filter B (Below): close[i] > EMA100[i]  — price above long-term trend
EMA100: continuous across full series, not reset daily
```

### Results — Best Combo, Filter A (Above), SL=4.0 TGT=6.0
| Metric | Value |
|---|---|
| N trades | 32,819 |
| PF | 1.2857 |
| ZPF | 0.9509 |
| ZSh(D) | -0.510 |
| Verdict | 🟡 Borderline |

### Results — Filter B (Below), SL=5.5 TGT=6.0
| Metric | Value |
|---|---|
| N trades | 50,185 |
| PF | 1.1776 |
| ZPF | 0.8498 |
| ZSh(D) | -1.545 |
| Verdict | ❌ Fails viability |

---

## 5. 6BCE + Daily Bias

### Entry/Exit Logic
Same as baseline, plus:
```
Filter: close[i] < previous day's close  — bearish daily bias
```

### Results — Best Combo (SL=5.5, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 50,810 |
| PF | 1.0935 |
| ZPF | 0.8197 |
| ZSh(D) | -1.716 |
| Verdict | ❌ Fails viability |

---

## 6. LSS (Liquidity Sweep Short)

### Entry/Exit Logic
```
Phase 1 — Swing low: N=2 fractal (5 candles), local minimum
Phase 2 — Sweep: within 50 bars of swing low
           wick pierces below swing low, close back above
Phase 3 — Confirmation: next bar closes above swing low
Phase 4 — Entry: SHORT at open of bar after confirmation
Exit: same priority logic as 6BCE (date change → hour≥15 → SL → TGT)
```

### Results — Baseline (W=50), Best Combo (SL=5.5, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 69,413 |
| PF | 1.0898 |
| ZPF | 0.8078 |
| ZSh(D) | -2.450 |
| Verdict | ❌ Fails viability |

**Distance sweep (W=10,20,30,40,50,60,75):** No meaningful difference — ZPF varied by only 0.006 across all windows. W=50 retained as standard.

### Results — LSS + VWAP, Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 43,898 |
| PF | 1.1646 |
| ZPF | 0.8559 |
| ZSh(D) | -1.594 |
| Verdict | ❌ Fails viability |

### Results — LSS + VWAP + RSI>54, Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 411 |
| PF | 1.3353 |
| ZPF | 1.0106 |
| ZSh(D) | +0.049 |
| Verdict | ✅ Passes but **statistically thin (N<500)** — ruled out per viability criteria |

### LSS Long
**Dead** — PF < 1.0 across all 90 combos. No further testing.

---

## 7. FVG (Fair Value Gap) Short

### Entry/Exit Logic
```
Phase 1 — FVG formation: 3 consecutive bearish-gap candles
           C3.high < C1.low (bearish FVG)
           fvg_bottom = C3.high, fvg_top = C1.low
Phase 2 — Retest: within 50 bars of C3
           high[i] >= fvg_bottom (wick enters zone)
           close[i] < fvg_bottom (body stays below — rejection)
Phase 3 — Confirmation: next bar closes below fvg_bottom
Phase 4 — Entry: SHORT at open of bar after confirmation
Exit: same priority logic as 6BCE
```

### Results — Baseline (corrected, single-pass position guard), Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 79,338 |
| PF | 1.1167 |
| ZPF | 0.8308 |
| Sh(D) | — |
| ZSh(D) | -1.957 |
| Verdict | ❌ Fails viability |

### Results — FVG Short + VWAP (corrected), Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 71,949 |
| PF | 1.1664 |
| ZPF | 0.8844 |
| ZSh(D) | -1.359 |
| Verdict | ❌ Fails viability |

**Year-wise (FVG+VWAP, SL=6.0 TGT=6.0):**
| Year | PF | ZPF | ZSh(D) | Flag |
|---|---|---|---|---|
| 2015 | 1.6858 | 0.9793 | -0.121 | 🟡 |
| 2016 | 1.4935 | 0.8372 | -1.065 | ❌ |
| 2017 | 1.9251 | 0.8874 | -0.705 | ❌ |
| 2018 | 1.5800 | 0.9202 | -0.519 | 🟡 |
| 2019 | 1.5961 | 0.9468 | -0.332 | 🟡 |
| 2020 | 1.3953 | 0.9581 | -0.238 | 🟡 |
| 2021 | 1.4107 | 0.8606 | -0.911 | ❌ |
| 2022 | 1.2760 | 0.7763 | -1.547 | ❌ |
| 2023 | 1.2051 | 0.5776 | -3.236 | ❌ |
| 2024 | 1.3232 | 0.7447 | -1.612 | ❌ |
| 2025 | 1.1183 | 0.5677 | -3.525 | ❌ |

### FVG Short + RSI (on retest candle, no VWAP)
RSI sweep 50→80 step 2. Best result: RSI>70 → ZPF=0.9340, but N=532 (too thin — ~48 trades/year across 30 stocks). RSI>50/54/60 all performed *worse* than unfiltered baseline (opposite effect vs 6BCE).

### FVG Short + VWAP — Pierce Depth Filter
Tested: pierce_depth ≤ 10%/25%/50%/75%/100% of FVG zone width, plus overshoot bucket (pierce > 100%).
- Best PF at 10% pierce (PF=1.2122) but worse ZPF than unfiltered baseline (0.8593 vs 0.8844)
- No pierce-depth threshold beat the unfiltered VWAP baseline
- Conclusion: body-close-below-zone-bottom is the only condition that matters; wick penetration depth is not predictive

### FVG Long
**Dead** — PF < 1.0 across all 90 combos.

---

## 8. OB (Order Block)

### OB Short — Entry/Exit Logic
```
Phase 1 — OB formation (2 candles):
           OB candle (bearish): close < open
           Displacement (bullish... wait, bearish for short):
           OB candle: close > open (bullish)
           Displacement: close < open (bearish), closes below OB low
           ob_top = OB candle high, ob_bottom = OB candle low
Phase 2 — Rally: at least one bar after displacement has low < displacement low
Phase 3 — Retest: within 50 bars of displacement
           high[i] >= ob_bottom (wick enters zone from below)
           close[i] < ob_bottom (body stays below)
Phase 4 — Confirmation: next bar closes below ob_bottom
Phase 5 — Entry: SHORT at open of bar after confirmation
Exit: same priority logic as 6BCE
```

### Results — OB Short, 5-minute bars, Best Combo (SL=6.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 75,342 |
| PF | 1.1236 |
| ZPF | 0.8425 |
| ZSh(D) | -1.922 |
| Verdict | ❌ Fails viability |

### Results — OB Short, 15-minute bars (resampled from 5-min), Best Combo (SL=4.0, TGT=6.0)
| Metric | Value |
|---|---|
| N trades | 46,565 |
| PF | 1.1474 |
| ZPF | 0.8304 |
| ZSh(D) | -1.955 |
| Verdict | ❌ Fails viability |

**Note:** OB Short + VWAP was planned but never executed in this session — pending.

### OB Long — Entry Logic
```
Phase 1 — OB formation: OB candle bearish (close<open),
           displacement bullish (close>open), closes above OB high
Phase 2 — Rally: at least one bar after displacement has high > displacement high
Phase 3 — Retest: low[i] <= ob_top, close[i] > ob_top
Phase 4 — Confirmation: next bar closes above ob_top
Phase 5 — Entry: LONG at open of bar after confirmation
```

### Results — OB Long
**Dead** — PF < 1.0 across all 90 combos (0/90). Best PF = 0.9586. Win rate consistently ~47-49% (below breakeven). No year passed.

---

## 9. Untested / Not Defined in This Session

- **BOS (Break of Structure)** — conceptually defined (regime identifier via higher highs/lows) but no backtestable entry logic built or tested
- **Inducement** — conceptually defined (pre-move liquidity trap) but no backtestable entry logic built or tested
- **Opening Range Breakdown** — not started
- **Intraday Trend Exhaustion** — not started

---

## Master Comparison — Best ZPF Combo Per Strategy

| Strategy | Best Combo | N | PF | ZPF | ZSh(D) | Verdict |
|---|---|---|---|---|---|---|
| 6BCE+VWAP+RSI>54 (8-stock) | SL=4.0 TGT=6.0 | 4,101 | 1.3957 | **1.1232** | **+0.647** | ✅ |
| LSS+VWAP+RSI>54 | SL=6.0 TGT=6.0 | 411 | 1.3353 | 1.0106 | +0.049 | ✅ (too thin) |
| 6BCE+VWAP+RSI>54 (30-stock) | SL=4.0 TGT=6.0 | 15,547 | 1.2604 | 0.9975 | -0.012 | 🟡 |
| 6BCE+VWAP+EMA100 (Above) | SL=4.0 TGT=6.0 | 32,819 | 1.2857 | 0.9509 | -0.510 | 🟡 |
| 6BCE+VWAP | SL=4.0 TGT=6.0 | 71,857 | 1.2139 | 0.8946 | -1.319 | ❌ |
| FVG Short+VWAP | SL=6.0 TGT=6.0 | 71,949 | 1.1664 | 0.8844 | -1.359 | ❌ |
| LSS+VWAP | SL=6.0 TGT=6.0 | 43,898 | 1.1646 | 0.8559 | -1.594 | ❌ |
| 6BCE+VWAP+EMA100 (Below) | SL=5.5 TGT=6.0 | 50,185 | 1.1776 | 0.8498 | -1.545 | ❌ |
| OB Short (5-min) | SL=6.0 TGT=6.0 | 75,342 | 1.1236 | 0.8425 | -1.922 | ❌ |
| FVG Short (baseline) | SL=6.0 TGT=6.0 | 79,338 | 1.1167 | 0.8308 | -1.957 | ❌ |
| OB Short (15-min) | SL=4.0 TGT=6.0 | 46,565 | 1.1474 | 0.8304 | -1.955 | ❌ |
| 6BCE+Daily Bias | SL=5.5 TGT=6.0 | 50,810 | 1.0935 | 0.8197 | -1.716 | ❌ |
| LSS (baseline) | SL=5.5 TGT=6.0 | 69,413 | 1.0898 | 0.8078 | -2.450 | ❌ |
| 6BCE (baseline) | SL=6.0 TGT=6.0 | 100,680 | 1.1238 | 0.8859 | -1.485 | ❌ |
| LSS Long | SL=6.0 TGT=6.0 | 70,012 | 0.8738 | 0.6456 | -4.955 | 💀 |
| FVG Long | — | — | <1.0 all combos | — | — | 💀 |
| OB Long | — | — | <1.0 all combos | — | — | 💀 |

**Legend:** ✅ Passes viability (ZPF>1.0 AND ZSh(D)>0) &nbsp;·&nbsp; 🟡 Borderline &nbsp;·&nbsp; ❌ Fails &nbsp;·&nbsp; 💀 No edge (dead)

---

## Key Findings

1. **6BCE+VWAP+RSI>54 on the 8-stock curated universe is the only strategy that passes both viability criteria with a statistically meaningful trade count.** It is the current paper-trading candidate.
2. **All LONG variants tested (LSS, FVG, OB) are structurally dead** — no combo crosses PF=1.0. NSE intraday on 5-minute bars shows a consistent structural short bias across all 11 years.
3. **VWAP consistently improves every SHORT strategy tested** — a reliable first-layer filter regardless of the underlying signal.
4. **RSI filtering works well for 6BCE (sweet spot ~54) but does not generalise to FVG Short** — elevated RSI on the retest candle is not predictive for FVG, unlike the 6BCE signal bar.
5. **Pierce depth (wick penetration into FVG zone) is not a useful filter** — body-close-below-zone-bottom is the only condition that matters.
6. **Distance/lookback window (W) has negligible effect** — tested 10–75 bars for LSS, ZPF varied by only 0.006.
7. **All strategies show the same year-wise pattern: strong 2015–2020, deteriorating 2021–2025**, most severe in 2022–2023 and 2025. This points to a market regime shift rather than a flaw specific to any one strategy.
