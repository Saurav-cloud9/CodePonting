import yfinance as yf
import pandas as pd

# Stock symbols
stocks = {
    'SUZLON': 'SUZLON.NS',
    'PNB': 'PNB.NS',
    'TATASTEEL': 'TATASTEEL.NS',
    'IDEA': 'IDEA.NS',
    'YESBANK': 'YESBANK.NS'
}

print("Downloading daily data from Yahoo Finance...")

for name, symbol in stocks.items():
    print(f"\n{name}...")

    # Download daily data (1 year)
    df = yf.download(symbol, start='2024-01-01', end='2026-01-08', progress=False)

    # Calculate MAs
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA100'] = df['Close'].rolling(100).mean()
    df['MA200'] = df['Close'].rolling(200).mean()

    # Save
    output = f'{name}_daily_with_MAs.csv'
    df.to_csv(output)

    print(f"✓ Saved: {output}")
    print(f"  Rows: {len(df)}, MA200 valid from row: {df['MA200'].notna().idxmax()}")

print("\n✓ All done! Now merge these with your 5-min data.")