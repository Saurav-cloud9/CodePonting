import os
import time
from datetime import datetime

INSTRUCTION_FILE = "instructions.txt"
EXECUTED_FILE = "instructions_executed.txt"

def run():
    print("=" * 50)
    print("CC Executor v0.1")
    print("Watching instructions.txt...")
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
                        print(f"\n[{timestamp}] Executing instruction:")
                        print(f"---\n{instruction}\n---")
                        try:
                            exec(instruction, {"__builtins__": __builtins__})
                            print("Execution complete.")
                        except Exception as e:
                            print(f"Execution error: {e}")

                        with open(EXECUTED_FILE, 'w') as f:
                            f.write("done")

                        print(f"Written 'done' to {EXECUTED_FILE}. Waiting for next instruction...")

                    last_modified = current_modified

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nCC Executor stopped.")
            break

if __name__ == "__main__":
    run()
