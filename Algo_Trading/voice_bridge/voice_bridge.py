import sys
import json
import os
from datetime import datetime
import time

INSTRUCTION_FILE = "instructions.txt"

def listen_for_instructions():
    """
    CodePonting Voice Bridge v0.2
    Reads Claude instructions from instructions.txt file
    """
    print("=" * 50)
    print("CodePonting Voice Bridge v0.2")
    print("Listening for Claude instructions...")
    print("=" * 50)

    last_modified = 0

    while True:
        try:
            if os.path.exists(INSTRUCTION_FILE):
                current_modified = os.path.getmtime(INSTRUCTION_FILE)

                if current_modified > last_modified:
                    with open(INSTRUCTION_FILE, 'r') as f:
                        instruction = f.read().strip()

                    if instruction:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"\n[{timestamp}] Claude's instruction received:")
                        print(f"---\n{instruction}\n---")

                        with open(INSTRUCTION_FILE, 'w') as f:
                            f.write("")

                    last_modified = current_modified

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nVoice Bridge stopped.")
            break

if __name__ == "__main__":
    listen_for_instructions()
