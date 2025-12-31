"""
Audio Alert Test Program
Test different beep sounds before adding to bot
"""

import winsound
import time

print("=" * 60)
print("AUDIO ALERT TESTING")
print("=" * 60)

# Test 1: Simple single beep
print("\n1. Testing simple beep...")
print("   Playing in 2 seconds...")
time.sleep(2)
winsound.Beep(1000, 500)
print("   ✅ Did you hear it?\n")
time.sleep(2)

# Test 2: Double beep
print("2. Testing double beep...")
print("   Playing in 2 seconds...")
time.sleep(2)
winsound.Beep(1000, 300)
time.sleep(0.2)
winsound.Beep(1000, 300)
print("   ✅ Did you hear it?\n")
time.sleep(2)

# Test 3: Triple beep (ding-ding-DING)
print("3. Testing triple beep (recommended)...")
print("   Playing in 2 seconds...")
time.sleep(2)
winsound.Beep(800, 200)   # Low
time.sleep(0.1)
winsound.Beep(1000, 200)  # Medium
time.sleep(0.1)
winsound.Beep(1200, 400)  # High
print("   ✅ Did you hear it?\n")
time.sleep(2)

# Test 4: Gentle chime
print("4. Testing gentle chime...")
print("   Playing in 2 seconds...")
time.sleep(2)
winsound.Beep(1500, 200)
time.sleep(0.05)
winsound.Beep(1200, 300)
print("   ✅ Did you hear it?\n")
time.sleep(2)

# Test 5: Attention pattern
print("5. Testing attention pattern...")
print("   Playing in 2 seconds...")
time.sleep(2)
winsound.Beep(1000, 150)
time.sleep(0.1)
winsound.Beep(1200, 150)
time.sleep(0.1)
winsound.Beep(1000, 150)
time.sleep(0.1)
winsound.Beep(1400, 400)
print("   ✅ Did you hear it?\n")

print("=" * 60)
print("TESTING COMPLETE!")
print("=" * 60)
print("\nWhich one did you like best?")
print("1 = Simple beep")
print("2 = Double beep")
print("3 = Triple beep (ding-ding-DING)")
print("4 = Gentle chime")
print("5 = Attention pattern")
