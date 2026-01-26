"""
Test to reproduce the exact error from gss_hyperparameter_search.py
"""

import pandas as pd
import yfinance as yf
from gss_core import calculate_atr, calculate_adx, calculate_rsi, calculate_actual_regime_lookahead

# Replicate the exact flow from gss_hyperparameter_search.py
print("📥 Downloading Nifty data (2015-2026)...")
buffer_start = "2014-01-01"
end_date = "2026-01-10"
nifty = yf.download("^NSEI", start=buffer_start, end=end_date, progress=False)

print(f"✅ Downloaded {len(nifty)} days")

# FIX #2: Explicit multi-index flattening
if isinstance(nifty.columns, pd.MultiIndex):
    print("⚠️ Flattening MultiIndex...")
    nifty.columns = nifty.columns.get_level_values(0)

print(f"📊 Columns after flattening: {nifty.columns.tolist()}")

# Calculate indicators (same as calculate_indicators function)
print("\n🔧 Calculating indicators...")
nifty['MA'] = nifty['Close'].rolling(20).mean()
nifty['MA_5d_ago'] = nifty['MA'].shift(5)
nifty['EMA'] = nifty['Close'].ewm(span=200).mean()
nifty['Volume_MA20'] = nifty['Volume'].rolling(20).mean()

nifty['ADX'], nifty['Plus_DI'], nifty['Minus_DI'] = calculate_adx(nifty, period=14)
nifty['ATR'] = calculate_atr(nifty, period=14)
nifty['RSI'] = calculate_rsi(nifty['Close'], period=14)
nifty['ADX_slope'] = nifty['ADX'].diff().rolling(window=3).mean()

print(f"✅ Indicators calculated")
print(f"📊 Columns now: {nifty.columns.tolist()}")
print(f"\n📊 DataFrame dtypes:\n{nifty.dtypes}")

# Now test calculate_actual_regime_lookahead (the function that fails)
print("\n🎯 Testing calculate_actual_regime_lookahead at index 100...")
try:
    regime = calculate_actual_regime_lookahead(nifty, 100, lookahead=5)
    print(f"✅ SUCCESS! Regime: {regime}")
except Exception as e:
    print(f"❌ ERROR REPRODUCED!")
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

    # Debug the exact issue
    print("\n🔍 DEBUGGING:")
    print(f"nifty.columns type: {type(nifty.columns)}")
    print(f"Is MultiIndex? {isinstance(nifty.columns, pd.MultiIndex)}")
    print(f"Columns: {nifty.columns.tolist()}")

    print(f"\n🔍 Testing iloc access:")
    try:
        row = nifty.iloc[100]
        print(f"✅ Row retrieved: {type(row)}")
        print(f"Row:\n{row}")
    except Exception as e2:
        print(f"❌ iloc failed: {e2}")

    print(f"\n🔍 Testing ATR column access:")
    try:
        atr_val = nifty.iloc[100]['ATR']
        print(f"✅ ATR value: {atr_val}")
    except Exception as e3:
        print(f"❌ ATR access failed: {e3}")
