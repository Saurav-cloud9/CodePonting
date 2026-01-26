"""
🐛 GSS ATR Debugging Script
===========================
Visualizing the ATR calculation error step-by-step
"""

import pandas as pd
import numpy as np
import yfinance as yf
import sys
import traceback

# Import the problematic functions
from gss_core import calculate_atr, calculate_actual_regime_lookahead


def main():
    print("\n" + "="*70)
    print("🐛 GSS ATR DEBUGGING SCRIPT")
    print("="*70)

    # ========================================================================
    # STEP 1: Download Nifty data (small sample for debugging)
    # ========================================================================
    print("\n📥 STEP 1: Downloading Nifty data...")
    nifty = yf.download("^NSEI", start="2024-01-01", end="2025-01-01", progress=False)
    print(f"✅ Downloaded {len(nifty)} days")
    print(f"\n📊 First 3 rows:\n{nifty.head(3)}")

    # ========================================================================
    # STEP 2: Check if DataFrame has MultiIndex columns
    # ========================================================================
    print("\n" + "="*70)
    print("🔍 STEP 2: CHECKING COLUMN STRUCTURE")
    print("="*70)
    print(f"Columns type: {type(nifty.columns)}")
    print(f"Is MultiIndex? {isinstance(nifty.columns, pd.MultiIndex)}")
    print(f"\nColumns: {nifty.columns.tolist()}")
    print(f"\nColumn names: {list(nifty.columns)}")

    # ========================================================================
    # STEP 3: Flatten if MultiIndex (this is what the code should do)
    # ========================================================================
    print("\n" + "="*70)
    print("🔧 STEP 3: FLATTENING MULTIINDEX")
    print("="*70)
    if isinstance(nifty.columns, pd.MultiIndex):
        print("⚠️ MultiIndex detected! Flattening...")
        nifty.columns = nifty.columns.get_level_values(0)
        print("✅ Flattened")
    else:
        print("✅ Already flat (single-level columns)")

    print(f"\nColumns after flattening: {nifty.columns.tolist()}")

    # ========================================================================
    # STEP 4: Calculate ATR and inspect the result
    # ========================================================================
    print("\n" + "="*70)
    print("🔧 STEP 4: CALCULATING ATR")
    print("="*70)
    atr_series = calculate_atr(nifty, period=14)

    print(f"\n📊 ATR RESULT:")
    print(f"Type: {type(atr_series)}")
    print(f"Length: {len(atr_series)}")
    print(f"\nFirst 5 ATR values:\n{atr_series.head()}")
    print(f"\nLast 5 ATR values:\n{atr_series.tail()}")
    print(f"\nNaN count: {atr_series.isna().sum()}")

    # ========================================================================
    # STEP 5: Assign ATR to DataFrame (this is what gss_hyperparameter_search.py does)
    # ========================================================================
    print("\n" + "="*70)
    print("📝 STEP 5: ASSIGNING ATR TO DATAFRAME")
    print("="*70)
    nifty['ATR'] = atr_series

    print("✅ ATR assigned to DataFrame")
    print(f"\n📊 DataFrame columns now: {nifty.columns.tolist()}")
    print(f"\nFirst 20 rows with ATR:\n{nifty[['Close', 'High', 'Low', 'ATR']].head(20)}")

    # ========================================================================
    # STEP 6: Test accessing ATR using iloc (THIS IS WHERE THE ERROR HAPPENS)
    # ========================================================================
    print("\n" + "="*70)
    print("🧪 STEP 6: TESTING ATR ACCESS WITH iloc")
    print("="*70)

    test_idx = 50  # Use index 50 (should have ATR calculated by then)

    print(f"\n1️⃣ Accessing row {test_idx} with iloc:")
    try:
        row = nifty.iloc[test_idx]
        print(f"   Row type: {type(row)}")
        print(f"   Row:\n{row}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    print(f"\n2️⃣ Accessing ATR from row {test_idx}:")
    try:
        atr_val = nifty.iloc[test_idx]['ATR']
        print(f"   ✅ ATR value: {atr_val}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")

    # ========================================================================
    # STEP 7: Check DataFrame index structure
    # ========================================================================
    print("\n" + "="*70)
    print("🔍 STEP 7: CHECKING DATAFRAME INDEX")
    print("="*70)
    print(f"Index type: {type(nifty.index)}")
    print(f"Index length: {len(nifty.index)}")
    print(f"Index dtype: {nifty.index.dtype}")
    print(f"\nFirst 5 index values:\n{nifty.index[:5]}")
    print(f"\nIndex 50 value: {nifty.index[50]}")
    print(f"\nIs index unique? {nifty.index.is_unique}")

    # ========================================================================
    # STEP 8: Simulate the actual error scenario from calculate_actual_regime_lookahead
    # ========================================================================
    print("\n" + "="*70)
    print("🎯 STEP 8: SIMULATING THE ACTUAL ERROR")
    print("="*70)

    current_idx = 50
    lookahead = 5

    print(f"\nAttempting to replicate error at index {current_idx}:")

    try:
        # This is the exact line from gss_core.py line 132
        start_price = nifty.iloc[current_idx]['Close']
        print(f"   ✅ Start price: {start_price}")

        future_price = nifty.iloc[current_idx + lookahead]['Close']
        print(f"   ✅ Future price: {future_price}")

        # THE PROBLEMATIC LINE
        atr_value = nifty.iloc[current_idx]['ATR']
        print(f"   ✅ ATR value: {atr_value}")

        # Calculate threshold
        change_decimal = (future_price - start_price) / start_price
        atr_threshold = (1.5 * atr_value) / start_price

        print(f"\n   Change: {change_decimal:.4f}")
        print(f"   ATR Threshold: {atr_threshold:.4f}")

    except Exception as e:
        print(f"\n   ❌ ERROR REPRODUCED!")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"\n   Full traceback:")
        traceback.print_exc()

    # ========================================================================
    # STEP 9: Alternative access methods (if iloc fails)
    # ========================================================================
    print("\n" + "="*70)
    print("🔧 STEP 9: TESTING ALTERNATIVE ACCESS METHODS")
    print("="*70)

    idx = 50

    print(f"\n1️⃣ Using .iloc[idx]['ATR']:")
    try:
        val1 = nifty.iloc[idx]['ATR']
        print(f"   ✅ Value: {val1}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n2️⃣ Using .loc[index_value, 'ATR']:")
    try:
        val2 = nifty.loc[nifty.index[idx], 'ATR']
        print(f"   ✅ Value: {val2}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n3️⃣ Using ['ATR'].iloc[idx]:")
    try:
        val3 = nifty['ATR'].iloc[idx]
        print(f"   ✅ Value: {val3}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n4️⃣ Using .at[index_value, 'ATR']:")
    try:
        val4 = nifty.at[nifty.index[idx], 'ATR']
        print(f"   ✅ Value: {val4}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # ========================================================================
    # STEP 10: Check for any duplicate columns
    # ========================================================================
    print("\n" + "="*70)
    print("🔍 STEP 10: CHECKING FOR DUPLICATE COLUMNS")
    print("="*70)
    print(f"\nAll columns: {nifty.columns.tolist()}")
    print(f"\nDuplicate columns: {nifty.columns[nifty.columns.duplicated()].tolist()}")
    print(f"\nColumn 'ATR' exists? {'ATR' in nifty.columns}")
    print(f"\nColumn count: {len(nifty.columns)}")
    print(f"\nUnique column count: {len(nifty.columns.unique())}")

    # ========================================================================
    # STEP 11: Visualize the DataFrame structure
    # ========================================================================
    print("\n" + "="*70)
    print("📊 STEP 11: DATAFRAME STRUCTURE SUMMARY")
    print("="*70)
    print(f"\nShape: {nifty.shape}")
    print(f"\nDtypes:\n{nifty.dtypes}")
    print(f"\nMemory usage:\n{nifty.memory_usage(deep=True)}")
    print(f"\nInfo:")
    nifty.info()

    print("\n" + "="*70)
    print("✅ DEBUGGING COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
