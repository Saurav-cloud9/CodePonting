# Weekly Log — w/c 2026-05-05

## This week
- Signal review phase complete (38 signals, 3 winners: #15 #16 #17)
- Decision: move to H5 build (param tuner) instead of continuing manual review
- fv2_params.md built: all 12 params specced, Opus-reviewed, moved to Framework_V2/docs/
- H5 design decisions locked: Explore/Filter modes, gate independence, N/A rules
- H5 Lite React artifact built on claude.ai — 3-panel UI, real CSV, candlestick chart
- POWERGRID 2022 signal CSVs generated: signals (100) + candles (~1985 rows)
- bounce_bar_index added to signals schema — artifact can now label T0/BNC/ENT correctly

## Key insight this week
- p04 swing high = highest high in window from T0-1 back to prior touch (not arbitrary lookback)
- H5 Lite validates the param tuning loop end-to-end before H5 full build

## Next week
- Complete H5 Lite chart refinement on claude.ai
- H5 full build: Python + HTML, 30 stocks
- Optuna joint sweep (P3) after H5 full validated
