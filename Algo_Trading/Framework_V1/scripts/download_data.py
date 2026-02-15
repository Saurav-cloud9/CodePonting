# download_data.py
"""
Historical Data Download Script for Framework_V1
=================================================
Downloads 11 years (2015-2025) of historical data from Upstox API
Saves as parquet files for offline backtesting

Data Downloaded:
- NIFTY50 index + 30 F&O stocks
- 5-min intraday candles (for MA20 bounce detection)
- Daily candles (for MA50/100/200 regime filters)

Output Structure:
  data/historical/
    ├── intraday_5min/
    │   ├── NIFTY50.parquet
    │   └── [30 stocks].parquet
    └── daily/
        ├── NIFTY50.parquet
        └── [30 stocks].parquet
"""

import os
import upstox_client
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
import calendar

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# REPLACE WITH YOUR VALID TOKEN
ACCESS_TOKEN = "YOUR_UPSTOX_ACCESS_TOKEN_HERE"

# Instruments to download
INSTRUMENTS = {
    'NIFTY50': 'NSE_INDEX|Nifty 50',
    'TATASTEEL': 'NSE_EQ|INE081A01020',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'NATIONALUM': 'NSE_EQ|INE139A01034',
    'SBIN': 'NSE_EQ|INE062A01020',
    'HDFCBANK': 'NSE_EQ|INE040A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021',
    'AXISBANK': 'NSE_EQ|INE238A01034',
    'PNB': 'NSE_EQ|INE160A01022',
    'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'INFY': 'NSE_EQ|INE009A01021',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'TECHM': 'NSE_EQ|INE669C01036',
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029',
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DIVISLAB': 'NSE_EQ|INE361B01024',
    'CIPLA': 'NSE_EQ|INE059A01026',
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'ONGC': 'NSE_EQ|INE213A01029',
    'COALINDIA': 'NSE_EQ|INE522F01014',
    'ITC': 'NSE_EQ|INE154A01025',
    'DABUR': 'NSE_EQ|INE016A01026',
    'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'VI': 'NSE_EQ|INE669E01016',  # Vodafone Idea (was IDEA)
    'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'VEDL': 'NSE_EQ|INE205A01025',
    'BANDHANBNK': 'NSE_EQ|INE545U01014'
}

# Date range: 2022-2025 (4 years)
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2025, 12, 31)

# Output paths
BASE_DIR = Path("../data/historical")
INTRADAY_DIR = BASE_DIR / "intraday_5min"
DAILY_DIR = BASE_DIR / "daily"

# Create directories if they don't exist
INTRADAY_DIR.mkdir(parents=True, exist_ok=True)
DAILY_DIR.mkdir(parents=True, exist_ok=True)

# API configuration
configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fetch_historical_data(instrument_key, from_date, to_date, interval="5", unit="minutes"):
    """
    Fetch historical data from Upstox API

    Args:
        instrument_key: Upstox instrument identifier
        from_date: Start date
        to_date: End date
        interval: Candle interval (default "5" for 5-min)
        unit: Time unit ("minutes" or "days")

    Returns:
        DataFrame with OHLCV data or None if failed
    """
    try:
        api_instance = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))
        api_response = api_instance.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit=unit,
            interval=interval,
            to_date=to_date.strftime('%Y-%m-%d'),
            from_date=from_date.strftime('%Y-%m-%d')
        )

        if not hasattr(api_response, 'data') or not api_response.data:
            return None

        candles = api_response.data.candles
        if len(candles) == 0:
            return None

        # Create DataFrame
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)

        return df

    except Exception as e:
        print(f"    ❌ Error fetching data: {e}")
        return None


def download_intraday_data(symbol, instrument_key):
    """
    Download 5-min intraday data in monthly chunks (API limit workaround)
    """
    print(f"\n📊 Downloading 5-min data for {symbol}...")

    all_data = []
    current_date = START_DATE

    while current_date < END_DATE:
        # Download one month at a time
        month_end = datetime(current_date.year, current_date.month, calendar.monthrange(current_date.year, current_date.month)[1])
        if month_end > END_DATE:
            month_end = END_DATE

        print(f"  📅 {current_date.strftime('%Y-%m')}...", end=" ")

        df = fetch_historical_data(
            instrument_key=instrument_key,
            from_date=current_date,
            to_date=month_end,
            interval="5",
            unit="minutes"
        )

        if df is not None and len(df) > 0:
            all_data.append(df)
            print(f"✅ {len(df)} candles")
        else:
            print("⚠️  No data")

        current_date = month_end + timedelta(days=1)
        time.sleep(0.5)  # Rate limiting - ~2 req/sec = safe

    # Combine all monthly data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

        # Save as parquet
        output_path = INTRADAY_DIR / f"{symbol}.parquet"
        combined_df.to_parquet(output_path, index=False)
        print(f"  💾 Saved: {output_path} ({len(combined_df)} total candles)")
        return True
    else:
        print(f"  ❌ No data downloaded for {symbol}")
        return False


def download_daily_data(symbol, instrument_key):
    """
    Download daily candles (can fetch entire range in one go)
    """
    print(f"\n📊 Downloading daily data for {symbol}...")

    df = fetch_historical_data(
        instrument_key=instrument_key,
        from_date=START_DATE,
        to_date=END_DATE,
        interval="1",
        unit="days"
    )

    if df is not None and len(df) > 0:
        # Save as parquet
        output_path = DAILY_DIR / f"{symbol}.parquet"
        df.to_parquet(output_path, index=False)
        print(f"  💾 Saved: {output_path} ({len(df)} candles)")
        return True
    else:
        print(f"  ❌ No data downloaded for {symbol}")
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║         Historical Data Download - Framework_V1              ║")
    print("║         Period: 2022-2025 (4 years)                         ║")
    print("║         Instruments: NIFTY50 + 30 F&O Stocks                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    start_time = time.time()

    success_intraday = 0
    success_daily = 0
    failed = []

    for symbol, instrument_key in INSTRUMENTS.items():
        print(f"\n{'=' * 70}")
        print(f"Processing: {symbol}")
        print(f"{'=' * 70}")

        # Download 5-min data
        if download_intraday_data(symbol, instrument_key):
            success_intraday += 1
        else:
            failed.append(f"{symbol} (5-min)")

        time.sleep(1)  # Rate limiting between symbol transitions

        # Download daily data
        if download_daily_data(symbol, instrument_key):
            success_daily += 1
        else:
            failed.append(f"{symbol} (daily)")

        time.sleep(1)  # Rate limiting between symbol transitions

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'=' * 70}")
    print("DOWNLOAD SUMMARY")
    print(f"{'=' * 70}")
    print(f"✅ 5-min data: {success_intraday}/{len(INSTRUMENTS)} instruments")
    print(f"✅ Daily data: {success_daily}/{len(INSTRUMENTS)} instruments")
    print(f"⏱️  Time elapsed: {elapsed / 60:.1f} minutes")

    if failed:
        print(f"\n❌ Failed downloads:")
        for item in failed:
            print(f"   - {item}")
    else:
        print(f"\n🎉 All data downloaded successfully!")

    print(f"\n📁 Data saved to:")
    print(f"   - {INTRADAY_DIR.resolve()}")
    print(f"   - {DAILY_DIR.resolve()}")


if __name__ == "__main__":
    main()