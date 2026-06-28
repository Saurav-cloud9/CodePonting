"""
fetch_bajfinance_ds3.py
Fetches BAJFINANCE 5-min data (2015-02-02 to 2025-12-31) via Kite MCP
and saves as BAJFINANCE.parquet in DS3 directory.
Run once to fix the warm-up gap in rsi_macd_mfe.py.
"""

import subprocess, json, time, os, sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pytz

STOCK      = 'BAJFINANCE'
START_DATE = datetime(2015, 2, 2)
END_DATE   = datetime(2025, 12, 31)
CHUNK_DAYS = 100
SLEEP_CALL = 0.4
SLEEP_RETRY = 2.0

OUTPUT_DIR = Path(r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3')
IST = pytz.FixedOffset(330)


# ── Kite MCP client (same as ds3_build.py) ─────────────────────────────────

class KiteMCPClient:
    def __init__(self):
        self._id = 0
        NPX = r'C:\Program Files\nodejs\npx.cmd'
        self.proc = subprocess.Popen(
            [NPX, 'mcp-remote', 'https://mcp.kite.trade/mcp'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        time.sleep(3)
        self._initialize()

    def _next_id(self):
        self._id += 1; return self._id

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + '\n'); self.proc.stdin.flush()

    def _recv_matching(self, msg_id, timeout=30.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline().strip()
            if not line: time.sleep(0.05); continue
            try:
                resp = json.loads(line)
                if resp.get('id') == msg_id: return resp
            except json.JSONDecodeError: continue
        raise TimeoutError(f"No MCP response for id={msg_id}")

    def _request(self, method, params=None, timeout=30.0):
        msg_id = self._next_id()
        msg = {'jsonrpc': '2.0', 'method': method, 'id': msg_id}
        if params: msg['params'] = params
        self._send(msg)
        return self._recv_matching(msg_id, timeout=timeout)

    def _notify(self, method, params=None):
        msg = {'jsonrpc': '2.0', 'method': method}
        if params: msg['params'] = params
        self._send(msg)

    def _initialize(self):
        self._request('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'bajfin-fetcher', 'version': '1.0'},
        }, timeout=20)
        self._notify('notifications/initialized')
        time.sleep(0.5)

    def call_tool(self, name, arguments=None, timeout=30.0):
        resp = self._request('tools/call', {'name': name, 'arguments': arguments or {}}, timeout=timeout)
        if 'error' in resp: raise RuntimeError(f"MCP error [{name}]: {resp['error']}")
        for item in resp.get('result', {}).get('content', []):
            if item.get('type') == 'text':
                try: return json.loads(item['text'])
                except json.JSONDecodeError: return {'raw': item['text']}
        return resp.get('result', {})

    def close(self):
        try: self.proc.terminate(); self.proc.wait(timeout=5)
        except Exception: pass


# ── Helpers ─────────────────────────────────────────────────────────────────

def date_chunks(start, end, days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def candles_to_df(candles):
    if not candles:
        return pd.DataFrame(columns=['datetime','open','high','low','close','volume','oi'])
    rows = []
    for c in candles:
        dt_str, o, h, l, cl, vol, oi = c[0], c[1], c[2], c[3], c[4], c[5], c[6]
        dt = pd.to_datetime(dt_str, utc=False)
        if dt.tzinfo is None: dt = IST.localize(dt)
        else: dt = dt.astimezone(IST)
        rows.append({'datetime': dt, 'open': float(o), 'high': float(h),
                     'low': float(l), 'close': float(cl), 'volume': int(vol), 'oi': int(oi)})
    df = pd.DataFrame(rows)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
    return df.reset_index(drop=True)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching {STOCK} | {START_DATE.date()} -> {END_DATE.date()}")
    print("Starting Kite MCP client...")
    client = KiteMCPClient()
    print("MCP client ready.\n")

    try:
        # 1. Get instrument token
        print(f"Searching token for NSE:{STOCK}...")
        result = client.call_tool('search_instruments', {'query': f'NSE:{STOCK}'})
        instruments = result if isinstance(result, list) else result.get('data', result.get('instruments', []))
        token = None
        for inst in instruments:
            if inst.get('tradingsymbol') == STOCK and inst.get('exchange') == 'NSE' and inst.get('instrument_type') == 'EQ':
                token = inst.get('instrument_token') or inst.get('id'); break
        if token is None:
            for inst in instruments:
                if inst.get('exchange') == 'NSE': token = inst.get('instrument_token') or inst.get('id'); break
        if token is None:
            print("ERROR: token not found"); return
        print(f"Token: {token}\n")
        time.sleep(SLEEP_CALL)

        # 2. Fetch in 100-day chunks
        chunks = list(date_chunks(START_DATE, END_DATE, CHUNK_DAYS))
        print(f"Fetching {len(chunks)} chunks...")
        all_candles = []

        for i, (cs, ce) in enumerate(chunks):
            attempt = 0
            while attempt < 2:
                try:
                    res = client.call_tool('get_historical_data', {
                        'instrument_token': token,
                        'from_date': cs.strftime('%Y-%m-%d %H:%M:%S'),
                        'to_date':   ce.strftime('%Y-%m-%d %H:%M:%S'),
                        'interval':  '5minute',
                        'continuous': False,
                        'oi': True,
                    })
                    candles = res if isinstance(res, list) else res.get('candles', res.get('data', []))
                    if candles: all_candles.extend(candles)
                    if (i + 1) % 5 == 0 or i == len(chunks) - 1:
                        print(f"  chunk {i+1}/{len(chunks)} done — {len(all_candles)} candles total")
                    break
                except Exception as e:
                    err = str(e).lower()
                    if 'rate' in err or '429' in err:
                        print(f"  Rate limit chunk {i+1}, sleeping {SLEEP_RETRY}s...")
                        time.sleep(SLEEP_RETRY); attempt += 1
                    elif 'timeout' in err and attempt == 0:
                        time.sleep(1.0); attempt += 1
                    else:
                        print(f"  Chunk {i+1} error: {e} — skipping"); break
            time.sleep(SLEEP_CALL)

        if not all_candles:
            print("ERROR: no candles returned"); return

        # 3. Build DataFrame + validate + save
        df = candles_to_df(all_candles)
        df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)

        # Remove post-15:30 candles
        mask_post = df['datetime'].dt.time > pd.Timestamp('15:30').time()
        if mask_post.sum(): print(f"Removing {mask_post.sum()} post-market candles"); df = df[~mask_post].reset_index(drop=True)

        # OHLC validation
        mask_ohlc = ((df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) |
                     (df['low'] > df['open']) | (df['low'] > df['close']))
        if mask_ohlc.sum(): print(f"Removing {mask_ohlc.sum()} OHLC-violation rows"); df = df[~mask_ohlc].reset_index(drop=True)

        out_path = OUTPUT_DIR / f'{STOCK}.parquet'
        df.to_parquet(out_path, index=False)
        trading_days = df['datetime'].dt.date.nunique()
        print(f"\nSaved: {out_path}")
        print(f"Candles : {len(df):,}")
        print(f"Range   : {df['datetime'].iloc[0]} -> {df['datetime'].iloc[-1]}")
        print(f"Trading days: {trading_days}")

    finally:
        client.close()


if __name__ == '__main__':
    main()
