# Flagship Family — Index Plan

## Purpose
Unify the flagship-family (ma_short / 6bce / ma_long_flip) strategy work under the
same numbered flat-file convention already used in `strategies/smc/`, and keep a
running master comparison log (`master_nifty.csv` / `master_basket.csv`) local to
this folder instead of at the temporary location it started at (`strategies/smc/`).

The original per-family folders (`ma_short/`, `6bce/`, `ma_long_flip/`) remain the
untouched working source-of-truth — nothing there was moved, renamed, or edited.
Everything in this folder is a copy (indices 02-07) or new work (08+).

## Index map

| # | File | Status | Source |
|---|---|---|---|
| 01 | `01_plan.md` | this file | new |
| 02 | `02_ma_short_v1.py` | locked, in monthly recon | copy of `ma_short/v1/sweep_v1.py` |
| 03 | `03_ma_short_v2_vwap.py` | locked, in monthly recon | copy of `ma_short/v2_vwap/sweep_v2_vwap.py` |
| 04 | `04_6bceh_short_v0.py` | locked, in monthly recon | copy of `6bce/v0/sweep_v0.py` |
| 05 | `05_6bceh_short_v1vwap.py` | locked, in monthly recon | copy of `6bce/v1_vwap/sweep_v1_vwap.py` |
| 06 | `06_ma_long_flip_v0.py` | locked, in monthly recon | copy of `ma_long_flip/v0/sweep_v0.py` |
| 07 | `07_ma_long_flip_v1vwap.py` | locked, in monthly recon | copy of `ma_long_flip/v1_vwap/sweep_v1_vwap.py` |
| 08 | `08_6bcel_short.py` | new — priority #1 | SHORT on fresh 6-bar closing LOW (breakdown continuation) |
| 09 | `09_6bceh_long.py` | new — priority #2 | LONG on fresh 6-bar closing HIGH (breakout continuation) |
| 10 | `10_6bcel_long.py` | new — priority #3 | LONG on fresh 6-bar closing LOW (reversal/bounce) |

`ma_short/v0` (a superseded pre-v1 iteration, never locked) is intentionally excluded.

## 6-Bar Close Extreme (6BCE) family — canonical naming (locked 2026-09-09)

Two independent triggers (which extreme of the last 6 closes) × two entry directions
= 4 variants. Only one has ever been tested:

```
6BCEH — 6-Bar Close Extreme HIGH  (close[i] == max(close[i-5..i]))
  → 6BCEH-Short   (reversal from high)      ✅ tested, locked  → #04/#05 here
  → 6BCEH-Long    (breakout continuation)   ❌ untested        → #09

6BCEL — 6-Bar Close Extreme LOW   (close[i] == min(close[i-5..i]))
  → 6BCEL-Long    (reversal/bounce from low)    ❌ untested    → #10
  → 6BCEL-Short   (breakdown continuation)      ❌ untested    → #08
```

The originally-tested variant was labeled `6bce_v0`/`6bce_v1vwap`/`FRESH_6BCE_V0` etc.
throughout earlier work (its own `strategies/6bce/` folder keeps that name, untouched).
Going forward, all new comparison rows and this folder's copies use `6BCEH_SHORT` to
avoid ambiguity now that the LOW-based sibling family exists.

## Testing order (priority ranking, per claude.ai review 2026-09-08)
1. `6BCEL-Short` — aligns with this project's repeatedly-confirmed structural short
   bias; a genuine (not contrarian) momentum-continuation short, unlike 6BCEH-Short.
2. `6BCEH-Long` — also a genuine continuation bet (buying into a fresh high),
   plausible for the same reason.
3. `6BCEL-Long` — pure reversal/bounce logic; expected to underperform based on every
   other reversal-flavored setup tested this project (Liquidity V0/V3, ma_short_flip).

Each gets: full 90-combo SL/TP sweep (SL 1.5-6.0, TP 2.0-6.0, same grid as the rest of
the flagship family), NaN-entry guard from the start (per `backtesting_rules.md` §15),
exit-mix diagnostic (SL%/TP%/EOD%), then a CAPM alpha row (both NIFTY- and basket-
regressed) appended to `master_nifty.csv` / `master_basket.csv` in this folder. **Not
every variant gets the deeper Table 3 (SL-sweep interior-peak confirmation) pass** —
see `backtesting_rules.md` §12's Screening Tiers: only a raw round good enough to
plausibly survive it earns that treatment, everything else gets the lighter
`RAW_SCREEN` pass (raw-best combo + one alpha computation, enough to rule out, not
enough to lock). Each row's `screen_tier` column in the master files records which
tier it actually got — all 3 of #08/09/10 came back `RAW_SCREEN` (their raw round was
decisively bad enough that Table 3 wasn't warranted).

## Status
2026-09-09: folder created and seeded (01-07). Built and ran 08/09/10 — **all 3 ruled
out**, same decisive-negative-alpha pattern as Liquidity V0-V3:

| # | Variant | ZPF (best, edge-of-grid) | Alpha (₹/day, NIFTY) | 95% CI |
|---|---|---|---|---|
| 08 | 6BCEL-Short | 0.835 @ SL=6.0/TP=6.0 | -12.970 | [-16.60, -9.34] |
| 09 | 6BCEH-Long  | 0.710 @ SL=6.0/TP=6.0 | -33.475 | [-37.00, -29.95] |
| 10 | 6BCEL-Long  | 0.739 @ SL=6.0/TP=6.0 | -29.058 | [-32.71, -25.40] |

All three: 0 NaN-entry trades dropped (guard confirmed working from the start), CI
entirely clear of zero (confidently negative, not just "no edge found"). Notably, the
priority-#1 hypothesis (6BCEL-Short as a genuine short-side continuation bet, expected
to benefit from this project's repeated short-bias finding) did **not** pan out —
still clearly below viability, just the least-bad of the three. Takeaway: the
short-bias finding does not generalize to "any short entry works" — the specific
6BCEH-Short trigger (reversal-from-high) that's actually locked remains the only
member of this 4-variant family that clears the bar. Full rows appended to
`master_nifty.csv` / `master_basket.csv` in this folder, tagged `screen_tier=RAW_SCREEN`.

**Decision (2026-09-09): no Table 3 follow-up on `6BCEL-Short`.** Its `RAW_SCREEN`
ZPF (0.835) already sits marginally below the already-locked `FRESH_6BCEHSHORT_V0`'s
`FULL_RIGOR` ZPF (0.836) — even a best-case Table 3 bump (~0.006, per that same
variant's own grid-extension precedent) wouldn't clear the existing comparison point,
let alone viability. Closing out the 6BCE family here. Back to SMC (FVG, index 05)
next.
