# ITC 2022 tb3 — Voltrend Filter Analysis

## Why We Are Here — The Breakeven Problem

The MA Bounce strategy has a fixed R:R structure:
- **Win:** price hits 4.5 ATR target → +4.5 ATR
- **Loss:** price hits 2.5 ATR stop → −2.5 ATR
- **Ratio:** 4.5 ÷ 2.5 = **1.8**

This sets the break-even win rate on decided trades (W + L only, EOD excluded):

> Win% × 1.8 = (1 − Win%) × 1
> → Win% = 1 ÷ 2.8 = **35.7%**

ITC 2022 baseline W/(W+L) = **34.4%** — 1.3 percentage points short.
A filter needs to push this above 35.7% *without* collapsing signal count.

Note: 35.7% is the floor (break-even). The real working target is 38–40% in IS
to have margin left after OOS decay.

---

## What We Tested — Beluga voltrend at Touch Bar

The Big Beluga oscillator computes a volume trend score (voltrend) at each bar.
High voltrend = strong volume momentum (sellers very active).
Low/negative voltrend = volume momentum fading or absent.

**Hypothesis going in:** High voltrend at touch = seller exhaustion = better bounce → higher W%.

**Result:** The opposite. High voltrend at touch is a bad sign — sellers are still
committed at that bar. After the touch, they continue pushing price down.

Low-to-moderate voltrend at touch = selling was gentle or fading → buyers step in
more easily → cleaner bounce → higher W/(W+L).

---

## Results — voltrend_touch Threshold Sweep (ITC 2022 tb3)

| Filter              | N Signals | W   | L   | W/(W+L) | Status           |
|---------------------|-----------|-----|-----|---------|------------------|
| Baseline (no filter)| 1574      | 321 | 611 | 34.4%   | below breakeven  |
| voltrend_touch < 5  | 1225      | 260 | 453 | 36.5%   | above breakeven  |
| **voltrend_touch < 4** | **1178** | **252** | **433** | **36.8%** | **above — peak** |
| voltrend_touch <= 3 | 1117      | 236 | 413 | 36.4%   | above breakeven  |
| voltrend_touch <= 2 | 1060      | 219 | 398 | 35.5%   | below breakeven  |
| voltrend_touch <= 1 | 1006      | 199 | 384 | 34.1%   | below breakeven  |
| voltrend_touch <= 0 |  943      | 187 | 360 | 34.2%   | below breakeven  |

Note: < 4 and <= 4 return identical results (no signal sits exactly at voltrend = 4.0).
Same for < 5 and <= 5.

---

## Key Findings

1. **Best single filter: voltrend_touch < 4** — 36.8% W/(W+L), 1178 signals retained (74.8% of baseline)
2. **Cutting too tight hurts**: below threshold 3, W/(W+L) drops back under breakeven — too many good signals removed along with bad ones
3. **High voltrend kills W%**: signals with voltrend > 5 drop to 27.9% — worse than random
4. **EOD+ still present**: the filtered set retains 313 EOD+ vs 180 EOD- — the EOD cushion is intact

---

## Next Step

Layer `trend_touch` on top of `voltrend_touch < 4` and measure the combined W/(W+L).
If trend_touch < 0 (downtrend at touch) + voltrend_touch < 4 pushes W/(W+L) toward 38–40%,
this combination becomes the candidate G1 filter for OOS validation.
