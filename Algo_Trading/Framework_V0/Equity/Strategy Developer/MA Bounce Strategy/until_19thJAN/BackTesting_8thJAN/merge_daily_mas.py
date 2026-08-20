"""
Merge Yahoo Finance daily MAs with 5-min intraday data
Creates final backtest-ready CSVs
"""

import pandas as pd
from datetime import datetime

STOCKS = ['SUZLON', 'PNB', 'TATASTEEL', 'IDEA', 'YESBANK']

def merge_daily_mas(stock_name):
    """Merge daily MAs with 5-min data"""
    
    print(f"\n{'='*60}")
    print(f"Processing {stock_name}")
    print('='*60)
    
    # Load 5-min data
    intraday_file = f'./{stock_name}_2025_processed.csv'
    try:
        df_5min = pd.read_csv(intraday_file)
    except FileNotFoundError:
        print(f"✗ 5-min file not found: {intraday_file}")
        return None
    
    print(f"✓ Loaded 5-min data: {len(df_5min)} candles")
    
    # Load Yahoo daily data
    daily_file = f'./{stock_name}_daily_with_MAs.csv'
    try:
        df_daily = pd.read_csv(daily_file, header=0, skiprows=[1, 2])
    except FileNotFoundError:
        print(f"✗ Daily file not found: {daily_file}")
        return None
    
    # Clean daily data
    df_daily = df_daily.rename(columns={'Price': 'Date'})
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['date_str'] = df_daily['Date'].dt.strftime('%Y-%m-%d')
    
    # Keep only needed columns
    df_daily = df_daily[['date_str', 'MA50', 'MA100', 'MA200']].copy()
    
    # Convert to numeric (handle any string values)
    for col in ['MA50', 'MA100', 'MA200']:
        df_daily[col] = pd.to_numeric(df_daily[col], errors='coerce')
    
    print(f"✓ Loaded daily MAs: {len(df_daily)} days")
    print(f"  MA50 valid from: {df_daily['MA50'].notna().sum()} days")
    print(f"  MA100 valid from: {df_daily['MA100'].notna().sum()} days")
    print(f"  MA200 valid from: {df_daily['MA200'].notna().sum()} days")
    
    # Merge
    df_5min['date_str'] = df_5min['date'].astype(str)
    df_merged = df_5min.merge(
        df_daily[['date_str', 'MA50', 'MA100', 'MA200']], 
        on='date_str', 
        how='left',
        suffixes=('_old', '')
    )
    
    # Drop old MA columns if they exist
    cols_to_drop = [col for col in df_merged.columns if col.endswith('_old')]
    if cols_to_drop:
        df_merged = df_merged.drop(columns=cols_to_drop)
    
    # Save
    output_file = f'./{stock_name}_2025_FINAL.csv'
    df_merged.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {output_file}")
    print(f"  Total candles: {len(df_merged)}")
    print(f"  Date range: {df_merged['date_str'].min()} to {df_merged['date_str'].max()}")
    
    # Check merge quality
    ma_count = df_merged[['MA50', 'MA100', 'MA200']].notna().all(axis=1).sum()
    print(f"  Rows with ALL MAs: {ma_count}/{len(df_merged)} ({ma_count/len(df_merged)*100:.1f}%)")
    
    return df_merged

# Process all stocks
print("\n╔═══════════════════════════════════════════════════════════════╗")
print("║   MERGING YAHOO DAILY MAs WITH 5-MIN INTRADAY DATA          ║")
print("╚═══════════════════════════════════════════════════════════════╝")

results = {}
for stock in STOCKS:
    df = merge_daily_mas(stock)
    if df is not None:
        results[stock] = df

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for stock, df in results.items():
    ma_valid = df[['MA50', 'MA100', 'MA200']].notna().all(axis=1).sum()
    print(f"{stock}: {len(df)} candles, {ma_valid} with complete MAs")

print("\n✓ All files ready!")
print("✓ Files: *_2025_FINAL.csv")
print("\nNext: Update backtest script to use *_2025_FINAL.csv files!")
