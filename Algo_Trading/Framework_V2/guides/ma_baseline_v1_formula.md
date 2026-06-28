# fv2 Baseline v1 Formula — MA Bounce (Wick-Only Touch)

**Script:** `Framework_V2/core/ma_baseline_v1.py`
**Pine:** `Framework_V2/scripts/fv2_baseline_v1.pine`
**Data:** 30 stocks | 2022–2025 | 5-min bars | fv2 CSVs
**Locked:** 2026-06-28
**Extends:** [[ma_baseline_formula]] (single change to touch condition)

---

## What Changed vs Baseline

| | Baseline | v1 |
|---|---|---|
| Touch condition | `low <= MA20` | `low <= MA20 AND open > MA20 AND close > MA20` |
| Touch type captured | All 5 types | Wick-only (body stays above MA20) |
| Bounce bar | Any bar with `close > MA20` within 3 bars | Same-bar always (touch requires close > MA20) |

**Effect:** Touch and bounce always occur on the same bar in v1. Entry fills at touch+1 open. Purple triangle on TV = same-bar touch+bounce.

---

## Touch Types — What v1 Excludes

| Type | Baseline | v1 |
|---|---|---|
| Wick touch (low ≤ MA, open > MA, close > MA) | ✓ | ✓ |
| Close pierce (low ≤ MA, open > MA, close ≤ MA) | ✓ | ✗ |
| Body touch (low ≤ MA, open ≤ MA, close > MA) | ✓ | ✗ |
| Body cross (low ≤ MA, open ≤ MA, close ≤ MA) | ✓ | ✗ |
| Gap down (open ≤ MA) | ✓ | ✗ |

---

## Signal Logic

| Step | Rule |
|---|---|
| Touch | `low <= MA20 AND open > MA20 AND close > MA20` on any bar |
| Touch cutoff | Skip if `hour >= 15` |
| Bounce | Same bar as touch (guaranteed by close > MA20 in touch condition) |
| Entry | Next bar open after bounce bar |
| Entry guard | Skip if entry bar is next day |
| Stop Loss | `entry - 2.5 × ATR14` |
| Target | `entry + 4.5 × ATR14` |
| EOD exit | Exit at open of first bar where `hour >= 15` |
| Exit order | EOD checked first, then TGT, then SL |
| Position guard | `i = k + 1` — no new trade until current trade exits |

---

## Config (same as baseline)

| Param | Value |
|---|---|
| MA | MA20 (simple moving average, 20 bars) |
| ATR | ATR14 (precomputed, fv2 CSV) |
| SL multiplier | 2.5 |
| TGT multiplier | 4.5 |
| Max bounce window | 3 bars (not used — always same-bar in v1) |
| EOD hard stop | 15:00 bar open |
| Slippage | None |
| Charges | None |

---

## Aggregate Results — 30 Stocks, 2022–2025

| Metric | Baseline | v1 | Delta |
|---|---|---|---|
| Total Trades (N) | 49,039 | 39,589 | -9,450 (-19.3%) |
| Profit Factor | 0.922 | 0.908 | -0.014 |
| Pure WR (TGT hits) | 15.0% | 12.7% | -2.3pp |

### Removed Trades Breakdown (Baseline → v1)

| Outcome | Removed | Note |
|---|---|---|
| L | 4,195 | Most removed — good |
| EOD+ | 2,250 | Profitable EOD trades lost |
| EOD- | 1,403 | |
| W | 1,602 | |
| **Total** | **9,450** | |

v1 removes more L than W (4,195 vs 1,602) directionally good, but also removes 2,250 EOD+ trades — net PF slightly worse.

---

## VWAP Context Analysis — v1 Trades

| Context | N | % of all | PF | Pure WR |
|---|---|---|---|---|
| Touch BELOW VWAP | 19,115 | 48.3% | 0.859 | 13.2% |
| Touch ABOVE VWAP | 20,474 | 51.7% | 0.949 | 15.8% |
| All | 39,589 | — | 0.908 | — |

VWAP split is meaningful (0.090 PF gap) but neither group crosses 1.0 alone.

---

## TV Validation — HDFCBANK (2025-05-26 to 2025-12-30)

| | Python v1 | TV v1 |
|---|---|---|
| Trades | 208 | 209 |
| Net PnL (raw) | -36.70 | -231.94 (after 0.05% commission) |
| Net PnL (Python + commission) | -241.72 | -231.94 |
| Gap | ~10 INR | ≈ 0.05 INR/trade — data feed rounding |
| WR (raw) | 42.3% | 34.0% (commission flips small wins) |

1-trade difference = MA20 boundary case (TV live feed vs pre-computed CSV). Logic confirmed matching.
