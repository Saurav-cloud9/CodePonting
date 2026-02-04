"""
DATA DOWNLOAD SCRIPT

Responsibility:
- One-time historical data fetch from Upstox API.
- Store raw OHLCV data as Parquet files.

Usage:
    python download_data.py --start 2015-01-01 --end 2025-12-31
# 10 years = includes major bull/bear cycles ---> check with all AIs and decide
    python download_data.py --start 2010-01-01 --end 2025-12-31
# 15 years = maximum history, includes 2008 aftermath

Output:
    data/historical/{symbol}_{interval}.parquet
"""