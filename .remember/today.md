# Session Log — 2026-05-21

## What was done
- Completed export_h5_candles.py full line-by-line review (candle window loop + output section)
- Confirmed bar_index = idx - T0 is correct (-10 at first pre-touch bar, 0 at T0)
- Confirmed output columns: signal_id, bar_index, datetime, OHLCV, ma20
- Confirmed to_csv params: index=False, utf-8, lineterminator='\n' (no Excel blank rows)
- Clarified pandas .shape attribute (built-in, returns (rows, cols) tuple)

## Status at SS
- Both export scripts fully reviewed and understood
- Signals CSV needs regenerating (multiplier fix from prior session)
- Next: regenerate signals CSV, then H5 Lite validation (P1)
