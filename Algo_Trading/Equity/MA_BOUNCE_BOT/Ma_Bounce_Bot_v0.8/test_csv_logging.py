"""
CSV LOGGING TEST SCRIPT
Tests both daily and master CSV file creation with all 18 columns
"""

import csv
import os
from datetime import datetime

# File names (same as bot)
today = datetime.now().strftime("%Y%m%d")
TRADES_LOG_FILE = f"trades_log_{today}.csv"
TRADES_MASTER_FILE = "trades_log_master.csv"

# CSV Headers (18 columns as designed)
headers = [
    'Date', 'Entry_Time', 'Exit_Time', 'Symbol',
    'Entry_Price', 'Exit_Price', 'Qty', 'P&L', 'P&L%',
    'Target_Price', 'SL_Price', 'Target_Hit',
    'Entry_Source', 'Exit_Source',
    'Hold_Duration_Minutes',
    'MA20_Distance_%',
    'Distance_to_Target_%',
    'Entry_Time_Category'
]

# Test data (3 dummy trades)
test_trades = [
    {
        'Date': '2025-12-31',
        'Entry_Time': '09:25:00',
        'Exit_Time': '10:15:00',
        'Symbol': 'TEST1',
        'Entry_Price': '100.00',
        'Exit_Price': '102.00',
        'Qty': 5,
        'P&L': '10.00',
        'P&L%': '2.00',
        'Target_Price': '102.00',
        'SL_Price': '99.00',
        'Target_Hit': 'Yes',
        'Entry_Source': 'Bot',
        'Exit_Source': 'Bot_Target',
        'Hold_Duration_Minutes': 50,
        'MA20_Distance_%': '0.45',
        'Distance_to_Target_%': '0.00',
        'Entry_Time_Category': 'Early'
    },
    {
        'Date': '2025-12-31',
        'Entry_Time': '11:30:00',
        'Exit_Time': '12:05:00',
        'Symbol': 'TEST2',
        'Entry_Price': '50.00',
        'Exit_Price': '49.50',
        'Qty': 10,
        'P&L': '-5.00',
        'P&L%': '-1.00',
        'Target_Price': '51.00',
        'SL_Price': '49.50',
        'Target_Hit': 'No',
        'Entry_Source': 'Bot',
        'Exit_Source': 'Bot_SL',
        'Hold_Duration_Minutes': 35,
        'MA20_Distance_%': '0.80',
        'Distance_to_Target_%': '3.00',
        'Entry_Time_Category': 'Mid'
    },
    {
        'Date': '2025-12-31',
        'Entry_Time': '13:00:00',
        'Exit_Time': '15:15:00',
        'Symbol': 'TEST3',
        'Entry_Price': '150.00',
        'Exit_Price': '150.75',
        'Qty': 3,
        'P&L': '2.25',
        'P&L%': '0.50',
        'Target_Price': '153.00',
        'SL_Price': '148.50',
        'Target_Hit': 'No',
        'Entry_Source': 'Bot',
        'Exit_Source': 'Bot_EOD',
        'Hold_Duration_Minutes': 135,
        'MA20_Distance_%': '1.20',
        'Distance_to_Target_%': '1.50',
        'Entry_Time_Category': 'Late'
    }
]

def test_csv_logging():
    """Test CSV file creation and verify format"""
    
    print("\n" + "=" * 70)
    print("🧪 CSV LOGGING TEST SCRIPT")
    print("=" * 70)
    
    # Test 1: Create DAILY CSV
    print(f"\n📝 TEST 1: Creating daily CSV - {TRADES_LOG_FILE}")
    
    with open(TRADES_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for trade in test_trades:
            writer.writerow(trade)
    
    if os.path.exists(TRADES_LOG_FILE):
        file_size = os.path.getsize(TRADES_LOG_FILE)
        print(f"✅ DAILY CSV CREATED: {TRADES_LOG_FILE}")
        print(f"   File size: {file_size} bytes")
        print(f"   Trades logged: {len(test_trades)}")
    else:
        print(f"❌ FAILED to create {TRADES_LOG_FILE}")
        return False
    
    # Test 2: Create MASTER CSV
    print(f"\n📝 TEST 2: Creating master CSV - {TRADES_MASTER_FILE}")
    
    with open(TRADES_MASTER_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for trade in test_trades:
            writer.writerow(trade)
    
    if os.path.exists(TRADES_MASTER_FILE):
        file_size = os.path.getsize(TRADES_MASTER_FILE)
        print(f"✅ MASTER CSV CREATED: {TRADES_MASTER_FILE}")
        print(f"   File size: {file_size} bytes")
        print(f"   Trades logged: {len(test_trades)}")
    else:
        print(f"❌ FAILED to create {TRADES_MASTER_FILE}")
        return False
    
    # Test 3: Verify columns
    print(f"\n📝 TEST 3: Verifying CSV structure")
    
    with open(TRADES_LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_headers = reader.fieldnames
        
        print(f"\n   Expected columns: {len(headers)}")
        print(f"   Found columns: {len(csv_headers)}")
        
        if csv_headers == headers:
            print(f"   ✅ ALL 18 COLUMNS CORRECT!")
        else:
            print(f"   ❌ COLUMN MISMATCH!")
            print(f"   Missing: {set(headers) - set(csv_headers)}")
            print(f"   Extra: {set(csv_headers) - set(headers)}")
            return False
    
    # Test 4: Read and display sample data
    print(f"\n📝 TEST 4: Sample data preview")
    print("-" * 70)
    
    with open(TRADES_LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            print(f"\nTrade {i}:")
            print(f"   Symbol: {row['Symbol']} | Entry: ₹{row['Entry_Price']} | Exit: ₹{row['Exit_Price']}")
            print(f"   P&L: ₹{row['P&L']} ({row['P&L%']}%) | Target Hit: {row['Target_Hit']}")
            print(f"   Exit Source: {row['Exit_Source']} | Duration: {row['Hold_Duration_Minutes']}min")
            print(f"   MA20 Distance: {row['MA20_Distance_%']}% | Category: {row['Entry_Time_Category']}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
    print(f"\n📂 Files created in current directory:")
    print(f"   • {TRADES_LOG_FILE}")
    print(f"   • {TRADES_MASTER_FILE}")
    
    print(f"\n⚠️  These are TEST files with dummy data")
    print(f"   To delete them, run:")
    print(f"   del {TRADES_LOG_FILE}")
    print(f"   del {TRADES_MASTER_FILE}")
    
    return True

if __name__ == "__main__":
    test_csv_logging()
