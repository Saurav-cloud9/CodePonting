# Liquidity Sweep — Full Findings (4-Variant Matrix)

*Completed 2026-09-07/08. All 4 variants tested, ruled out. Concept dead as a standalone
signal — see recommendation at the bottom.*

## Background

Two independent axes generate 4 variants, exactly mirroring the flagship ma_short/
ma_long family's own touch/flip structure (confirmed parallel, see below):

|             | Swing LOW trigger | Swing HIGH trigger |
|---|---|---|
| **LONG entry**  | V0 (intuitive) | V3 (contrarian) |
| **SHORT entry** | V1 (contrarian) | V2 (intuitive / "true mirror") |

Signal conditions 1-4 (swing point, distance ≤50 bars, sweep, confirmation) are
identical within each row/column pairing per `02_concepts_summary.md` §1 — only the
swing extreme (low/high) and entry direction (long/short) change. Cutoffs:
`LAST_SWEEP_TIME=14:40`, `ENTRY_CUTOFF_TIME=14:50` (universal, per `backtesting_rules.md`
§2's sharpened formula — 2-bar signal-to-entry chain, one bar longer than the flagship's).

## Table 1 — Raw 90-combo sweep, best ZPF per variant

| Variant | Best SL/TP | Raw ZPF | EOD% | Verdict |
|---|---|---|---|---|
| V0 (swing low + LONG) | 6.0/6.0 | 0.661 | 79.1% | Decisively dead |
| V1 (swing low + SHORT) | 4.5/5.5 | 0.823 | 69.7% | Closest to soft-triage line |
| V2 (swing high + SHORT) | 5.0/6.0 | 0.798 | 74.4% | Below V1 |
| V3 (swing high + LONG) | 6.0/6.0 | 0.691 | 78.9% | Weak (but not the weakest — see below) |

Cross-check: the recovered claude.ai session's own "LSS" (a contrarian short on the
swing-low setup, same as our V1) scored ZPF=0.808 — closely matches our fresh V1
(0.823), validating the engine. Their own "LSS Long" (= our V0) was also found dead.

## Table 2 — Healthy subset (EOD% ≤ 30), best ZPF per variant

| Variant | Best SL/TP | Healthy ZPF | N |
|---|---|---|---|
| V0 | 2.5/2.5 | 0.596 | 99,228 |
| V1 | 2.0/3.0 | 0.745 | 98,790 |
| V2 | 2.0/3.0 | 0.729 | 98,832 |
| V3 | 1.5/5.0 | 0.630 | 95,953 |

## Soft-triage gate (ZPF < 0.75 → skip Table 3, per backtesting_rules.md §12, lowered
## from 0.85 this same session after finding it would have wrongly killed 3 of the 6
## currently-locked flagship variants)

- V0 (0.661) and V3 (0.691) — **excluded**, well below 0.75.
- V1 (0.823) and V2 (0.798) — **qualify**, proceed to full rigor.

## Flagship-family parallel (predicted before running V2/V3, then checked against results)

| ma_short/ma_long | Liquidity | Predicted | Actual |
|---|---|---|---|
| ma_bounce (intuitive LONG, bullish touch) | V0 | weak | 0.661 — weakest overall |
| ma_long_flip (contrarian SHORT, bullish touch) — **locked** | V1 | **strongest** | **0.823 — strongest, confirmed** |
| ma_short (intuitive SHORT, bearish touch) — flagship's own direction | V2 | decent | 0.798 — second |
| ma_short_flip (contrarian LONG, bearish touch) — **ruled out**, worst of 4 | V3 | **weakest** | 0.691 — second-weakest (V0 edges it out) |

The core prediction (V1 strongest) held exactly. The "V3 weakest" prediction was close
but not exact — V0 turned out marginally weaker (0.661 vs 0.691). Noted honestly rather
than forced to fit.

## Table 3 — SL-sweep at fixed TP=3.0 (both V1 and V2 share the same healthy-subset
## best TP, so both use the same reference point), tracking ZPF + NetZPnL + Alpha

### V1 (swing low + SHORT)

| SL | N | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|---|
| 1.5 | 104,685 | 0.714 | -50,571 | 51.8 | 26.2 | 15.1 | 6.9 | -17.069 | 5.1e-99 |
| 2.0 | 98,790 | 0.745 | -45,889 | 42.1 | 29.1 | 17.5 | 11.3 | -15.288 | 1.6e-68 |
| 2.5 | 94,756 | 0.756 | -44,363 | 34.5 | 31.0 | 19.0 | 15.5 | -14.638 | 1.0e-55 |
| 3.0 | 91,685 | 0.769 | -41,687 | 28.2 | 32.3 | 19.9 | 19.5 | -13.616 | 1.5e-45 |
| 3.5 | 89,480 | 0.772 | -41,014 | 23.2 | 33.1 | 20.4 | 23.3 | -13.320 | 1.6e-40 |
| 4.0 | 87,763 | 0.780 | -39,108 | 18.9 | 33.8 | 20.7 | 26.6 | -12.593 | 6.9e-35 |
| **4.5** | **86,463** | **0.784** | **-38,222** | 15.5 | 34.2 | 20.9 | 29.4 | **-12.244** | 4.8e-32 |
| 5.0 | 85,568 | 0.783 | -38,379 | 12.8 | 34.5 | 21.0 | 31.7 | -12.289 | 3.5e-31 |
| 5.5 | 84,857 | 0.781 | -38,643 | 10.6 | 34.7 | 21.0 | 33.7 | -12.361 | 1.3e-30 |
| 6.0 | 84,288 | 0.781 | -38,419 | 8.7 | 34.8 | 21.1 | 35.4 | -12.265 | 1.2e-29 |

**Genuine interior peak at SL=4.5** — both ZPF and NetZPnL peak there simultaneously,
not at the edge of the grid. **Locked combo: SL=4.5/TP=3.0.**

### V2 (swing high + SHORT)

| SL | N | ZPF | NetZPnL | SL% | TP% | EOD+% | EOD-% | Alpha (₹/day) | p-value |
|---|---|---|---|---|---|---|---|---|---|
| 1.5 | 107,153 | 0.699 | -56,104 | 52.8 | 25.6 | 14.6 | 6.9 | -18.911 | 7.9e-107 |
| 2.0 | 98,832 | 0.729 | -50,513 | 43.2 | 28.6 | 17.1 | 11.1 | -16.835 | 5.8e-76 |
| 2.5 | 93,223 | 0.749 | -46,363 | 35.3 | 30.7 | 18.6 | 15.4 | -15.283 | 1.9e-58 |
| 3.0 | 89,573 | 0.753 | -45,274 | 29.1 | 31.9 | 19.5 | 19.5 | -14.823 | 9.9e-51 |
| 3.5 | 86,916 | 0.756 | -44,599 | 24.1 | 32.9 | 20.1 | 23.0 | -14.528 | 6.6e-46 |
| 4.0 | 84,845 | 0.761 | -43,027 | 19.8 | 33.5 | 20.4 | 26.4 | -13.923 | 1.7e-40 |
| 4.5 | 83,324 | 0.762 | -42,539 | 16.3 | 33.9 | 20.6 | 29.3 | -13.712 | 7.3e-38 |
| **5.0** | **82,162** | **0.764** | **-41,933** | 13.4 | 34.2 | 20.6 | 31.8 | **-13.454** | 1.2e-35 |
| 5.5 | 81,333 | 0.763 | -41,866 | 11.0 | 34.5 | 20.7 | 33.8 | -13.406 | 1.7e-34 |
| 6.0 | 80,676 | 0.762 | -42,004 | 9.1 | 34.7 | 20.7 | 35.5 | -13.427 | 1.6e-33 |

**Genuine interior peak at SL=5.0** (ZPF peaks exactly here; NetZPnL near-flat 5.0-5.5,
essentially tied). **Locked combo: SL=5.0/TP=3.0.**

## Full CAPM row (both market factors) for the 2 qualifying variants' locked combos

| source | sl_tp | n_trades | zpf | alpha_capm (NIFTY) | p | ci_low/ci_high (NIFTY) | alpha_capm (basket) | ci_low/ci_high (basket) |
|---|---|---|---|---|---|---|---|---|
| LIQUIDITY_V1_SWINGLOW_SHORT | 4.5x3.0 | 86,463 | 0.784 | -12.244 | <0.001 | (-14.257, -10.231) | -12.397 | (-14.551, -10.243) |
| LIQUIDITY_V2_SWINGHIGH_SHORT | 5.0x3.0 | 82,162 | 0.764 | -13.454 | <0.001 | (-15.542, -11.366) | -13.658 | (-15.945, -11.372) |

**Both confidently, decisively NOT zero — and confidently negative.** p-values in the
e-32 to e-107 range across every single SL value tested (not just the locked combo) —
this isn't noise or a borderline case. Confidence intervals sit entirely below -9 in
every case, nowhere near zero. Cross-validated against both NIFTY and the 30-stock
basket independently — same conclusion both ways (alpha differs by <2% between factors).

V0 and V3 logged to `nifty.csv`/`basket.csv` with `RULED_OUT` in place of the alpha
columns (excluded by the soft-triage gate before the CAPM step — consistent with not
wasting compute on decisively-dead combos, per `backtesting_rules.md` §12).

## Recommendation

**Liquidity Sweep is dead as a standalone signal, in all 4 structural configurations.**
Not "insufficient edge" — the two variants that even reached the alpha-testing stage
show a real, statistically overwhelming NEGATIVE edge (near-zero p-values, CIs entirely
clear of zero). This matches the pattern already found for the flagship signal family
(ma_short/6bce) back in the strategies/ work — negative alpha, not just absence of edge.

Per the plan's own "Key Principles" (`02_concepts_summary.md`): individual SMC concepts
were expected to give "mediocre results," with the real edge hypothesized to concentrate
in **triple confluence** (Liquidity + FVG + OB all lining up in the same zone). This
result doesn't rule confluence out — but it does mean confluence would need to overcome
Liquidity's own standalone negative contribution, not just add to a neutral base.

Next per `01_plan.md`'s ordering: **FVG (index 05)**, following the same 4-variant
matrix discipline established here.
