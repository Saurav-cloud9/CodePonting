import sys
import json
import os
from datetime import datetime
import time
import subprocess

INSTRUCTION_FILE = "instructions.txt"
EXECUTED_FILE = "instructions_executed.txt"

def listen_for_instructions():
    """
    CodePonting Voice Bridge v0.2
    Reads Claude instructions from instructions.txt file
    """
    print("=" * 50)
    print("CodePonting Voice Bridge v0.2")
    print("Listening for Claude instructions...")
    print("=" * 50)

    executor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cc_executor.py")
    subprocess.Popen([sys.executable, executor_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("CC Executor launched in background.")

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
                        print(f"\n[{timestamp}] Instruction received:")
                        print(f"---\n{instruction}\n---")
                        print("Waiting for CC execution...")

                        # Wait for CC to confirm execution
                        while True:
                            if os.path.exists(EXECUTED_FILE):
                                with open(EXECUTED_FILE, 'r') as f:
                                    status = f.read().strip()
                                if status == "done":
                                    print("Instruction executed. Clearing files.")
                                    with open(INSTRUCTION_FILE, 'w') as f:
                                        f.write("")
                                    os.remove(EXECUTED_FILE)
                                    break
                            time.sleep(1)

                    last_modified = current_modified

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nVoice Bridge stopped.")
            break

if __name__ == "__main__":
    listen_for_instructions()
