"""
Patch fv2_signal_viewer.html — add Vol_Ratio (vol/vol_ma20) as p[7] to candle tooltip.
Data format discovered: "c":{"YYYY-MM-DD":"o,h,l,c,ma,sl,atr|o,h,l,c,ma,sl,atr|..."}
"""
import pandas as pd
import re
from collections import defaultdict

PATH_HTML = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/outputs/reports/fv2_signal_viewer.html"
PATH_CSV  = r"c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min/TATAMOTORS_5min.csv"

# ── Build vol_ratio lookup: date → list of vr strings (in order) ─────────────
df = pd.read_csv(PATH_CSV, parse_dates=['datetime'])
if 'vol_ma20' not in df.columns:
    df['vol_ma20'] = df['volume'].rolling(20).mean()
df['vr'] = (df['volume'] / df['vol_ma20']).round(2)
df = df.sort_values('datetime')
day_vr = defaultdict(list)
for _, row in df.iterrows():
    d = row['datetime'].strftime('%Y-%m-%d')
    day_vr[d].append('' if pd.isna(row['vr']) else str(row['vr']))

with open(PATH_HTML, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Patch candle strings: append vr as 8th field ──────────────────────────
def patch_day(m):
    date_str = m.group(1)
    raw = m.group(2)
    vr_list = day_vr.get(date_str, [])
    candles = raw.split('|')
    out = []
    for i, c in enumerate(candles):
        vr = vr_list[i] if i < len(vr_list) else ''
        out.append(c + ',' + vr)
    return f'"{date_str}":"{"|".join(out)}"'

new_html = re.sub(r'"(\d{4}-\d{2}-\d{2})":"([^"]+)"', patch_day, html)

added = new_html.count(',') - html.count(',')
print(f"Candle fields patched. Extra commas: {added:,}")

# ── 2. Update JS parser ───────────────────────────────────────────────────────
OLD_PARSER = "return {o: +p[0], h: +p[1], l: +p[2], c: +p[3], ma: p[4] ? +p[4] : null, sl: p[5] ? +p[5] : null, atr: p[6] ? +p[6] : null};"
NEW_PARSER = "return {o: +p[0], h: +p[1], l: +p[2], c: +p[3], ma: p[4] ? +p[4] : null, sl: p[5] ? +p[5] : null, atr: p[6] ? +p[6] : null, vr: p[7] ? +p[7] : null};"
assert OLD_PARSER in new_html, "Parser anchor not found"
new_html = new_html.replace(OLD_PARSER, NEW_PARSER, 1)

# ── 3. Add Vol Ratio row after ATR14 in tooltip ───────────────────────────────
OLD_TT = "    if (c.atr !== null) html += '<div class=\"tt-row\"><span class=\"tt-label\">ATR14</span><span class=\"tt-val\" style=\"color:#888\">' + c.atr.toFixed(2) + '</span></div>';"
NEW_TT = (
    OLD_TT + "\n"
    "    if (c.vr !== null) { const vrC = c.vr >= 1.5 ? '#f97316' : c.vr >= 1.0 ? '#888' : '#555d72';"
    " html += '<div class=\"tt-row\"><span class=\"tt-label\">Vol Ratio</span>"
    "<span class=\"tt-val\" style=\"color:' + vrC + '\">' + c.vr.toFixed(2) + 'x</span></div>'; }"
)
assert OLD_TT in new_html, "Tooltip anchor not found"
new_html = new_html.replace(OLD_TT, NEW_TT, 1)

with open(PATH_HTML, 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f"Written OK. {len(new_html)//1024//1024} MB")
print("Color: orange>=1.5x, grey>=1.0x, dim<1.0x")
