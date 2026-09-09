# ma_short/v2_vwap — SL/TP sweet-spot analysis (2026-09-04)

## Method
Same as `ma_short/v1/sl_sweet_spot.md` — hold TP=3.0x fixed, sweep SL 1.5x-6.0x, require
ZPF, NetZPnL, and CAPM alpha (vs NIFTY50) to all show a genuine interior peak.

## Full sweep (TP=3.0 fixed)

| SL | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|
| 1.5 | 0.702 | -44,715 | 52.5 | 26.9 | 13.7 | 7.0 | -15.08 | 7.66e-108 |
| 2.0 | 0.743 | -38,191 | 42.3 | 30.1 | 16.2 | 11.4 | -12.68 | 1.45e-68 |
| 2.5 | 0.760 | -35,801 | 34.6 | 32.0 | 17.7 | 15.7 | -11.77 | 7.09e-53 |
| 3.0 | 0.768 | -34,582 | 28.3 | 33.3 | 18.7 | 19.7 | -11.27 | 7.10e-44 |
| 3.5 | 0.777 | -33,033 | 23.2 | 34.2 | 19.3 | 23.3 | -10.66 | 8.34e-37 |
| 4.0 | 0.780 | -32,601 | 19.1 | 34.7 | 19.6 | 26.6 | -10.46 | 4.23e-33 |
| **4.5** | **0.785** | **-31,732** | 15.6 | 35.2 | 19.8 | 29.4 | **-10.11** | 1.12e-29 |
| 5.0 | 0.783 | -32,211 | 12.9 | 35.5 | 19.9 | 31.7 | -10.24 | 7.92e-29 |
| 5.5 | 0.782 | -32,475 | 10.7 | 35.6 | 20.0 | 33.7 | -10.31 | 2.53e-28 |
| 6.0 | 0.784 | -32,069 | 8.8 | 35.8 | 20.1 | 35.4 | -10.15 | 7.49e-27 |

## Locked: SL=4.5x / TP=3.0x

Clean interior peak on ZPF, NetZPnL, and Alpha simultaneously — same pattern as `v1`. VWAP
filter (below-VWAP, per `vwap_decision.md`) improves the plateau numbers slightly across the
board vs the unfiltered v1 signal, but the plateau location (SL=4.5) is identical.
