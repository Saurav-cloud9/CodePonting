from datetime import datetime
import time

# Test config
EOD_EXIT_TIME = "14:54"  # Set to 2 mins from now for testing
dashboard_metrics = {
    "positions": {
        "TATAMOTORS": {"qty": 10, "buy_price": 350.0}
    }
}

print("🧪 Starting EOD exit test...")
print(f"📍 EOD time set to: {EOD_EXIT_TIME}")

while True:
    current_time = datetime.now().strftime("%H:%M")
    print(f"🕐 Current time: {current_time}")

    # Check for EOD exit
    if current_time >= EOD_EXIT_TIME:
        print(f"\n⏰ TRIGGERED! {current_time} >= {EOD_EXIT_TIME}")
        print("📤 Would exit all positions here")
        print("✅ EOD logic working!")
        break
    else:
        print(f"   Not yet: {current_time} < {EOD_EXIT_TIME}")

    time.sleep(30)  # Check every 30 seconds

print("🛑 Test complete")