#!/usr/bin/env python3
"""
DS3 Build Script — Kite MCP 5-min Historical Data Fetcher
Fetches 5-min OHLCV+OI data for 30 FV1 stocks via Kite MCP subprocess.
Output: Algo_Trading/Framework_V1/data/historical/intraday_5min_DS3/
"""

import subprocess
import json
import time
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytz

# ─── Configuration ────────────────────────────────────────────────────────────

PYTHON = sys.executable
STOCKS = [
    'ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BANDHANBNK', 'BHARTIARTL',
    'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB', 'HDFCBANK', 'HINDALCO',
    'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'NATIONALUM',
    'NTPC', 'ONGC', 'PNB', 'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'VEDL', 'VI', 'WIPRO'
]

START_DATE  = datetime(2015, 2, 2)
END_DATE    = datetime(2026, 3, 2)
CHUNK_DAYS  = 100
SLEEP_CALL  = 0.4   # seconds between API calls
SLEEP_RETRY = 2.0   # seconds before retry on rate limit

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'Framework_V1/data/historical/intraday_5min_DS3'
LOG_FILE   = BASE_DIR / 'DS3_fetch_log.csv'

IST = pytz.FixedOffset(330)   # UTC+5:30 — matches existing schema

# ─── Schema (from existing Upstox parquets) ───────────────────────────────────
# Columns: datetime (datetime64[ns, pytz.FixedOffset(330)]), open, high, low,
#          close (float64), volume, oi (int64)
# Index  : plain RangeIndex (int64)

# ─── MCP subprocess client ────────────────────────────────────────────────────

class KiteMCPClient:
    """Minimal MCP JSON-RPC client over npx mcp-remote STDIO."""

    def __init__(self):
        self._id  = 0
        self.proc = None
        self._start()

    def _start(self):
        # Full path needed — npx not in Python's PATH on Windows
        NPX = r'C:\Program Files\nodejs\npx.cmd'
        self.proc = subprocess.Popen(
            [NPX, 'mcp-remote', 'https://mcp.kite.trade/mcp'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,   # suppress status lines
            text=True,
            bufsize=1,
        )
        time.sleep(3)   # wait for mcp-remote to establish connection
        self._initialize()

    def _next_id(self):
        self._id += 1
        return self._id

    def _send(self, msg: dict):
        line = json.dumps(msg) + '\n'
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def _recv_matching(self, msg_id: int, timeout: float = 30.0) -> dict:
        """Read stdout until we get a response matching msg_id."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
                if resp.get('id') == msg_id:
                    return resp
                # else: notification or other message — discard
            except json.JSONDecodeError:
                continue
        raise TimeoutError(f"No MCP response for id={msg_id} within {timeout}s")

    def _request(self, method: str, params: dict = None, timeout: float = 30.0) -> dict:
        msg_id = self._next_id()
        msg = {'jsonrpc': '2.0', 'method': method, 'id': msg_id}
        if params:
            msg['params'] = params
        self._send(msg)
        return self._recv_matching(msg_id, timeout=timeout)

    def _notify(self, method: str, params: dict = None):
        msg = {'jsonrpc': '2.0', 'method': method}
        if params:
            msg['params'] = params
        self._send(msg)

    def _initialize(self):
        self._request('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'ds3-fetcher', 'version': '1.0'},
        }, timeout=20)
        self._notify('notifications/initialized')
        time.sleep(0.5)   # give server a moment

    def call_tool(self, name: str, arguments: dict = None, timeout: float = 30.0) -> dict:
        resp = self._request('tools/call', {
            'name': name,
            'arguments': arguments or {},
        }, timeout=timeout)
        if 'error' in resp:
            raise RuntimeError(f"MCP tool error [{name}]: {resp['error']}")
        result = resp.get('result', {})
        # result.content is a list of TextContent objects
        content = result.get('content', [])
        for item in content:
            if item.get('type') == 'text':
                try:
                    return json.loads(item['text'])
                except json.JSONDecodeError:
                    return {'raw': item['text']}
        return result

    def close(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                pass

# ─── Helpers ──────────────────────────────────────────────────────────────────

def date_chunks(start: datetime, end: datetime, days: int):
    """Yield (chunk_start, chunk_end) pairs, each up to `days` days."""
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def candles_to_df(candles: list) -> pd.DataFrame:
    """Convert Kite candle list to DataFrame matching existing schema."""
    if not candles:
        return pd.DataFrame(columns=['datetime','open','high','low','close','volume','oi'])

    rows = []
    for c in candles:
        # Kite returns: [date_str, open, high, low, close, volume, oi]
        dt_str, o, h, l, cl, vol, oi = c[0], c[1], c[2], c[3], c[4], c[5], c[6]
        # Parse datetime — Kite returns ISO8601 with +05:30
        dt = pd.to_datetime(dt_str, utc=False)
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        rows.append({
            'datetime': dt,
            'open':     float(o),
            'high':     float(h),
            'low':      float(l),
            'close':    float(cl),
            'volume':   int(vol),
            'oi':       int(oi),
        })

    df = pd.DataFrame(rows)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
    df['open']     = df['open'].astype('float64')
    df['high']     = df['high'].astype('float64')
    df['low']      = df['low'].astype('float64')
    df['close']    = df['close'].astype('float64')
    df['volume']   = df['volume'].astype('int64')
    df['oi']       = df['oi'].astype('int64')
    df = df.reset_index(drop=True)
    return df


def load_log() -> dict:
    """Return dict of {stock: row} from existing log (for checkpointing)."""
    done = {}
    if LOG_FILE.exists():
        with open(LOG_FILE, newline='') as f:
            for row in csv.DictReader(f):
                done[row['stock']] = row
    return done


def append_log(row: dict):
    """Append one row to DS3_fetch_log.csv."""
    fieldnames = ['stock','status','candles_fetched','date_from','date_to','error']
    write_header = not LOG_FILE.exists()
    with open(LOG_FILE, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow(row)


def validate_and_save(stock: str, df: pd.DataFrame) -> dict:
    """Apply P2 + P3a checks, save parquet, return stats."""
    stats = {'post_mkt_removed': 0, 'ohlc_removed': 0}

    # P2: remove candles after 15:30 IST
    mask_post = df['datetime'].dt.time > pd.Timestamp('15:30').time()
    stats['post_mkt_removed'] = int(mask_post.sum())
    if stats['post_mkt_removed']:
        print(f"  ⚠  {stock}: removing {stats['post_mkt_removed']} post-market candles")
        df = df[~mask_post].reset_index(drop=True)

    # P3a: OHLC violations
    mask_ohlc = (
        (df['high'] < df['low'])  |
        (df['high'] < df['open']) |
        (df['high'] < df['close'])|
        (df['low']  > df['open']) |
        (df['low']  > df['close'])
    )
    stats['ohlc_removed'] = int(mask_ohlc.sum())
    if stats['ohlc_removed']:
        print(f"  ⚠  {stock}: removing {stats['ohlc_removed']} OHLC-violation rows")
        df = df[~mask_ohlc].reset_index(drop=True)

    # Save parquet
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f'{stock}.parquet'
    df.to_parquet(out_path, index=False)

    stats['candles'] = len(df)
    stats['date_from'] = str(df['datetime'].iloc[0]) if len(df) else 'N/A'
    stats['date_to']   = str(df['datetime'].iloc[-1]) if len(df) else 'N/A'
    return stats


# ─── Main ─────────────────────────────────────────────────────────────────────

def fetch_stock(client: KiteMCPClient, stock: str) -> dict:
    """Fetch all historical data for one stock. Returns log row dict."""

    # 1. Get instrument token
    print(f"\n[{stock}] Searching instrument token...")
    try:
        result = client.call_tool('search_instruments', {'query': f'NSE:{stock}'})
        # result may be a list or dict
        instruments = result if isinstance(result, list) else result.get('data', result.get('instruments', []))
        token = None
        for inst in instruments:
            if inst.get('tradingsymbol') == stock and inst.get('exchange') == 'NSE' and inst.get('instrument_type') == 'EQ':
                token = inst.get('instrument_token') or inst.get('id')
                break
        # Fallback: first NSE result
        if token is None:
            for inst in instruments:
                if inst.get('exchange') == 'NSE':
                    token = inst.get('instrument_token') or inst.get('id')
                    break
        if token is None:
            return {'stock': stock, 'status': 'SKIPPED', 'candles_fetched': 0,
                    'date_from': '', 'date_to': '', 'error': 'token not found'}
        print(f"  token={token}")
    except Exception as e:
        return {'stock': stock, 'status': 'ERROR', 'candles_fetched': 0,
                'date_from': '', 'date_to': '', 'error': f'search failed: {e}'}

    time.sleep(SLEEP_CALL)

    # 2. Fetch in 100-day chunks
    all_candles = []
    chunks = list(date_chunks(START_DATE, END_DATE, CHUNK_DAYS))
    print(f"  Fetching {len(chunks)} chunks...")

    for i, (cs, ce) in enumerate(chunks):
        from_str = cs.strftime('%Y-%m-%d %H:%M:%S')
        to_str   = ce.strftime('%Y-%m-%d %H:%M:%S')
        attempt  = 0
        while attempt < 2:
            try:
                res = client.call_tool('get_historical_data', {
                    'instrument_token': token,
                    'from_date':        from_str,
                    'to_date':          to_str,
                    'interval':         '5minute',
                    'continuous':       False,
                    'oi':               True,
                })
                candles = res if isinstance(res, list) else res.get('candles', res.get('data', []))
                if candles:
                    all_candles.extend(candles)
                if (i + 1) % 10 == 0 or i == len(chunks) - 1:
                    print(f"  chunk {i+1}/{len(chunks)} done — {len(all_candles)} candles so far")
                break
            except Exception as e:
                err_str = str(e).lower()
                if 'rate' in err_str or '429' in err_str:
                    print(f"  ⚠  Rate limit on chunk {i+1}, sleeping {SLEEP_RETRY}s...")
                    time.sleep(SLEEP_RETRY)
                    attempt += 1
                elif 'timeout' in err_str and attempt == 0:
                    print(f"  ⚠  Timeout on chunk {i+1}, retrying...")
                    time.sleep(1.0)
                    attempt += 1
                else:
                    print(f"  ✗  Chunk {i+1} error: {e} — skipping")
                    break

        time.sleep(SLEEP_CALL)

    if not all_candles:
        return {'stock': stock, 'status': 'EMPTY', 'candles_fetched': 0,
                'date_from': '', 'date_to': '', 'error': 'no candles returned'}

    # 3. Build DataFrame + validate + save
    df = candles_to_df(all_candles)
    df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)
    stats = validate_and_save(stock, df)

    trading_days = df['datetime'].dt.date.nunique()
    flag = ' ⚠️ LOW COVERAGE' if trading_days < 2000 else ''
    print(f"  ✅ {stock} — {stats['candles']} candles | {stats['date_from'][:10]} → {stats['date_to'][:10]} | {trading_days} trading days{flag}")

    return {
        'stock':          stock,
        'status':         'OK',
        'candles_fetched': stats['candles'],
        'date_from':      stats['date_from'][:10],
        'date_to':        stats['date_to'][:10],
        'error':          '',
    }


def write_validation_report(report_rows: list):
    """Write DS3_validation_report.txt."""
    report_path = BASE_DIR / 'DS3_validation_report.txt'
    header = f"{'Stock':<14} {'Candles':>8} {'Date From':>12} {'Date To':>12} {'PostMkt':>9} {'OHLC':>6}"
    sep    = '-' * len(header)
    lines  = ['DS3 VALIDATION REPORT', f'Generated: {datetime.now():%Y-%m-%d %H:%M:%S}', sep, header, sep]
    for r in report_rows:
        lines.append(
            f"{r['stock']:<14} {r.get('candles',0):>8} {r.get('date_from','N/A'):>12} "
            f"{r.get('date_to','N/A'):>12} {r.get('post_mkt',0):>9} {r.get('ohlc',0):>6}"
        )
    lines += [sep, f"Total stocks: {len(report_rows)}"]
    report_path.write_text('\n'.join(lines))
    print(f"\nValidation report saved → {report_path}")


def main():
    print("=" * 60)
    print("DS3 BUILD — Kite MCP 5-min Historical Data")
    print(f"Stocks : {len(STOCKS)}")
    print(f"Range  : {START_DATE.date()} → {END_DATE.date()}")
    print(f"Output : {OUTPUT_DIR}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load checkpoint
    done = load_log()
    completed = {s for s, r in done.items() if r.get('status') == 'OK'}
    if completed:
        print(f"\nCheckpoint: {len(completed)} stocks already done → {sorted(completed)}")
    remaining = [s for s in STOCKS if s not in completed]
    print(f"Remaining: {len(remaining)} stocks\n")

    # Start MCP client
    print("Starting Kite MCP client...")
    client = KiteMCPClient()
    print("MCP client ready.\n")

    report_rows      = []
    total_candles    = 0
    stocks_completed = len(completed)

    try:
        for stock in remaining:
            log_row = fetch_stock(client, stock)
            append_log(log_row)

            if log_row['status'] == 'OK':
                stocks_completed += 1
                total_candles    += int(log_row['candles_fetched'])

            report_rows.append({
                'stock':    stock,
                'candles':  log_row.get('candles_fetched', 0),
                'date_from':log_row.get('date_from', ''),
                'date_to':  log_row.get('date_to', ''),
                'post_mkt': 0,
                'ohlc':     0,
            })

    except KeyboardInterrupt:
        print("\n\n⚠  Interrupted — progress saved to DS3_fetch_log.csv")
    finally:
        client.close()

    if report_rows:
        write_validation_report(report_rows)

    print("\n" + "=" * 60)
    print(f"DS3 BUILD COMPLETE — {stocks_completed} stocks, {total_candles} candles")
    print("=" * 60)


if __name__ == '__main__':
    main()
