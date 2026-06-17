"""
add_vol_ma20_to_csv.py
Adds vol_ma20 column to all 30 fv2 CSVs with proper warmup.

DS3 stocks (29): load DS3 parquet (2015+), compute rolling(20), filter to 2022+, merge into CSV.
BAJFINANCE    : parse existing 2021 Kite tool-result chunks for warmup, compute rolling(20), filter to 2022+.
"""

import json
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
CSV_DIR  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
DS3_DIR  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V1/data/historical/intraday_5min_DS3')
TOOL_DIR = Path(r'C:/Users/Saurav/.claude/projects/c--Users-Saurav-CodePonting/88a37868-0107-4210-8cec-ccb641b46966/tool-results')

DATE_START = '2022-01-01'

DS3_STOCKS = [
    'ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BANDHANBNK', 'BHARTIARTL',
    'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB', 'HDFCBANK', 'HINDALCO',
    'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'NATIONALUM',
    'NTPC', 'ONGC', 'PNB', 'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'VEDL', 'WIPRO',
]


def add_vol_ma20_ds3(stock: str):
    csv_path = CSV_DIR / f'{stock}_5min.csv'
    parquet  = DS3_DIR / f'{stock}.parquet'

    df = pd.read_csv(csv_path)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=False)

    ds3 = pd.read_parquet(parquet, columns=['datetime', 'volume'])
    ds3['datetime'] = pd.to_datetime(ds3['datetime'], utc=False)
    ds3 = ds3.sort_values('datetime').reset_index(drop=True)
    ds3['vol_ma20'] = ds3['volume'].rolling(20).mean()
    ds3 = ds3[ds3['datetime'] >= DATE_START][['datetime', 'vol_ma20']].reset_index(drop=True)

    # Normalise tz representation to string for merge key
    df['_dt_str']  = df['datetime'].astype(str)
    ds3['_dt_str'] = ds3['datetime'].astype(str)
    vol_map = ds3.set_index('_dt_str')['vol_ma20'].to_dict()
    df['vol_ma20'] = df['_dt_str'].map(vol_map)
    df = df.drop(columns=['_dt_str'])

    # Reorder: insert vol_ma20 after volume
    cols = df.columns.tolist()
    if 'vol_ma20' in cols:
        cols.remove('vol_ma20')
        vol_idx = cols.index('volume') + 1
        cols.insert(vol_idx, 'vol_ma20')
        df = df[cols]

    df.to_csv(csv_path, index=False)
    nan_count = df['vol_ma20'].isna().sum()
    print(f'  {stock:15s}  rows={len(df):6d}  vol_ma20_nan={nan_count}')


def add_vol_ma20_bajfinance():
    csv_path  = CSV_DIR / 'BAJFINANCE_5min.csv'
    chunk_files = sorted(TOOL_DIR.glob('mcp-kite-get_historical_data-*.txt'))

    # Parse all chunks to get full BAJFINANCE 2021+ candles
    all_candles = []
    for f in chunk_files:
        outer = json.loads(f.read_text(encoding='utf-8'))
        for item in outer:
            if item.get('type') == 'text':
                data = json.loads(item['text'])
                candles = data if isinstance(data, list) else data.get('candles', data.get('data', []))
                for c in candles:
                    if isinstance(c, dict):
                        all_candles.append({'datetime': c['date'], 'volume': c['volume']})

    if not all_candles:
        print('  BAJFINANCE  ERROR: no candles parsed from tool-results')
        return

    warm = pd.DataFrame(all_candles)
    warm['datetime'] = pd.to_datetime(warm['datetime'], utc=False)
    warm = warm.sort_values('datetime').drop_duplicates('datetime').reset_index(drop=True)
    warm['vol_ma20'] = warm['volume'].rolling(20).mean()
    warm = warm[warm['datetime'] >= DATE_START][['datetime', 'vol_ma20']].reset_index(drop=True)

    df = pd.read_csv(csv_path)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=False)

    warm['_dt_str'] = warm['datetime'].astype(str)
    df['_dt_str']   = df['datetime'].astype(str)
    vol_map = warm.set_index('_dt_str')['vol_ma20'].to_dict()
    df['vol_ma20'] = df['_dt_str'].map(vol_map)
    df = df.drop(columns=['_dt_str'])

    cols = df.columns.tolist()
    if 'vol_ma20' in cols:
        cols.remove('vol_ma20')
        vol_idx = cols.index('volume') + 1
        cols.insert(vol_idx, 'vol_ma20')
        df = df[cols]

    df.to_csv(csv_path, index=False)
    nan_count = df['vol_ma20'].isna().sum()
    print(f'  {"BAJFINANCE":15s}  rows={len(df):6d}  vol_ma20_nan={nan_count}')


# ── Run ────────────────────────────────────────────────────────────────────────
print('Adding vol_ma20 to all 30 CSVs...')
for stock in DS3_STOCKS:
    csv_path = CSV_DIR / f'{stock}_5min.csv'
    if not csv_path.exists():
        print(f'  {stock:15s}  SKIP — CSV not found')
        continue
    add_vol_ma20_ds3(stock)

add_vol_ma20_bajfinance()
print('\nDone.')
