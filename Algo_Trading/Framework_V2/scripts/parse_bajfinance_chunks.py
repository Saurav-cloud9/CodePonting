"""
Parse BAJFINANCE MCP result files and build BAJFINANCE_5min.csv with outcome columns.
Run after all chunk files are fetched.
"""
import json, re
from pathlib import Path
import pandas as pd
import numpy as np
import pytz

TOOL_DIR = Path(r'C:\Users\Saurav\.claude\projects\c--Users-Saurav-CodePonting\88a37868-0107-4210-8cec-ccb641b46966\tool-results')
OUT_DIR  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
OUT_CSV  = OUT_DIR / 'BAJFINANCE_5min.csv'
IST      = pytz.FixedOffset(330)
DATE_START = '2022-01-01'
DATE_END   = '2025-12-31'

# ── Collect all bajfinance chunk files ────────────────────────────────────────
chunk_files = sorted(TOOL_DIR.glob('mcp-kite-get_historical_data-*.txt'))
print(f"Found {len(chunk_files)} chunk files")

all_candles = []
for f in chunk_files:
    raw = f.read_text(encoding='utf-8')
    # Format: [{"type": "text", "text": "..."}]
    try:
        outer = json.loads(raw)
        for item in outer:
            if item.get('type') == 'text':
                text = item['text']
                # text is a JSON object or array
                try:
                    data = json.loads(text)
                except:
                    # Try to extract JSON array from text
                    m = re.search(r'\[.*\]', text, re.DOTALL)
                    if m:
                        data = json.loads(m.group())
                    else:
                        print(f"  Could not parse candles from {f.name}")
                        continue
                # data may be {"candles": [...]} or [...] directly
                if isinstance(data, list):
                    candles = data
                elif isinstance(data, dict):
                    candles = data.get('candles', data.get('data', []))
                else:
                    candles = []
                all_candles.extend(candles)
                print(f"  {f.name}: +{len(candles):,} candles (total: {len(all_candles):,})")
    except Exception as e:
        print(f"  ERROR {f.name}: {e}")

print(f"\nTotal raw candles: {len(all_candles):,}")

if not all_candles:
    print("No candles found — exiting")
    raise SystemExit(1)

# ── Build DataFrame ────────────────────────────────────────────────────────────
rows = []
for c in all_candles:
    if isinstance(c, dict):
        raw_dt = c.get('date') or c.get('datetime') or c.get('time')
        dt = pd.to_datetime(raw_dt, utc=False)
        row = {
            'datetime': dt,
            'open':     float(c.get('open', c.get('o', 0))),
            'high':     float(c.get('high', c.get('h', 0))),
            'low':      float(c.get('low',  c.get('l', 0))),
            'close':    float(c.get('close', c.get('c', 0))),
            'volume':   int(c.get('volume', c.get('v', 0))),
        }
    else:
        dt = pd.to_datetime(c[0], utc=False)
        row = {
            'datetime': dt,
            'open':     float(c[1]),
            'high':     float(c[2]),
            'low':      float(c[3]),
            'close':    float(c[4]),
            'volume':   int(c[5]),
        }
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    else:
        dt = dt.astimezone(IST)
    row['datetime'] = dt
    rows.append(row)

df = pd.DataFrame(rows)
df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)
df = df[df['datetime'].dt.time <= pd.Timestamp('15:30').time()].reset_index(drop=True)
print(f"After dedup + market hours filter: {len(df):,} candles")
print(f"Range: {df['datetime'].iloc[0]}  to  {df['datetime'].iloc[-1]}")

# ── Signal logic ───────────────────────────────────────────────────────────────
df['ma20']     = df['close'].rolling(20).mean()
prev_close     = df['close'].shift(1)
tr = pd.concat([
    df['high'] - df['low'],
    (df['high'] - prev_close).abs(),
    (df['low']  - prev_close).abs()
], axis=1).max(axis=1)
df['atr14']    = tr.rolling(14).mean()
df['vol_ma20'] = df['volume'].rolling(20).mean()

# Filter to output range
df = df[(df['datetime'] >= DATE_START) & (df['datetime'] <= DATE_END)].reset_index(drop=True)
print(f"After date filter (2022–2025): {len(df):,} rows")
print(f"NaN in MA20: {df['ma20'].isna().sum()}")

df['_date'] = df['datetime'].dt.date
eod_map = df.groupby('_date').apply(lambda g: g.index[-1], include_groups=False).to_dict()

df['signal_type'] = pd.Series(dtype='object')
df['exit_reason'] = pd.Series(dtype='object')
df['raw_pnl']     = np.nan
df['win']         = np.nan

n = len(df)
i = 0
while i < n:
    row = df.iloc[i]
    if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
        i += 1; continue
    if row['low'] > row['ma20']:
        i += 1; continue

    touch_idx  = i
    touch_date = row['_date']

    bounce_idx = None
    for j in range(touch_idx, min(touch_idx + 4, n)):
        b = df.iloc[j]
        if b['_date'] != touch_date: break
        if b['close'] > b['ma20'] and b['volume'] >= 1.2 * b['vol_ma20']:
            bounce_idx = j; break

    if bounce_idx is None or bounce_idx + 1 >= n:
        i += 1; continue

    entry_idx   = bounce_idx + 1
    entry_row   = df.iloc[entry_idx]
    entry_date  = entry_row['_date']
    entry_price = entry_row['open']
    atr         = df.iloc[touch_idx]['atr14']
    sl          = entry_price - 2.5 * atr
    target      = entry_price + 4.5 * atr

    if touch_idx >= 5:
        ma_now  = df.iloc[touch_idx]['ma20']
        ma_prev = df.iloc[touch_idx - 5]['ma20']
        slope   = (ma_now - ma_prev) / ma_now * 100
        sig_type = 'rising' if slope > 0.05 else ('falling' if slope < -0.05 else 'flat')
    else:
        sig_type = 'flat'

    eod_idx = eod_map.get(entry_date)
    if eod_idx is None:
        i += 1; continue

    exit_reason = exit_price = None
    for k in range(entry_idx, n):
        krow = df.iloc[k]
        if krow['_date'] != entry_date:
            exit_reason = 'EOD'; exit_price = df.iloc[eod_idx]['close']; break
        if krow['high'] >= target:
            exit_reason = 'target'; exit_price = target; break
        if krow['low'] <= sl:
            exit_reason = 'stoploss'; exit_price = sl; break
        if k == eod_idx:
            exit_reason = 'EOD'; exit_price = krow['close']; break

    if exit_reason is None:
        i += 1; continue

    df.at[entry_idx, 'signal_type'] = sig_type
    df.at[entry_idx, 'exit_reason']  = exit_reason
    df.at[entry_idx, 'raw_pnl']      = exit_price - entry_price
    df.at[entry_idx, 'win']          = 1 if exit_reason == 'target' else 0
    i = k + 1

out = df.drop(columns=['atr14', 'vol_ma20', '_date'])
trades = out.dropna(subset=['signal_type'])
r = (trades['signal_type'] == 'rising').sum()
fl = (trades['signal_type'] == 'flat').sum()
fa = (trades['signal_type'] == 'falling').sum()

out.to_csv(OUT_CSV, index=False)
print(f"\nSaved: {OUT_CSV}")
print(f"Rows : {len(out):,} | Signals: {len(trades):,} | Rising: {r} | Flat: {fl} | Falling: {fa}")
print(f"Win rate (rising): {(trades[trades['signal_type']=='rising']['win'].mean()*100):.1f}%")
