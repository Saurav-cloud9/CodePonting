"""
Fetch BAJFINANCE 5-min data from Kite MCP (2021-01-01 to 2025-12-31)
and save as parquet to Framework_V2/data/historical/parquet/BAJFINANCE.parquet
2021 included for MA20 warmup.
"""

import subprocess, json, time, sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pytz

TOKEN      = 81153
START_DATE = datetime(2021, 1, 1)
END_DATE   = datetime(2025, 12, 31)
CHUNK_DAYS = 60
SLEEP_CALL = 0.5
NPX        = r'C:\Program Files\nodejs\npx.cmd'
IST        = pytz.FixedOffset(330)
OUT_DIR    = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/parquet')
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE   = OUT_DIR / 'BAJFINANCE.parquet'

class KiteMCPClient:
    def __init__(self):
        self._id = 0
        self.proc = subprocess.Popen(
            [NPX, 'mcp-remote', 'https://mcp.kite.trade/mcp'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1
        )
        time.sleep(4)
        self._initialize()

    def _next_id(self):
        self._id += 1
        return self._id

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + '\n')
        self.proc.stdin.flush()

    def _recv(self, msg_id, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.05); continue
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                if r.get('id') == msg_id:
                    return r
            except json.JSONDecodeError:
                continue
        raise TimeoutError(f'No response for id={msg_id}')

    def _req(self, method, params=None, timeout=30):
        mid = self._next_id()
        msg = {'jsonrpc': '2.0', 'method': method, 'id': mid}
        if params: msg['params'] = params
        self._send(msg)
        return self._recv(mid, timeout)

    def _notify(self, method, params=None):
        msg = {'jsonrpc': '2.0', 'method': method}
        if params: msg['params'] = params
        self._send(msg)

    def _initialize(self):
        self._req('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'bajfinance-fetcher', 'version': '1.0'},
        }, timeout=20)
        self._notify('notifications/initialized')
        time.sleep(0.5)

    def call_tool(self, name, arguments=None, timeout=30):
        resp = self._req('tools/call', {'name': name, 'arguments': arguments or {}}, timeout)
        if 'error' in resp:
            raise RuntimeError(f'MCP error [{name}]: {resp["error"]}')
        for item in resp.get('result', {}).get('content', []):
            if item.get('type') == 'text':
                try:    return json.loads(item['text'])
                except: return {'raw': item['text']}
        return {}

    def close(self):
        try: self.proc.terminate(); self.proc.wait(timeout=5)
        except: pass


def chunks(start, end, days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def candles_to_df(candles):
    rows = []
    for c in candles:
        dt = pd.to_datetime(c[0], utc=False)
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        rows.append({'datetime': dt, 'open': float(c[1]), 'high': float(c[2]),
                     'low': float(c[3]), 'close': float(c[4]),
                     'volume': int(c[5]), 'oi': int(c[6])})
    df = pd.DataFrame(rows)
    if df.empty: return df
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
    return df.reset_index(drop=True)


print('Starting Kite MCP client...')
client = KiteMCPClient()
print('Connected.\n')

all_candles = []
chunk_list  = list(chunks(START_DATE, END_DATE, CHUNK_DAYS))
print(f'Fetching BAJFINANCE (token={TOKEN}) — {len(chunk_list)} chunks...')

for i, (cs, ce) in enumerate(chunk_list):
    from_str = cs.strftime('%Y-%m-%d %H:%M:%S')
    to_str   = ce.strftime('%Y-%m-%d %H:%M:%S')
    for attempt in range(2):
        try:
            res = client.call_tool('get_historical_data', {
                'instrument_token': TOKEN,
                'from_date': from_str,
                'to_date':   to_str,
                'interval':  '5minute',
                'continuous': False,
                'oi': True,
            }, timeout=60)
            candles = res if isinstance(res, list) else res.get('candles', res.get('data', []))
            if candles:
                all_candles.extend(candles)
            if (i + 1) % 5 == 0 or i == len(chunk_list) - 1:
                print(f'  chunk {i+1}/{len(chunk_list)} done — {len(all_candles):,} candles')
            break
        except Exception as e:
            if attempt == 0:
                print(f'  retry chunk {i+1}: {e}')
                time.sleep(1)
            else:
                print(f'  skip chunk {i+1}: {e}')
    time.sleep(SLEEP_CALL)

client.close()

if not all_candles:
    print('ERROR: no candles returned'); sys.exit(1)

df = candles_to_df(all_candles)
df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)
df.to_parquet(OUT_FILE, index=False)
print(f'\nSaved: {OUT_FILE}')
print(f'Rows : {len(df):,}  |  {df["datetime"].iloc[0]}  →  {df["datetime"].iloc[-1]}')
