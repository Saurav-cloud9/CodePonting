"""
accumulate_kite_chunk.py
Reads the latest Kite tool-result file from CC's tool-results dir,
parses candles, appends to growing CSV.
Usage: python accumulate_kite_chunk.py
"""
import json, os, glob, csv, sys
from pathlib import Path

TOOL_RESULTS_DIR = r'C:\Users\Saurav\.claude\projects\c--Users-Saurav-CodePonting\e9e1dc13-550d-4fcd-9c75-3da972a3b99a\tool-results'
OUT_CSV = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\scripts\bajfinance_warmup_raw.csv'

def get_latest_kite_file():
    pattern = os.path.join(TOOL_RESULTS_DIR, 'mcp-kite-get_historical_data-*.txt')
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return files[0] if files else None

def parse_candles(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read().strip()
    # The file contains raw JSON — either a list or dict with 'candles' key
    data = json.loads(raw)
    if isinstance(data, list):
        candles = data
    elif isinstance(data, dict):
        candles = data.get('candles', data.get('data', []))
    else:
        return []
    return candles

def main():
    latest = get_latest_kite_file()
    if not latest:
        print('ERROR: No Kite tool-result file found'); sys.exit(1)

    candles = parse_candles(latest)
    if not candles:
        print(f'No candles in {latest}'); sys.exit(1)

    write_header = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['datetime','open','high','low','close','volume','oi'])
        for c in candles:
            w.writerow(c)

    print(f'Appended {len(candles)} candles from {os.path.basename(latest)} -> {OUT_CSV}')
    total = sum(1 for _ in open(OUT_CSV, encoding='utf-8')) - 1
    print(f'Total rows so far: {total:,}')

if __name__ == '__main__':
    main()
