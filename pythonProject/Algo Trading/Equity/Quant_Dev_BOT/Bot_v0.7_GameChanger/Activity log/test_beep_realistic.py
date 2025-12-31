"""
REALISTIC BOT SIMULATION - Beep Test
Simulates bot scanning and beeping like the real bot will
"""

import time
import winsound

def play_signal_alert():
    """Play 3 beeps to alert signal detection"""
    try:
        for _ in range(3):
            winsound.Beep(1000, 200)
            time.sleep(0.1)
    except:
        pass

# Simulate bot scanning
print("=" * 60)
print("🎮 BOT SIMULATION - Testing Beeps During Scanning")
print("=" * 60)
print("\nSimulating bot behavior:")
print("- Scanning stocks every 5 seconds")
print("- Will trigger 'signal' at 15 seconds")
print("- Check if you hear 3 beeps when signal appears!\n")

input("Press ENTER to start simulation...")

start_time = time.time()
signal_triggered = False

for i in range(6):  # 30 second simulation
    elapsed = int(time.time() - start_time)
    
    print(f"\n[{elapsed}s] Scanning stocks...")
    print("   Checking YESBANK... No signal")
    print("   Checking SUZLON... No signal")
    print("   Checking PNB... No signal")
    
    # Trigger signal at 15 seconds
    if elapsed >= 15 and not signal_triggered:
        print("\n" + "=" * 60)
        print("🔔 SIGNAL DETECTED FOR PNB!")
        print("=" * 60)
        
        # PLAY BEEPS
        play_signal_alert()
        
        print("\n⚠️  Did you hear 3 beeps just now?")
        print("    Signal detected - waiting for confirmation...")
        
        signal_triggered = True
        
        # Simulate waiting for user input (like real bot)
        print("\n    Press ENTER to confirm order (or type 'skip')...")
        user_input = input("    > ").strip().lower()
        
        if user_input == 'skip':
            print("    ⏭️  Signal skipped\n")
        else:
            print("    ✅ Order confirmed\n")
        
        print("Continuing scan...\n")
    
    # Small delay between scans
    time.sleep(5)

print("\n" + "=" * 60)
print("SIMULATION COMPLETE")
print("=" * 60)
print("\n✅ If you heard 3 beeps at the 15-second mark,")
print("   then beeps will work in the live bot too!")
print("\n❌ If you didn't hear beeps, we should skip audio alerts.")

print("\n" + "=" * 60)
heard = input("\nDid you hear the beeps during simulation? (yes/no): ").strip().lower()

if heard == 'yes':
    print("\n✅ PERFECT! Bot v0.7 v2 is ready with audio alerts.")
    print("   You'll hear beeps when signals are detected while trading.")
else:
    print("\n⚠️  Beeps didn't work during scanning.")
    print("   Recommendation: Use Bot v0.7 v1 (without beeps)")
    print("   or keep v2 but rely on visual alerts only.")

print("\n" + "=" * 60)
input("Press ENTER to exit...")
