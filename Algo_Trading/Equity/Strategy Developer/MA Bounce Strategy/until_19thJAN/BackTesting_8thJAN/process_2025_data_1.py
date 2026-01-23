"""
Process 2025 XLSX data for MA Bounce backtest
- Convert XLSX to CSV
- Parse datetime
- Clean volume
- Calculate MA20 (5-min), MA50/100/200 (daily)
- Skip incomplete days
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

STOCKS = ['SUZLON', 'PNB', 'TATASTEEL', 'IDEA', 'YESBANK']

def clean_volume(vol_str):
    """Convert '148.605 K' or '1.459 M' to numeric"""
    if pd.isna(vol_str):
        return 0
    
    vol_str = str(vol_str).strip()
    
    if 'M' in vol_str:
        return float(vol_str.replace('M', '').strip()) * 1_000_000
    elif 'K' in vol_str:
        return float(vol_str.replace('K', '').strip()) * 1_000
    else:
        return float(vol_str)

def process_stock(stock_name):
    """Process single stock data"""
    
    print(f"\n{'='*60}")
    print(f"Processing {stock_name}")
    print('='*60)
    
    # Find the file
    import glob
    pattern = f'C:/Users/Saurav/CodePonting/pythonProject/Algo Trading/Equity/Strategy Developer/MA Bounce Strategy/BackTesting_8thJAN/{stock_name}-OHLC-5min-Data-*.xlsx'
    files = glob.glob(pattern)
    
    if not files:
        print(f"✗ File not found for {stock_name}")
        return None
    
    filepath = files[0]
    print(f"✓ Loading {filepath}")
    
    # Load XLSX
    df = pd.read_excel(filepath)
    
    # Parse datetime
    df['datetime'] = pd.to_datetime(df['time'], format='%d %b %y %I:%M %p')
    
    # Clean volume
    df['volume'] = df['Volume'].apply(clean_volume)
    
    # Standardize columns
    df = df.rename(columns={
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close'
    })
    
    # Sort chronologically
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Add date column
    df['date'] = df['datetime'].dt.date
    
    # Remove incomplete days (today Jan 8)
    last_complete_date = df['date'].max() - timedelta(days=1)
    df = df[df['date'] <= last_complete_date]
    
    print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"✓ Total candles: {len(df)}")
    
    # Calculate MA20 (5-min)
    df['MA20'] = df['close'].rolling(20).mean()
    
    # Calculate daily MAs
    # Group by date and get EOD close
    daily_closes = df.groupby('date')['close'].last().reset_index()
    daily_closes['MA50'] = daily_closes['close'].rolling(50).mean()
    daily_closes['MA100'] = daily_closes['close'].rolling(100).mean()
    daily_closes['MA200'] = daily_closes['close'].rolling(200).mean()
    
    # Merge daily MAs back to 5-min data
    df = df.merge(daily_closes[['date', 'MA50', 'MA100', 'MA200']], on='date', how='left')
    
    print(f"✓ MA20 calculated ({df['MA20'].notna().sum()}/{len(df)} valid)")
    print(f"✓ Daily MAs calculated")
    
    # Save as CSV
    output_file = f'./{stock_name}_2025_processed.csv'
    df[['datetime', 'date', 'open', 'high', 'low', 'close', 'volume', 'MA20', 'MA50', 'MA100', 'MA200']].to_csv(output_file, index=False)
    print(f"✓ Saved to {output_file}")
    
    return df

# Process all stocks
print("\n" + "="*60)
print("PROCESSING 2025 DATA - ALL STOCKS")
print("="*60)

results = {}
for stock in STOCKS:
    df = process_stock(stock)
    if df is not None:
        results[stock] = df

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for stock, df in results.items():
    days = df['date'].nunique()
    print(f"{stock}: {len(df)} candles, {days} days")

print("\n✓ All files ready for backtest!")
print("Run: python3 ma_bounce_2025_backtest.py")
