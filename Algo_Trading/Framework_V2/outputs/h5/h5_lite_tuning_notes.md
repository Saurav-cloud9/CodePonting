# H5 Lite — POWERGRID 2022 Tuning Session
Date: 2026-05-26

## Dataset
- Stock: POWERGRID
- Year: 2022
- Total signals: 100
- SL/TP multipliers: 2.5 / 4.5 ATR
- Entry cutoff: 14:40
- Hard exit: 15:00 (open of 15:00 bar)

## Baseline (no params active)
- WR: 21%
- NET PnL: -41.714

## Key Findings

### Params that worked
- **p05 shoot_depth (0.0–1.60 ATR)** — selects signals with meaningful wick below MA20
- **p08 bounce_vr_abs (≥ 0.5x)** — filters low-conviction bounces, eliminated 6 losers cleanly
- **p11 G3a entry_close_above** — strongest standalone gate, confirms buyer momentum into entry

### Best combo
**p05 (0.0–1.60) + p08 (≥0.5x) + p11 ON**
- Signals: 21
- WR: 61.9%
- PF: 2.43
- NET PnL: +10.261

### Params that underperformed
- **p01/p02 slope** — 5-bar window too short for 5-min MA20. Defer to Optuna in H5 full
- **p04 pullback_bars** — 63% signals have NaN (no valid swing high). Only 37 measurable
- **p10 max_tb_gap** — best at 9 (effectively off). Touch-bounce gap not a quality differentiator

## Structural Insights
- 63% signals have no valid pullback structure — price not approaching from above cleanly
- POWERGRID 2022 had sustained downtrend — regime context limits strategy edge
- Bounce execution quality (p05/p08/p11) matters more than pre-touch regime on this dataset
- Asymmetric payoff (2.5/4.5 ATR) working as designed — few big wins covering many small losses
- EOD+ exits were masking genuine target hits due to exit loop order bug (now fixed in export script)

## Next Step
→ H5 full: 30 stocks × multiple years + Optuna for systematic param search