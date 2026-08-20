"""
BEEP TEST - Bot v0.7 v2
Quick test to verify audio alert functionality
"""


import time

# Try to import winsound
try:
    import winsound
    AUDIO_AVAILABLE = True
    print("✅ winsound module imported successfully")
except ImportError:
    AUDIO_AVAILABLE = False
    print("❌ winsound not available (not on Windows?)")

def play_signal_alert():
    """Play 3 beeps to alert signal detection"""
    if AUDIO_AVAILABLE:
        try:
            print("\n🔔 Playing 3 beeps...")
            # Play 3 beeps: frequency 1000 Hz, 200ms each
            for i in range(3):
                print(f"   Beep {i+1}...")
                winsound.Beep(1000, 200)
                time.sleep(0.1)  # Small gap between beeps
            print("✅ Beep test completed!\n")
            return True
        except Exception as e:
            print(f"❌ Error playing beep: {e}")
            return False
    else:
        print("⚠️  Audio not available - beeps won't play in bot")
        return False

# Run the test
print("=" * 60)
print("BEEP FUNCTIONALITY TEST")
print("=" * 60)
print("\nThis will play 3 short beeps to simulate signal detection.")
print("Press ENTER to test...\n")
input()

success = play_signal_alert()

if success:
    print("✅ RESULT: Beeps working! Bot v0.7 v2 will alert you on signals.")
else:
    print("⚠️  RESULT: Beeps not working, but bot will still function normally.")

print("\n" + "=" * 60)
input("Press ENTER to exit...")
