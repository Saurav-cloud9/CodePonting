# fv2 Baseline v1.1 Formula — MA Bounce (Wick-Only + Above VWAP + Below EMA100)

**Script:** `Framework_V2/core/ma_baseline_v1_1.py`
**Data:** 30 stocks | 2022–2025 | 5-min bars | fv2 CSVs
**Locked:** 2026-07-03
**Pine:** `Framework_V2/core/pine/fv2_baseline_v1_1.pine`
**Extends:** [[ma_baseline_v1_formula]] (two additional filters at touch bar)

---

## What Changed vs v1

| | v1 | v2 |
|---|---|---|
| Touch condition | `low <= MA20 AND open > MA20 AND close > MA20` | Same + `close >= VWAP AND close < EMA100` |
| VWAP filter | None | Touch bar close must be above VWAP |
| EMA filter | None | Touch bar close must be below EMA100 |
| Trades (N) | 39,589 | 8,377 |
| Profit Factor | 0.908 | 1.010 |

---

## Signal Logic

| Step | Rule |
|---|---|
| Touch | `low <= MA20 AND open > MA20 AND close > MA20` |
| VWAP filter | `close >= VWAP` at touch bar |
| EMA filter | `close < EMA100` at touch bar |
| Touch cutoff | Skip if `hour >= 15` |
| Entry | Next bar open after touch bar |
| Entry guard | Skip if entry bar is next day |
| Stop Loss | `entry - 2.5 × ATR14` |
| Target | `entry + 4.5 × ATR14` |
| EOD exit | Exit at open of first bar where `hour >= 15` |
| Position guard | `i = k + 1` — no new trade until current trade exits |

---

## Config

| Param | Value |
|---|---|
| MA | MA20 (simple moving average, 20 bars) |
| ATR | ATR14 (precomputed, fv2 CSV) |
| EMA span | 100 bars |
| SL multiplier | 2.5 |
| TP multiplier | 4.5 |
| EOD hard stop | 15:00 bar open |
| Slippage | None |
| Charges | None |

---

## Aggregate Results — 30 Stocks, 2022–2025

| Metric | Baseline | v1 | v2 | Delta (v1→v2) |
|---|---|---|---|---|
| Total Trades (N) | 49,039 | 39,589 | 8,377 | -31,212 (-78.8%) |
| Profit Factor | 0.922 | 0.908 | 1.010 | +0.102 |
| NPF (Kotak Neo) | — | — | 0.588 | — |

---

## Year-wise PF

| Year | v2 PF | Note |
|---|---|---|
| 2022 | 1.018 | Above break-even |
| 2023 | 0.985 | Just below |
| 2024 | 1.084 | Strongest year |
| 2025 | 0.947 | Below — regime effect |

Pattern: 2022/2024 consistently above 1.0, 2023/2025 below. Not filter weakness — likely market regime.

---

## Filter Contribution

| Step | PF | N | Lift |
|---|---|---|---|
| Baseline | 0.922 | 49,039 | — |
| + wick-only (v1) | 0.908 | 39,589 | -0.014 |
| + Above VWAP | 0.949 | 20,474 | +0.041 |
| + Below EMA100 (v2) | 1.010 | 8,377 | +0.061 |

VWAP was the first meaningful lift; EMA100 pushed it over break-even. Both filters are structural (price context), not signal overlays.

---

## NPF Gap

| PF | NPF (Kotak Neo) | Gap to NPF=1.0 |
|---|---|---|
| 1.010 | 0.588 | -0.412 |

NPF ≈ PF − 0.3 to 0.4 at ~900 INR price. Need PF ≥ 1.5 for NPF ≈ 1.1–1.2 (comfortably profitable). v2 is raw-edge positive but not yet live-tradeable.
