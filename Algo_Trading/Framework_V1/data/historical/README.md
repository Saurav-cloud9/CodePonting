# Historical Data Storage

## Structure:
- One Parquet file per symbol per timeframe
- Columns: datetime, open, high, low, close, volume, oi

## Naming Convention:
- `{SYMBOL}_{INTERVAL}.parquet`
- Example: `TATASTEEL_5min.parquet`

## Data Source:
- Upstox API (historical candles)
- Downloaded via `scripts/download_data.py`

## Update Frequency:
- Initial download: Full 48 months
- Incremental: Monthly (or as needed)
```

**data/historical/.gitkeep**
```
# Placeholder to track empty directory in git