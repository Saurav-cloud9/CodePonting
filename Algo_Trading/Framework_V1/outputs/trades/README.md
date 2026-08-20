# Trade Logs

## Purpose:
Detailed record of every trade executed.

## Schema:
- trade_id, datetime, symbol, side
- entry_price, exit_price, pnl, pnl_pct
- reason (Target/SL/EOD)
- candles_held, entry_atr

## Format:
- CSV or Parquet
- One file per backtest run or trading session

## Naming:
- `trades_{run_id}_{timestamp}.parquet`
```

**outputs/trades/.gitkeep**
```
# Placeholder