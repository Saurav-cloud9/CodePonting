import yfinance as yf
import pandas as pd
from datetime import datetime

# Stocks you might want to trade Monday
stocks = ['RELIANCE.NS', 'INFY.NS', 'TCS.NS', '^NSEI']  # Add any others

print("📊 Pulling last 3 months of data...\n")

for stock in stocks:
    data = yf.download(stock, period='3mo', interval='1d')

    # Add moving averages
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()

    # Save to CSV
    filename = f"{stock.replace('.NS', '')}_3months.csv"
    data.to_csv(filename)

    print(f"✅ Saved {filename}")
    print(f"   Latest Close: ₹{data['Close'][-1]:.2f}")
    print(f"   MA20: ₹{data['MA20'][-1]:.2f}, MA50: ₹{data['MA50'][-1]:.2f}\n")

print("🎯 Data ready! Check your PyCharm project folder for CSV files.")