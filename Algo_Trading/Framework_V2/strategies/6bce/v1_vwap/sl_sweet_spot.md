# 6bce/v1_vwap — SL/TP sweet-spot analysis (2026-09-04)

## Method
Same as `ma_short/v1/sl_sweet_spot.md` — hold TP=3.0x fixed, sweep SL 1.5x-6.0x, require
ZPF, NetZPnL, and CAPM alpha (vs NIFTY50) to all show a genuine interior peak.

## Full sweep (TP=3.0 fixed)

| SL | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|
| 1.5 | 0.756 | -41,600 | 50.3 | 26.9 | 15.5 | 7.3 | -13.89 | 8.37e-71 |
| 2.0 | 0.792 | -35,423 | 40.6 | 30.1 | 17.7 | 11.5 | -11.61 | 1.59e-43 |
| 2.5 | 0.813 | -31,704 | 33.0 | 32.1 | 19.0 | 15.9 | -10.20 | 9.92e-30 |
| 3.0 | 0.820 | -30,544 | 26.9 | 33.4 | 19.8 | 19.9 | -9.71 | 7.95e-25 |
| 3.5 | 0.826 | -29,504 | 22.0 | 34.2 | 20.3 | 23.5 | -9.27 | 3.11e-21 |
| 4.0 | 0.827 | -29,274 | 18.0 | 34.7 | 20.6 | 26.7 | -9.12 | 1.30e-19 |
| **4.5** | **0.828** | -29,294 | 14.7 | 35.1 | 20.7 | 29.5 | **-9.09** | 2.03e-18 |
| 5.0 | 0.825 | -29,847 | 12.1 | 35.3 | 20.9 | 31.7 | -9.25 | 3.81e-18 |
| 5.5 | 0.826 | -29,729 | 9.9 | 35.5 | 20.9 | 33.7 | -9.17 | 3.24e-17 |
| 6.0 | 0.824 | -30,118 | 8.2 | 35.6 | 20.9 | 35.3 | -9.28 | 3.63e-17 |

Note: NetZPnL's actual minimum-loss point is SL=4.0 (-29,274), very slightly ahead of ZPF's
nominal peak (SL=4.5, 0.828) — both sit within the same tight plateau (4.0-4.5), treated as
effectively the same point.

## Locked: SL=4.5x / TP=3.0x

Alpha peaks exactly here (-9.09) then gets slightly worse past it (-9.25, -9.17, -9.28) —
all three metrics agree cleanly, unlike `ma_short/v1` where alpha kept drifting to the grid
edge. Best-behaved plateau of the three "clean" families.
