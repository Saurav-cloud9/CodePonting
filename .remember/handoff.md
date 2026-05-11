# Handoff Note — 2026-05-09

## State
H5 Lite React artifact built on claude.ai and functional. Both CSVs ready:
- Signals: Algo_Trading/Framework_V2/outputs/h5/powergrid_2022_h5_signals.csv (100 signals, 12 params + bounce_bar_index + entry_bar_index)
- Candles: Algo_Trading/Framework_V2/outputs/h5/powergrid_2022_h5_candles.csv (~1985 rows, T0-10 to exit+3)

## Next
1. Continue H5 Lite chart refinement on claude.ai (T0/BNC/ENT labels, MA20, SL, TGT rendering)
2. After H5 Lite validated → H5 full (Python + HTML, 30 stocks)
3. After H5 full → Optuna joint sweep (P3)

## Context
- bounce_bar_index = bounce_bar - T0 (0=same candle, 1/2/3=bars after)
- entry_bar_index = bounce_bar_index + 1 always
- p04 swing high window: T0-1 back to first bar where low <= MA20 (prior touch stops walk)
- Candle window: T0-10 bars to exit+3
- fv2_params.md: Algo_Trading/Framework_V2/docs/fv2_params.md
- Export scripts: Framework_V2/scripts/export_h5_signals.py + export_h5_candles.py
