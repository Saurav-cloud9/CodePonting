# Handoff Note — 2026-05-21

## State
- export_h5_signals.py reviewed end to end — SL/TGT multipliers corrected (2.5/4.5 ATR)
- export_h5_candles.py fully reviewed — all sections complete, logic clean
- Notebooks folder created: Framework_V2/Notebooks/explore.ipynb

## Next
1. Validate H5 Lite logic is sound (P1) — chart refinement: T0/BNC/ENT labels, MA20/SL/TGT
2. Regenerate powergrid_2022_h5_signals.csv (multiplier fix changes PnL/outcomes)
3. Build H5 full (P2) — 30 stocks × 4 years

## Known Issues
- 12 passing signals is too small to draw conclusions — need full dataset
- PnL multipliers in signals CSV were wrong (1.0/1.5), now fixed to 2.5/4.5 — regenerate CSV before H5 full build
