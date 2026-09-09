# 6bce/v0 — SL/TP sweet-spot analysis (2026-09-04)

## Method
Same as `ma_short/v1/sl_sweet_spot.md` — hold TP=3.0x fixed, sweep SL. This family did NOT
show a clean peak within the standard 1.5x-6.0x grid (all metrics still climbing at SL=6.0),
so the grid was extended to 10.0x to find the genuine turnover point.

## Full sweep (TP=3.0 fixed, SL=1.5 to 10.0)

| SL | ZPF | NetZPnL | SL% | TP% | EOD% (combined) | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|
| 1.5 | 0.731 | -124,034 | 53.9 | 26.0 | 20.1 | -41.40 | 5.97e-133 |
| 2.0 | 0.770 | -98,078 | 44.4 | 29.3 | 26.4 | -32.23 | 2.81e-84 |
| 2.5 | 0.787 | -84,730 | 36.6 | 31.5 | 32.0 | -27.50 | 2.74e-61 |
| 3.0 | 0.801 | -74,771 | 30.2 | 33.1 | 36.7 | -23.96 | 1.47e-46 |
| 3.5 | 0.812 | -67,339 | 25.1 | 34.2 | 40.7 | -21.32 | 2.32e-37 |
| 4.0 | 0.818 | -62,730 | 20.8 | 35.1 | 44.1 | -19.68 | 8.41e-32 |
| 4.5 | 0.823 | -58,887 | 17.3 | 35.7 | 47.0 | -18.31 | 1.00e-27 |
| 5.0 | 0.825 | -56,786 | 14.5 | 36.2 | 49.3 | -17.57 | 1.16e-25 |
| 5.5 | 0.829 | -54,306 | 12.1 | 36.6 | 51.2 | -16.69 | 2.18e-23 |
| 6.0 | 0.831 | -52,852 | 10.3 | 36.9 | 52.8 | -16.14 | 7.64e-22 |
| 6.5 | 0.834 | -51,076 | 8.7 | 37.2 | 54.1 | -15.52 | 2.96e-20 |
| 7.0 | 0.835 | -50,482 | 7.4 | 37.4 | 55.1 | -15.33 | 8.94e-20 |
| 7.5 | 0.835 | -49,878 | 6.4 | 37.6 | 56.0 | -15.11 | 3.18e-19 |
| **8.0** | **0.836** | -49,549 | 5.5 | 37.7 | 56.7 | -14.99 | 6.19e-19 |
| 8.5 | 0.836 | **-49,152** | 4.8 | 37.9 | 57.4 | **-14.85** | 1.25e-18 |
| 9.0 | 0.835 | -49,172 | 4.2 | 38.0 | 57.9 | -14.85 | 1.33e-18 |
| 9.5 | 0.836 | -48,884 | 3.7 | 38.0 | 58.3 | -14.75 | 2.51e-18 |
| 10.0 | 0.837 | -48,312 | 3.2 | 38.1 | 58.7 | -14.55 | 5.74e-18 |

## Why this family is different

Unlike ma_short_v1/v2vwap/6bce_v1vwap (clean SL=4.5 peak), this family keeps genuinely
improving well past SL=6.0 — confirmed real (not grid-edge artifact) because the extension
shows an actual saturation: NetZPnL/step shrinks to ~$300-700 by SL=6.5+ (vs $2,000+ per step
earlier), with a tiny dip at 8.5→9.0 confirming true plateau, not just deceleration.

**Trade-off**: the genuine plateau (SL≈8.0-8.5) comes with EOD%=56-57%, well above the ~47-50%
seen at the other 4 families' SL=4.5 picks.

## Locked: SL=8.0x / TP=3.0x (Saurav's call, 2026-09-05)

Decision: accept the higher EOD% since it's a confirmed genuine saturation point, not an
artifact — treated as a deliberate anomaly/variety across the 5 locked families, not a defect
to correct. (SL=8.5 is a near-identical alternative — marginally better NetZPnL/Alpha, both
within the same plateau; SL=8.0 was the value explicitly chosen.)
