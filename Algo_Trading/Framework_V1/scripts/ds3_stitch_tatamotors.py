"""
DS3 TATAMOTORS Stitch Script
Combines Kite 2015-2021 (from tool-result files) + Upstox 2022-2025 (from parquet).
Applies P1+P2+P3a, saves to intraday_5min_DS3/TATAMOTORS.parquet.
"""
import sys, json, io
from pathlib import Path
import pandas as pd
import pytz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

IST        = pytz.FixedOffset(330)
SCRIPT_DIR = Path(__file__).parent
FV1_DIR    = SCRIPT_DIR.parent
OUTPUT_DIR = FV1_DIR / 'data/historical/intraday_5min_DS3'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# TATAMOTORS Kite tool-result file timestamps (from previous session)
TOOL_DIR  = Path(sys.argv[1])   # pass tool-results dir as arg
START_TS  = int(sys.argv[2])
END_TS    = int(sys.argv[3])
UPSTOX_PARQUET = FV1_DIR / 'data/historical/intraday_5min/TATAMOTORS.parquet'

# ── Load Kite tool-result files ──────────────────────────────────────────────
files = []
for f in TOOL_DIR.glob("mcp-kite-get_historical_data-*.txt"):
    ts = int(f.stem.replace("mcp-kite-get_historical_data-", ""))
    if START_TS <= ts <= END_TS:
        files.append(f)

print(f"Found {len(files)} Kite tool-result files for TATAMOTORS")

rows = []
for fpath in files:
    try:
        raw = json.loads(fpath.read_text(encoding='utf-8'))
        for item in raw:
            if item.get('type') == 'text':
                candles = json.loads(item['text'])
                for c in candles:
                    if isinstance(c, dict):
                        dt = pd.to_datetime(c['date'])
                    else:
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

df_kite = pd.DataFrame(rows)
df_kite['datetime'] = pd.to_datetime(df_kite['datetime']).dt.tz_convert(IST)
for col in ['open','high','low','close']: df_kite[col] = df_kite[col].astype('float64')
for col in ['volume','oi']:               df_kite[col] = df_kite[col].astype('int64')
df_kite = df_kite.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)

print(f"Kite raw: {len(df_kite):,} candles | "
      f"{str(df_kite['datetime'].iloc[0])[:10]} → {str(df_kite['datetime'].iloc[-1])[:10]}")

# Keep Kite ≤ 2021-12-31
KITE_END = pd.Timestamp('2021-12-31 23:59:59', tz=IST)
df_kite  = df_kite[df_kite['datetime'] <= KITE_END].reset_index(drop=True)
print(f"Kite ≤ 2021-12-31: {len(df_kite):,} candles | last = {str(df_kite['datetime'].iloc[-1])[:19]}")

# ── Load Upstox parquet ──────────────────────────────────────────────────────
df_up = pd.read_parquet(UPSTOX_PARQUET)
print(f"Upstox raw: {len(df_up):,} candles | columns: {list(df_up.columns)}")

# Normalize Upstox datetime
if df_up['datetime'].dt.tz is None:
    df_up['datetime'] = df_up['datetime'].dt.tz_localize(IST)
else:
    df_up['datetime'] = df_up['datetime'].dt.tz_convert(IST)

# Keep Upstox ≥ 2022-01-01
UPSTOX_START = pd.Timestamp('2022-01-01', tz=IST)
df_up = df_up[df_up['datetime'] >= UPSTOX_START].reset_index(drop=True)
print(f"Upstox ≥ 2022-01-01: {len(df_up):,} candles | "
      f"first = {str(df_up['datetime'].iloc[0])[:19]}")

# Ensure schema compatibility
for col in ['open','high','low','close']: df_up[col] = df_up[col].astype('float64')
for col in ['volume','oi']:
    if col in df_up.columns:
        df_up[col] = df_up[col].astype('int64')
    else:
        df_up[col] = 0
        print(f"  NOTE: '{col}' not in Upstox data, filled with 0")

# ── Price-gap check at stitch boundary ──────────────────────────────────────
last_kite_close   = df_kite['close'].iloc[-1]
first_up_close    = df_up['close'].iloc[0]
gap_pct = abs(first_up_close - last_kite_close) / last_kite_close * 100
print(f"Stitch gap: last Kite close={last_kite_close:.2f} "
      f"| first Upstox close={first_up_close:.2f} | gap={gap_pct:.2f}%")
if gap_pct > 2.0:
    print(f"  WARNING: gap > 2% ({gap_pct:.2f}%) — different instruments or data issue!")
else:
    print(f"  OK: gap ≤ 2%")

# ── Stitch ───────────────────────────────────────────────────────────────────
COLS = ['datetime','open','high','low','close','volume','oi']
df = pd.concat([df_kite[COLS], df_up[COLS]], ignore_index=True)
df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)

# P1: ≤ 2025-12-31
END_DATE    = pd.Timestamp('2025-12-31', tz=IST)
mask_future = df['datetime'] > END_DATE
n_future    = int(mask_future.sum())
if n_future:
    print(f'  P1: removing {n_future} candles after 2025-12-31')
    df = df[~mask_future].reset_index(drop=True)

# P2: post-15:30
mask_post = df['datetime'].dt.time > pd.Timestamp('15:30').time()
n_post    = int(mask_post.sum())
if n_post:
    print(f'  P2: removing {n_post} post-market candles')
    df = df[~mask_post].reset_index(drop=True)

# P3a: OHLC violations
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

out = OUTPUT_DIR / 'TATAMOTORS.parquet'
df.to_parquet(out, index=False)

trading_days = df['datetime'].dt.date.nunique()
flag = '  ⚠️  LOW COVERAGE' if trading_days < 2000 else ''
print(f'✅ TATAMOTORS: {len(df):,} candles | '
      f'{str(df["datetime"].iloc[0])[:10]} → {str(df["datetime"].iloc[-1])[:10]} | '
      f'{trading_days} trading days{flag}')
print(f'   Future removed: {n_future} | PostMkt removed: {n_post} | OHLC removed: {n_ohlc}')
print(f'   Saved → {out}')
