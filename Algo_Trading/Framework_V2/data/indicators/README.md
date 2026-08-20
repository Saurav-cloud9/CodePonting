# Indicator Cache

## Purpose:
Precomputed technical indicators for fast backtesting.

## Structure:
- One Parquet file per symbol
- Includes: MA20, ATR14, MA50, MA100, MA200, regime, etc.

## Naming Convention:
- `{SYMBOL}_indicators.parquet`
- Example: `TATASTEEL_indicators.parquet`

## Generation:
- Run `scripts/compute_indicators.py`
- Automatically syncs with historical data updates

## Columns:
- datetime (index)
- ma20, atr_14, avg_volume
- ma50, ma100, ma200 (daily)
- regime (Bull/Bear/Sideways)
```

**data/indicators/.gitkeep**
```
# Placeholder to track empty directory in git