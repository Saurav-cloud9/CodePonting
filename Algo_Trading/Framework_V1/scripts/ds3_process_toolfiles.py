"""
DS3 Tool-Results Processor
Reads MCP get_historical_data tool-result files, builds DataFrame, saves parquet.

Usage:
    python ds3_process_toolfiles.py <STOCK> <file1.txt> [file2.txt ...]
"""
import sys, json, io
from pathlib import Path
import pandas as pd
import pytz

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

STOCK     = sys.argv[1]
TXT_FILES = sys.argv[2:]

IST        = pytz.FixedOffset(330)
# Script is at Framework_V1/scripts/ → go up two levels to reach Framework_V1/
SCRIPT_DIR = Path(__file__).parent           # .../Framework_V1/scripts
FV1_DIR    = SCRIPT_DIR.parent               # .../Framework_V1
OUTPUT_DIR = FV1_DIR / 'data/historical/intraday_5min_DS3'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

END_DATE = pd.Timestamp('2025-12-31', tz=IST)

rows = []
for fpath in TXT_FILES:
    try:
        raw = json.loads(Path(fpath).read_text(encoding='utf-8'))
        # format: [{type: "text", text: "candle_json_string"}]
        for item in raw:
            if item.get('type') == 'text':
                candles = json.loads(item['text'])
                for c in candles:
                    if isinstance(c, dict):
                        dt = pd.to_datetime(c['date'])
                    else:  # array format fallback
                        dt = pd.to_datetime(c[0])
                        c  = {'date': c[0], 'open': c[1], 'high': c[2],
                              'low': c[3], 'close': c[4], 'volume': c[5],
                              'oi': c[6] if len(c) > 6 else 0}
                    if dt.tzinfo is None:
                        dt = IST.localize(dt)
                    else:
                        dt = dt.astimezone(IST)
                    rows.append({
                        'datetime': dt,
                        'open':   float(c['open']),
                        'high':   float(c['high']),
                        'low':    float(c['low']),
                        'close':  float(c['close']),
                        'volume': int(c['volume']),
                        'oi':     int(c.get('oi', 0)),
                    })
    except Exception as e:
        print(f'  WARN: {fpath}: {e}')

if not rows:
    print(f'ERROR: No candles found for {STOCK}')
    sys.exit(1)

df = pd.DataFrame(rows)
df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
for col in ['open','high','low','close']:
    df[col] = df[col].astype('float64')
for col in ['volume','oi']:
    df[col] = df[col].astype('int64')

df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)

# ── P1: enforce end-date ≤ 2025-12-31 ──────────────────────────────────────
mask_future = df['datetime'] > END_DATE
n_future = int(mask_future.sum())
if n_future:
    print(f'  P1: removing {n_future} candles after 2025-12-31')
    df = df[~mask_future].reset_index(drop=True)

# ── P2: remove post 15:30 candles ──────────────────────────────────────────
mask_post = df['datetime'].dt.time > pd.Timestamp('15:30').time()
n_post = int(mask_post.sum())
if n_post:
    print(f'  P2: removing {n_post} post-market candles')
    df = df[~mask_post].reset_index(drop=True)

# ── P3a: OHLC violations ───────────────────────────────────────────────────
mask_ohlc = (
    (df['high'] < df['low'])   |
    (df['high'] < df['open'])  |
    (df['high'] < df['close']) |
    (df['low']  > df['open'])  |
    (df['low']  > df['close'])
)
n_ohlc = int(mask_ohlc.sum())
if n_ohlc:
    print(f'  P3a: removing {n_ohlc} OHLC-violation rows')
    df = df[~mask_ohlc].reset_index(drop=True)

out = OUTPUT_DIR / f'{STOCK}.parquet'
df.to_parquet(out, index=False)

trading_days = df['datetime'].dt.date.nunique()
flag = '  ⚠️  LOW COVERAGE' if trading_days < 2000 else ''
print(f'✅ {STOCK}: {len(df):,} candles | '
      f'{str(df["datetime"].iloc[0])[:10]} → {str(df["datetime"].iloc[-1])[:10]} | '
      f'{trading_days} trading days{flag}')
print(f'   Future removed: {n_future} | PostMkt removed: {n_post} | OHLC removed: {n_ohlc}')
print(f'   Saved → {out}')
