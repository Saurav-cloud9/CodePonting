"""
Audio Alert Test Program
Test different beep sounds before adding to bot
"""

import winsound
import time

print("=" * 60)
print("AUDIO ALERT TESTING")
print("=" * 60)

while True:
    # Test 3: Triple beep (ding-ding-DING)
    print("3. Testing triple beep (recommended)...")
    print("   Playing in 2 seconds...")
    time.sleep(2)
    winsound.Beep(800, 200)  # Low
    time.sleep(0.1)
    winsound.Beep(1000, 200)  # Medium
    time.sleep(0.1)
    winsound.Beep(1200, 400)  # High
    print("   ✅ Did you hear it?\n")
    time.sleep(2)

