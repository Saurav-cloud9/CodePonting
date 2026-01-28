import subprocess, sys

def main():
    for script in ["step1_threshold_sweep.py", "step2_multistock_validation.py", "step3_final_report.py"]:
        print(f"Running {script}...")
        subprocess.run([sys.executable, script], check=True)
    print("Option A Complete.")

if __name__ == "__main__": main()