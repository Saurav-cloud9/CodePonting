# Session Log — 2026-05-16

## What was done
- Reviewed export_h5_signals.py line by line — understood all params p01-p12, PnL sim, for-else pattern
- Fixed SL/TGT multipliers in export_h5_signals.py (were 1.0/1.5, corrected to 2.5/4.5)
- Reviewed export_h5_candles.py partially — shift(1), ATR, signal loading understood
- Created Framework_V2/Notebooks/ folder + explore.ipynb for interactive pandas exploration
- Tested H5 Lite with updated CSVs: 12/100 passing, WR 66.7%, PF 4.17
- Codedex: higher-order functions, map/filter/reduce, list comprehensions, classes, unittest basics

## Status at SS
- export_h5_candles.py candle window loop not yet reviewed
- H5 Lite validation is next (P1), then H5 full build (P2)
