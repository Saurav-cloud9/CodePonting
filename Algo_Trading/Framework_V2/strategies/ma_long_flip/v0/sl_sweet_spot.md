# ma_long_flip/v0 — SL/TP sweet-spot analysis (2026-09-04/05)

## Method
Same as `ma_short/v1/sl_sweet_spot.md` — hold TP=3.0x fixed, sweep SL. Like `6bce/v0`, this
family did not peak within the standard 1.5x-6.0x grid, so it was extended to 10.0x.

## Full sweep (TP=3.0 fixed, SL=1.5 to 10.0)

| SL | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|
| 1.5 | 0.718 | -62,209 | 52.1 | 26.1 | 14.9 | 7.0 | -20.87 | 1.43e-111 |
| 2.0 | 0.746 | -55,090 | 42.8 | 29.0 | 17.2 | 11.0 | -18.26 | 1.01e-76 |
| 2.5 | 0.763 | -50,554 | 35.3 | 31.0 | 18.7 | 15.0 | -16.59 | 2.18e-59 |
| 3.0 | 0.772 | -47,919 | 29.2 | 32.5 | 19.5 | 18.8 | -15.60 | 1.73e-49 |
| 3.5 | 0.777 | -46,245 | 24.3 | 33.5 | 20.0 | 22.2 | -14.96 | 1.37e-43 |
| 4.0 | 0.781 | -44,774 | 20.1 | 34.2 | 20.3 | 25.4 | -14.37 | 6.38e-39 |
| 4.5 | 0.785 | -43,366 | 16.6 | 34.8 | 20.4 | 28.2 | -13.83 | 2.85e-35 |
| 5.0 | 0.788 | -42,247 | 13.9 | 35.2 | 20.5 | 30.4 | -13.41 | 2.05e-32 |
| 5.5 | 0.788 | -42,112 | 11.6 | 35.5 | 20.5 | 32.4 | -13.34 | 2.18e-31 |
| 6.0 | 0.790 | -41,481 | 9.6 | 35.8 | 20.5 | 34.1 | -13.09 | 7.00e-30 |
| 6.5 | 0.790 | -41,199 | 8.0 | 35.9 | 20.5 | 35.6 | -12.99 | 3.42e-29 |
| **7.0** | **0.790** | **-41,083** | 6.7 | 36.1 | 20.5 | 36.7 | **-12.93** | 1.72e-28 |
| 7.5 | 0.789 | -41,302 | 5.7 | 36.2 | 20.5 | 37.7 | -12.99 | 2.34e-28 |
| 8.0 | 0.789 | -41,300 | 4.8 | 36.3 | 20.5 | 38.5 | -12.98 | 3.40e-28 |
| 8.5 | 0.788 | -41,404 | 4.0 | 36.3 | 20.5 | 39.2 | -13.01 | 3.72e-28 |
| 9.0 | 0.788 | -41,301 | 3.4 | 36.4 | 20.4 | 39.7 | -12.97 | 7.81e-28 |
| 9.5 | 0.788 | -41,389 | 2.9 | 36.4 | 20.4 | 40.2 | -13.00 | 9.77e-28 |
| 10.0 | 0.788 | -41,361 | 2.5 | 36.5 | 20.4 | 40.7 | -12.99 | 1.42e-27 |

## Why this family needed extending, and how it differs from 6bce/v0

Same edge-of-grid situation as `6bce/v0` initially — but unlike `6bce/v0` (which only
plateaus, never turns over even out to SL=10.0), this one shows a genuine, cleaner interior
peak: NetZPnL and Alpha both top out exactly at SL=7.0, then actually *decline* past it
(not just flatten) — -41,083 → -41,302 → -41,300 → -41,404... A cleaner signal of true
saturation than 6bce/v0's pattern.

## Locked: SL=7.0x / TP=3.0x

NetZPnL and Alpha both peak here; ZPF is tied for its own peak (0.790, shared with 6.0/6.5).
EOD%=57.2% — similar magnitude of "anomaly" to `6bce/v0`'s locked pick (56-57%), accepted on
the same basis: a genuine saturation point, not an artifact, kept as deliberate variety
across the 5 locked families rather than corrected toward a lower-EOD% alternative.
