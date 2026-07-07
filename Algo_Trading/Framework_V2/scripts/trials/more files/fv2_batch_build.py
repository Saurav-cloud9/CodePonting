"""
fv2 Batch CSV Builder
Generates outcome-column CSVs for all 30 fv2 stocks:
  - 29 DS3 stocks (excluding VI)
  - BAJFINANCE via Kite MCP fetch

Output: Framework_V2/data/historical/csv/intraday_5min/
Columns per CSV: datetime, open, high, low, close, volume, ma20,
                 signal_type, exit_reason, raw_pnl, win
"""

import subprocess, json, time, sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import pytz

# ── Paths ─────────────────────────────────────────────────────────────────────
DS3_DIR  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V1/data/historical/intraday_5min_DS3')
OUT_DIR  = Path(r'c:/Users/Saurav/CodePonting/Algo_Trading/Framework_V2/data/historical/csv/intraday_5min')
BAJF_PARQUET = OUT_DIR / '_bajfinance_raw.parquet'   # temp
OUT_DIR.mkdir(parents=True, exist_ok=True)

DS3_STOCKS = [
    'ADANIPORTS', 'ASHOKLEY', 'AXISBANK', 'BANDHANBNK', 'BHARTIARTL',
    'CIPLA', 'COALINDIA', 'DABUR', 'DIVISLAB', 'HDFCBANK', 'HINDALCO',
    'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'NATIONALUM',
    'NTPC', 'ONGC', 'PNB', 'POWERGRID', 'RELIANCE', 'SBIN', 'SUNPHARMA',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'VEDL', 'WIPRO'   # VI excluded
]

DATE_START = '2022-01-01'
DATE_END   = '2025-12-31'
IST = pytz.FixedOffset(330)

# ── Signal detection (same logic as TATAMOTORS) ────────────────────────────────

def run_signals(df_raw: pd.DataFrame, stock: str) -> pd.DataFrame:
    df = df_raw.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)

    # MA20 on full history (warmup before 2022)
    df['ma20'] = df['close'].rolling(20).mean()

    # ATR14
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low']  - prev_close).abs()
    ], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14).mean()

    # Vol MA20
    df['vol_ma20'] = df['volume'].rolling(20).mean()

    # Slope: compute BEFORE date filter so pre-2022 MA history provides correct values
    # for the first bars of 2022 (if computed after filter, first 5 bars default to 'flat')
    df['slope'] = (df['ma20'] - df['ma20'].shift(5)) / df['ma20'] * 100

    # Filter to output range
    df = df[(df['datetime'] >= DATE_START) & (df['datetime'] <= DATE_END)].reset_index(drop=True)

    # Date col for EOD
    df['_date'] = df['datetime'].dt.date
    # EOD detection via datetime set — no positional index dependency (Bug 1 fix)
    eod_datetimes = set(df.groupby('_date')['datetime'].last())

    # Init outcome cols
    df['signal_type'] = None          # object dtype — accepts strings without FutureWarning
    df['exit_reason'] = None
    df['raw_pnl']     = np.nan
    df['win']         = np.nan

    n = len(df)
    i = 0
    while i < n:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1
            continue
        if row['low'] > row['ma20']:
            i += 1
            continue

        touch_idx  = i
        touch_date = row['_date']

        # Bounce: touch or next 1-3 candles, same day
        bounce_idx = None
        for j in range(touch_idx, min(touch_idx + 4, n)):
            b = df.iloc[j]
            if b['_date'] != touch_date:
                break
            if b['close'] > b['ma20'] and b['volume'] >= 1.2 * b['vol_ma20']:
                bounce_idx = j
                break

        if bounce_idx is None or bounce_idx + 1 >= n:
            i += 1
            continue

        entry_idx   = bounce_idx + 1
        entry_row   = df.iloc[entry_idx]
        entry_date  = entry_row['_date']

        # Same-day guard: entry must be on same day as touch/bounce (intraday only)
        if entry_date != touch_date:
            i += 1
            continue

        entry_price = entry_row['open']
        atr         = df.iloc[touch_idx]['atr14']
        sl          = entry_price - 2.5 * atr
        target      = entry_price + 4.5 * atr

        # Slope: read pre-computed column (uses pre-2022 history, no boundary issue)
        slope_val = df.iloc[touch_idx]['slope']
        slope_val = slope_val if pd.notna(slope_val) else 0.0
        sig_type  = 'R' if slope_val > 0.05 else ('F' if slope_val < -0.05 else 'L')

        # Exit
        exit_reason = exit_price = None
        for k in range(entry_idx, n):
            krow = df.iloc[k]
            if krow['_date'] != entry_date:
                # Walked into next day — k-1 was last bar of entry_date
                exit_reason = 'EOD'
                exit_price  = df.iloc[k - 1]['close']
                break
            # Convention: target checked before SL — if both hit on same bar, target wins (Bug 2 note)
            if krow['high'] >= target:
                exit_reason = 'target'
                exit_price  = target
                break
            if krow['low'] <= sl:
                exit_reason = 'stoploss'
                exit_price  = sl
                break
            if krow['datetime'] in eod_datetimes:
                # Last bar of entry_date — exit at close
                exit_reason = 'EOD'
                exit_price  = krow['close']
                break

        if exit_reason is None:
            # Should never reach here — EOD always catches last bar; advance past entry (Bug 8 fix)
            i = k + 1
            continue

        df.at[entry_idx, 'signal_type'] = sig_type
        df.at[entry_idx, 'exit_reason']  = exit_reason
        df.at[entry_idx, 'raw_pnl']      = exit_price - entry_price
        df.at[entry_idx, 'win']          = 1 if exit_reason == 'target' else 0

        i = k + 1

    # Drop temp cols, keep output cols
    out = df.drop(columns=['atr14', 'vol_ma20', '_date', 'slope'])
    return out


# ── Kite MCP client (minimal) ──────────────────────────────────────────────────

class KiteMCPClient:
    def __init__(self):
        self._id  = 0
        self.proc = None
        self._start()

    def _start(self):
        NPX = r'C:\Program Files\nodejs\npx.cmd'
        self.proc = subprocess.Popen(
            [NPX, 'mcp-remote', 'https://mcp.kite.trade/mcp'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        time.sleep(4)
        self._initialize()

    def _next_id(self):
        self._id += 1
        return self._id

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + '\n')
        self.proc.stdin.flush()

    def _recv(self, msg_id, timeout=60.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            try:
                resp = json.loads(line.strip())
                if resp.get('id') == msg_id:
                    return resp
            except json.JSONDecodeError:
                continue
        raise TimeoutError(f"No response for id={msg_id}")

    def _request(self, method, params=None, timeout=60.0):
        mid = self._next_id()
        msg = {'jsonrpc': '2.0', 'method': method, 'id': mid}
        if params:
            msg['params'] = params
        self._send(msg)
        return self._recv(mid, timeout=timeout)

    def _notify(self, method, params=None):
        msg = {'jsonrpc': '2.0', 'method': method}
        if params:
            msg['params'] = params
        self._send(msg)

    def _initialize(self):
        self._request('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'fv2-builder', 'version': '1.0'},
        }, timeout=20)
        self._notify('notifications/initialized')
        time.sleep(0.5)

    def call_tool(self, name, arguments=None, timeout=60.0):
        resp = self._request('tools/call', {
            'name': name, 'arguments': arguments or {}
        }, timeout=timeout)
        if 'error' in resp:
            raise RuntimeError(f"MCP error [{name}]: {resp['error']}")
        content = resp.get('result', {}).get('content', [])
        for item in content:
            if item.get('type') == 'text':
                try:
                    return json.loads(item['text'])
                except json.JSONDecodeError:
                    return {'raw': item['text']}
        return {}

    def close(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                pass


def fetch_bajfinance(client: KiteMCPClient) -> pd.DataFrame:
    print("\n[BAJFINANCE] Searching instrument token...")
    result = client.call_tool('search_instruments', {'query': 'NSE:BAJFINANCE'})
    instruments = result if isinstance(result, list) else result.get('data', result.get('instruments', []))
    token = None
    for inst in instruments:
        if inst.get('tradingsymbol') == 'BAJFINANCE' and inst.get('exchange') == 'NSE':
            token = inst.get('instrument_token') or inst.get('id')
            break
    if token is None:
        raise RuntimeError("BAJFINANCE token not found")
    print(f"  token={token}")

    # Fetch 2021-01-01 to 2025-12-31 (warmup from 2021 for MA20)
    start = datetime(2021, 1, 1)
    end   = datetime(2025, 12, 31)
    chunk = 100
    all_candles = []

    cur = start
    chunks = []
    while cur < end:
        nxt = min(cur + timedelta(days=chunk), end)
        chunks.append((cur, nxt))
        cur = nxt + timedelta(days=1)

    print(f"  Fetching {len(chunks)} chunks...")
    for i, (cs, ce) in enumerate(chunks):
        for attempt in range(2):
            try:
                res = client.call_tool('get_historical_data', {
                    'instrument_token': token,
                    'from_date':        cs.strftime('%Y-%m-%d %H:%M:%S'),
                    'to_date':          ce.strftime('%Y-%m-%d %H:%M:%S'),
                    'interval':         '5minute',
                    'continuous':       False,
                    'oi':               True,
                }, timeout=60)
                candles = res if isinstance(res, list) else res.get('candles', res.get('data', []))
                if candles:
                    all_candles.extend(candles)
                if (i + 1) % 5 == 0 or i == len(chunks) - 1:
                    print(f"  chunk {i+1}/{len(chunks)} — {len(all_candles):,} candles")
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(2)
                else:
                    print(f"  ✗ chunk {i+1} error: {e}")
        time.sleep(0.4)

    if not all_candles:
        raise RuntimeError("No candles returned for BAJFINANCE")

    # Build DataFrame
    rows = []
    for c in all_candles:
        dt = pd.to_datetime(c[0], utc=False)
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        rows.append({'datetime': dt, 'open': float(c[1]), 'high': float(c[2]),
                     'low': float(c[3]), 'close': float(c[4]), 'volume': int(c[5])})

    df = pd.DataFrame(rows)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
    df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)
    # Remove post-market
    df = df[df['datetime'].dt.time <= pd.Timestamp('15:30').time()].reset_index(drop=True)
    print(f"  BAJFINANCE: {len(df):,} raw candles fetched")
    return df


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    summary = []

    # ── Step 1: Process 29 DS3 stocks ─────────────────────────────────────────
    print("=" * 60)
    print("STEP 1 — Processing 29 DS3 stocks")
    print("=" * 60)

    for stock in DS3_STOCKS:
        out_path = OUT_DIR / f'{stock}_5min.csv'
        if out_path.exists():
            # Already done — just read counts
            existing = pd.read_csv(out_path)
            trades = existing.dropna(subset=['signal_type'])
            r = (trades['signal_type'] == 'R').sum()
            f = (trades['signal_type'] == 'L').sum()
            d = (trades['signal_type'] == 'F').sum()
            print(f"  {stock:15s} SKIP (exists) | signals={len(trades):4d} | R={r} L={f} F={d}")
            summary.append((stock, len(existing), len(trades), r, f, d))
            continue

        parquet = DS3_DIR / f'{stock}.parquet'
        if not parquet.exists():
            print(f"  {stock:15s} ERROR — parquet not found")
            summary.append((stock, 0, 0, 0, 0, 0))
            continue

        try:
            df_raw = pd.read_parquet(parquet)
            df_out = run_signals(df_raw, stock)
            df_out.to_csv(out_path, index=False)
            trades = df_out.dropna(subset=['signal_type'])
            r = (trades['signal_type'] == 'R').sum()
            f = (trades['signal_type'] == 'L').sum()
            d = (trades['signal_type'] == 'F').sum()
            print(f"  {stock:15s} done | rows={len(df_out):6,} | signals={len(trades):4d} | R={r} L={f} F={d}")
            summary.append((stock, len(df_out), len(trades), r, f, d))
        except Exception as e:
            print(f"  {stock:15s} ERROR: {e}")
            summary.append((stock, 0, 0, 0, 0, 0))

    # ── Step 2: Fetch + process BAJFINANCE ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2 — Fetching BAJFINANCE via Kite MCP")
    print("=" * 60)

    out_path = OUT_DIR / 'BAJFINANCE_5min.csv'
    if out_path.exists():
        existing = pd.read_csv(out_path)
        trades = existing.dropna(subset=['signal_type'])
        r = (trades['signal_type'] == 'rising').sum()
        f = (trades['signal_type'] == 'flat').sum()
        d = (trades['signal_type'] == 'falling').sum()
        print(f"  BAJFINANCE SKIP (exists) | signals={len(trades):4d} | R={r} L={f} F={d}")
        summary.append(('BAJFINANCE', len(existing), len(trades), r, f, d))
    else:
        client = KiteMCPClient()
        try:
            df_raw = fetch_bajfinance(client)
            df_out = run_signals(df_raw, 'BAJFINANCE')
            df_out.to_csv(out_path, index=False)
            trades = df_out.dropna(subset=['signal_type'])
            r = (trades['signal_type'] == 'R').sum()
            f = (trades['signal_type'] == 'L').sum()
            d = (trades['signal_type'] == 'F').sum()
            print(f"  BAJFINANCE done | rows={len(df_out):6,} | signals={len(trades):4d} | R={r} L={f} F={d}")
            summary.append(('BAJFINANCE', len(df_out), len(trades), r, f, d))
        except Exception as e:
            print(f"  BAJFINANCE ERROR: {e}")
            summary.append(('BAJFINANCE', 0, 0, 0, 0, 0))
        finally:
            client.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"{'Stock':15s} {'Total':>7} {'Signals':>8} {'R':>7} {'L':>6} {'F':>8}")
    print("-" * 60)
    total_sig = 0
    for stock, rows, sig, r, f, d in sorted(summary):
        print(f"{stock:15s} {rows:7,} {sig:8,} {r:7,} {f:6,} {d:8,}")
        total_sig += sig
    print("-" * 60)
    print(f"{'TOTAL':15s} {'':>7} {total_sig:8,}")
    print(f"\nCSVs saved to: {OUT_DIR}")


if __name__ == '__main__':
    main()
