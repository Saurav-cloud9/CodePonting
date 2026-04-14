"""
Re-patch candle data for ALL 30 stocks in fv2_signal_viewer.html.
Parser + tooltip are already correct — only candle strings need p[7] added.
"""
import pandas as pd
import re
from collections import defaultdict
import os

PATH_HTML  = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_signal_viewer.html"
CSV_DIR    = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min"

# ── Build vol_ratio lookup for ALL stocks: (stock, date) → [vr, vr, ...] ─────
print("Loading CSVs...")
all_day_vr = {}  # date_str → ordered list of vr strings (across all stocks combined)
# Actually need per-stock lookup since same date appears in multiple stocks
# But candle data in HTML is keyed only by date, not stock+date
# Check: does HTML store per-stock data separately?

with open(PATH_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

# Check structure: ALL_STOCKS_DATA[stock]["c"][date] = candle_str
# So same date key appears once per stock — we need per-stock lookup
# Pattern: "STOCKNAME":{"d":[...],"c":{"date":"candles",...},...}

# Build per-stock per-date vol_ratio lists
stock_day_vr = {}  # stock → {date → [vr_str, ...]}

for fname in os.listdir(CSV_DIR):
    if not fname.endswith('_5min.csv'):
        continue
    stock = fname.replace('_5min.csv', '')
    df = pd.read_csv(os.path.join(CSV_DIR, fname), parse_dates=['datetime'])
    if 'vol_ma20' not in df.columns:
        df['vol_ma20'] = df['volume'].rolling(20).mean()
    df['vr'] = (df['volume'] / df['vol_ma20']).round(2)
    df = df.sort_values('datetime')
    day_vr = defaultdict(list)
    for _, row in df.iterrows():
        d = row['datetime'].strftime('%Y-%m-%d')
        day_vr[d].append('' if pd.isna(row['vr']) else str(row['vr']))
    stock_day_vr[stock] = dict(day_vr)
    print(f"  {stock}: {len(day_vr)} days")

print(f"Loaded {len(stock_day_vr)} stocks")

# ── Patch per-stock candle blocks ─────────────────────────────────────────────
# Pattern: "STOCK":{"d":[...],"c":{...candles...}
# We'll process stock by stock using the known stock names

def patch_candle_str(raw, vr_list):
    candles = raw.split('|')
    out = []
    for i, c in enumerate(candles):
        # Only add if not already 8 fields
        if c.count(',') >= 7:
            out.append(c)
            continue
        vr = vr_list[i] if i < len(vr_list) else ''
        out.append(c + ',' + vr)
    return '|'.join(out)

total_patched = 0
for stock, day_vr in stock_day_vr.items():
    # Find this stock's candle section and patch dates within it
    stock_marker = f'"{stock}":{{'
    idx_stock = html.find(stock_marker)
    if idx_stock < 0:
        print(f"  SKIP {stock} — not found in HTML")
        continue

    # Find end of this stock's block (next top-level stock key or end)
    # Simple approach: regex replace only within a window
    # More robust: replace date→candle pairs globally but use stock context
    # Since dates are unique per stock block, we can just do a targeted replace

    def make_replacer(dv):
        def replacer(m):
            date_str = m.group(1)
            raw = m.group(2)
            if raw.split('|')[0].count(',') >= 7:
                return m.group(0)  # already patched
            vrl = dv.get(date_str, [])
            return f'"{date_str}":"{patch_candle_str(raw, vrl)}"'
        return replacer

    # Find this stock's "c":{...} block boundaries
    c_start = html.find('"c":{', idx_stock)
    if c_start < 0:
        continue
    # Find matching closing brace
    depth = 0
    pos = c_start + 5
    for pos in range(c_start + 4, min(c_start + 5_000_000, len(html))):
        if html[pos] == '{': depth += 1
        elif html[pos] == '}':
            if depth == 0:
                break
            depth -= 1
    c_end = pos + 1

    segment = html[c_start:c_end]
    new_segment = re.sub(r'"(\d{4}-\d{2}-\d{2})":"([^"]+)"', make_replacer(day_vr), segment)
    changed = new_segment.count(',') - segment.count(',')
    total_patched += changed
    html = html[:c_start] + new_segment + html[c_end:]
    print(f"  {stock}: +{changed:,} commas")

print(f"\nTotal commas added: {total_patched:,}")

# Verify parser + tooltip already in place
assert 'vr: p[7] ? +p[7] : null' in html, "Parser missing!"
assert 'Vol Ratio' in html, "Tooltip missing!"
print("Parser + tooltip: OK")

with open(PATH_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written OK. {len(html)//1024//1024} MB")
