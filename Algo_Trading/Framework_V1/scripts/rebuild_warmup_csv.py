import json, os, glob, csv

TOOL_RESULTS_DIR = r'C:\Users\Saurav\.claude\projects\c--Users-Saurav-CodePonting\e9e1dc13-550d-4fcd-9c75-3da972a3b99a\tool-results'
OUT_CSV = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\scripts\bajfinance_warmup_raw.csv'

files = sorted(glob.glob(os.path.join(TOOL_RESULTS_DIR, 'mcp-kite-get_historical_data-*.txt')), key=os.path.getmtime)
print(f'Processing {len(files)} chunk files...')

all_candles = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    candles = data if isinstance(data, list) else data.get('candles', [])
    all_candles.extend(candles)
    print(f'  {os.path.basename(f)}: {len(candles)} candles')

seen = set()
unique = []
for c in all_candles:
    key = c['date']
    if key not in seen:
        seen.add(key)
        unique.append(c)
unique.sort(key=lambda x: x['date'])

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['datetime','open','high','low','close','volume','oi'])
    for c in unique:
        w.writerow([c['date'], c['open'], c['high'], c['low'], c['close'], c['volume'], c['oi']])

print(f'Total unique candles: {len(unique):,}')
print(f'Range: {unique[0]["date"]} -> {unique[-1]["date"]}')
print(f'Saved: {OUT_CSV}')
