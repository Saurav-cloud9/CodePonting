# Session Log — 2026-05-09

## What was done
- /resume vs CCP protocol clarified
- export_h5_signals.py built: raw MA20 bounce detection, all 12 params, SL/target exit sim
- p04 swing high logic fixed: window = T0-1 back to prior touch, highest high = swing high
- bounce_bar_index + entry_bar_index added to signals CSV (artifact needs exact bar positions)
- export_h5_candles.py built: candle windows per signal, T0-10 to exit+3, bar_index relative to T0
- CSV encoding fixed: UTF-8, LF line endings, no BOM
- H5 Lite built on claude.ai: 3-panel UI, 12 param sliders/toggles, H1 Baseline + Filter modes
- SVG candlestick chart wired with T0/BNC/ENT markers, MA20, SL, TGT lines
- Real POWERGRID 2022 signals loaded and rendering in artifact

## Key decisions
- p04 window = T0-1 back to first bar where low <= MA20 (prior touch stops the walk)
- bounce_bar_index = bounce_bar - T0 (0=same candle, 1/2/3=bars after T0)
- entry_bar_index = bounce_bar_index + 1 always
- Candle window: T0-10 to exit+3 (~20 bars per signal)
- H5 Lite defaults = most permissive (H1 baseline state)

## Status at SS
- H5 Lite signal tuning loop validated end-to-end
- Both CSVs ready: signals (100 rows) + candles (~1985 rows)
- Next: continue H5 Lite chart refinement on claude.ai
