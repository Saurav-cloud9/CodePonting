# MemLabs Model A as a Day-Level Regime Gate on fv2 TATAMOTORS Trades (2026-08-04)

Index notebook: `24_fv2_tatamotors_replication.ipynb`
Scripts: `25_build_long_trade_log.py`, `26_regime_gated_analysis.py`

## Question
Does MemLabs Model A's daily directional signal (`+1`/`-1`, predicted from yesterday's
close-to-close log return) carry real information usable by fv2's actual trading strategies —
not just an abstract `cum_trade_log_return` metric, but real PnL/ZPnL on real trades?

## Method
- **Model A**: fit on the chronological first 75% of TATAMOTORS daily closes (DS3, 2015-2025),
  predicted on the full series. `coef_=-0.00879`, `intercept_=-0.000129`.
  Train: 1998 days (2015-02-04 → 2023-04-12). Test: 667 days (2023-04-13 → 2025-12-31).
- **SHORT trades**: existing live-parity trade log (`ma_rejection_v1_core.py`, SL=2.0x/TP=4.5x)
  — `TATAMOTORS_2015-2025_trade_log_with_memory_feature.csv`, 3697 trades.
- **LONG trades**: newly built (`25_build_long_trade_log.py`, matching `ma_30_bounce_v1.py`'s
  wick-only-touch logic, SL=2.0x/TP=5.5x) — `TATAMOTORS_2015-2025_trade_log_LONG_bounce_v1.csv`,
  3755 trades.
- **Gating rule**: each trade tagged with the calendar day's Model A signal (via `entry_dt`
  normalized to date). On Sell-signal (-1) days, only SHORT trades count. On Buy-signal (+1)
  days, only LONG trades count. This is NOT a new strategy — it's a day-level filter applied to
  the two existing fv2 strategies' real trades.
- **Train/Test reported separately, never blended** — Train-period signal is in-sample (fit on
  that exact data), only Test-period signal is genuinely predictive/out-of-sample. This is the
  same rigor established in notebook 22 for the pure price-return work.

## Results

| Split | Bucket | N | Net PnL | PF | Net ZPnL | ZPF |
|---|---|---|---|---|---|---|
| Train | SHORT baseline (every short trade) | 2815 | 500.60 | 1.274 | -180.51 | 0.918 |
| Train | SHORT gated (Sell-signal days only) | 2131 | 403.65 | 1.306 | -123.75 | 0.923 |
| Train | LONG baseline (every long trade) | 2786 | -225.06 | 0.895 | -901.78 | 0.653 |
| Train | LONG gated (Buy-signal days only) | 643 | -61.22 | 0.883 | -205.76 | 0.667 |
| Train | COMBINED baseline | 5601 | 275.55 | 1.069 | -1082.29 | 0.775 |
| Train | COMBINED gated | 2774 | 342.43 | 1.186 | -329.51 | 0.852 |
| **Test** | SHORT baseline (every short trade) | 880 | 389.90 | 1.435 | -78.50 | 0.932 |
| **Test** | SHORT gated (Sell-signal days only) | 744 | 382.42 | 1.560 | -13.06 | **0.985** |
| **Test** | LONG baseline (every long trade) | 966 | -247.45 | 0.814 | -763.55 | 0.546 |
| **Test** | LONG gated (Buy-signal days only) | 133 | -11.88 | 0.945 | -82.84 | 0.684 |
| **Test** | **COMBINED baseline** (both sides, ungated) | 1846 | 142.46 | 1.064 | -842.05 | **0.703** |
| **Test** | **COMBINED gated** (regime-matched only) | 877 | 370.54 | 1.412 | -95.90 | **0.917** |

## Conclusion

- **On genuinely out-of-sample Test data, gating meaningfully improves the combined strategy**:
  ZPF goes from 0.703 (ungated, both strategies run always) to 0.917 (regime-matched only),
  using less than half the trade count (877 vs 1846). This holds up broken down by side too —
  SHORT-gated ZPF improves from 0.932 to 0.985 (nearly breakeven), LONG-gated improves from
  0.546 to 0.684 (still weak, but meaningfully less bad).
- **Still not net-profitable after full Zerodha costs** (ZPF < 1.0 in every bucket), so this
  isn't a standalone tradeable edge yet — but a genuine, real-money-metric improvement from a
  single, simple daily regime filter is a meaningful signal that Model A carries real
  information, not noise.
- **Train-period numbers are in-sample and not meaningful evidence on their own** (Model A was
  fit on that exact data) — included only for completeness/comparison, not as supporting
  evidence. The Test-period result is the one that matters.
- Single-stock result (TATAMOTORS only) — same caveat as before, needs multi-stock validation
  before drawing broader conclusions about MA-rejection/bounce + regime gating in general.

## Next
- Multi-stock version of this same gating analysis across the DS3 universe.
- Try MA-alone / Model B as the gate instead of Model A, using the same Train/Test rigor.
- If multi-stock holds up, explore whether combining the regime gate with existing signal-
  quality filters narrows the ZPF gap to 1.0 further.
