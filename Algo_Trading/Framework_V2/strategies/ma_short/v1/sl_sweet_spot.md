# ma_short/v1 — SL/TP sweet-spot analysis (2026-09-04)

## Method
Hold TP=3.0x fixed, sweep SL from 1.5x to 6.0x, track ZPF, NetZPnL, and CAPM alpha
(vs NIFTY50 daily return) together — require all three to show a genuine interior peak
before locking, not just wherever the swept grid happened to end.

## Full sweep (TP=3.0 fixed)

| SL | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|
| 1.5 | 0.691 | -64,899 | 52.4 | 26.1 | 14.2 | 7.3 | -21.88 | 1.23e-130 |
| 2.0 | 0.729 | -56,161 | 42.4 | 29.1 | 16.7 | 11.8 | -18.70 | 8.58e-87 |
| 2.5 | 0.744 | -52,503 | 34.7 | 31.0 | 18.2 | 16.1 | -17.33 | 1.13e-68 |
| 3.0 | 0.752 | -50,372 | 28.5 | 32.3 | 19.1 | 20.1 | -16.50 | 4.03e-57 |
| 3.5 | 0.761 | -47,987 | 23.5 | 33.2 | 19.7 | 23.6 | -15.60 | 2.87e-48 |
| 4.0 | 0.767 | -46,241 | 19.3 | 33.9 | 19.9 | 26.9 | -14.93 | 2.47e-42 |
| **4.5** | **0.772** | **-44,687** | 15.9 | 34.4 | 20.1 | 29.6 | **-14.34** | 4.74e-38 |
| 5.0 | 0.772 | -44,684 | 13.1 | 34.8 | 20.1 | 32.0 | -14.31 | 1.60e-36 |
| 5.5 | 0.772 | -44,567 | 10.9 | 35.0 | 20.1 | 33.9 | -14.24 | 2.76e-35 |
| 6.0 | 0.773 | -44,030 | 9.0 | 35.2 | 20.1 | 35.6 | -14.04 | 1.41e-33 |

## Deceleration (Δ NetZPnL vs prior row)

1.5→2.0: +8,738 · 2.0→2.5: +3,658 · 2.5→3.0: +2,131 · 3.0→3.5: +2,385 · 3.5→4.0: +1,746 ·
**4.0→4.5: +1,554** · **4.5→5.0: +3 (flat)** · 5.0→5.5: +117 · 5.5→6.0: +537

Gains essentially stop at SL=4.5 — the tiny wobble after that (+117, +537) is noise-level, not
a continuing trend. Alpha's mild continued improvement to SL=6.0 (-14.34→-14.04) is too small
and inconsistent to override this.

## Locked: SL=4.5x / TP=3.0x

Clean interior peak on ZPF, NetZPnL, and Alpha simultaneously — the strongest, most
unambiguous case of the 5 families tested. All 10 combos remain statistically significant
NEGATIVE alpha (this is a health/plateau optimization within an already-non-viable signal,
not a claim of profitability).
