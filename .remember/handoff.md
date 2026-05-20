# Handoff Note — 2026-05-19

## State
- export_h5_signals.py reviewed end to end — SL/TGT multipliers corrected (2.5/4.5 ATR)
- export_h5_candles.py partially reviewed — shift(1), ATR, signal loading done; candle window loop not yet reviewed
- H5 Lite tested on updated CSVs: 12/100 passing, WR 66.7%, PF 4.17 (small sample, not conclusive)
- Notebooks folder created: Framework_V2/Notebooks/explore.ipynb

## Next
1. Finish export_h5_candles.py review (candle window loop + output section)
2. Validate H5 Lite logic is sound (P1 TODO)
3. Then build H5 full (P2 TODO) — 30 stocks × 4 years

## Known Issues
- 12 passing signals is too small to draw conclusions — need full dataset
- PnL multipliers in signals CSV were wrong (1.0/1.5), now fixed to 2.5/4.5 — regenerate CSV before H5 full build
