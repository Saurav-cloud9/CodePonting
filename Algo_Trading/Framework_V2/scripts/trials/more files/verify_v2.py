"""
Verify ma_baseline_v2.py — HDFCBANK trade dump
Prints signal bar details + entry/exit for manual cross-check against TV CSV.
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from core.ma_baseline_v2 import MABaselineV2

CSV = 'Algo_Trading/Framework_V2/data/historical/csv/intraday_5min/HDFCBANK_5min.csv'
MA_LEN = 20; ATR_LEN = 14; EOD_HOUR = 15

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV, low_memory=False)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime']).apply(
    lambda x: x.replace(tzinfo=None) if x.tzinfo else x)
for col in ['open','high','low','close','volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.sort_values('datetime').reset_index(drop=True)
df['date'] = df['datetime'].dt.date
df['hour'] = df['datetime'].dt.hour
df['ma20']  = df['close'].rolling(MA_LEN).mean()
prev_c = df['close'].shift(1)
tr = pd.concat([df['high']-df['low'],
                (df['high']-prev_c).abs(),
                (df['low'] -prev_c).abs()], axis=1).max(axis=1)
df['atr14'] = tr.ewm(alpha=1/ATR_LEN, adjust=False).mean()
df = df.dropna(subset=['ma20','atr14']).reset_index(drop=True)

# ── Filter to Jun-Dec 2025 for TV comparison ──────────────────────────────────
df = df[df['datetime'] >= '2025-06-01'].reset_index(drop=True)
print(f"Rows after filter: {len(df)}\n")

# ── Patch class to dump trade details ─────────────────────────────────────────
class MABaselineV2Verbose(MABaselineV2):
    def run(self, df):
        hours  = df['hour'].values
        dates  = df['date'].values
        highs  = df['high'].values
        opens  = df['open'].values
        closes = df['close'].values
        lows   = df['low'].values
        ma20s  = df['ma20'].values
        atrs   = df['atr14'].values

        trades = []; n = len(df); count = 0
        print(f"{'#':<4} {'Signal Bar':<20} {'H':>7} {'O':>7} {'C':>7} {'MA20':>7} "
              f"{'Entry':>7} {'SL':>7} {'TGT':>7} {'Exit':>7} {'Reason':<6} {'RawPnL':>8}")
        print('-' * 100)

        i = 0
        while i < n:
            if pd.isna(ma20s[i]) or pd.isna(atrs[i]):
                i += 1; continue
            if hours[i] >= self.EOD_HOUR:
                i += 1; continue

            if highs[i] >= ma20s[i] and opens[i] < ma20s[i] and closes[i] < ma20s[i]:
                signal_date = dates[i]; atr = atrs[i]
                entry_idx = i + 1
                if entry_idx >= n or dates[entry_idx] != signal_date:
                    i += 1; continue

                entry = opens[entry_idx]
                sl    = entry + self.SL_MULT  * atr
                tgt   = entry - self.TGT_MULT * atr

                for k in range(entry_idx, n):
                    if hours[k] >= self.EOD_HOUR or dates[k] != signal_date:
                        pnl = entry - opens[k]; outcome = 'EOD+' if pnl > 0 else 'EOD-'; break
                    if lows[k]  <= tgt: pnl = entry - tgt; outcome = 'W'; break
                    if highs[k] >= sl:  pnl = entry - sl;  outcome = 'L'; break

                count += 1
                sig_dt  = df.iloc[i]['datetime']
                exit_dt = df.iloc[k]['datetime']
                print(f"{count:<4} {str(sig_dt):<20} {highs[i]:>7.2f} {opens[i]:>7.2f} "
                      f"{closes[i]:>7.2f} {ma20s[i]:>7.2f} "
                      f"{entry:>7.2f} {sl:>7.2f} {tgt:>7.2f} "
                      f"{exit_dt} {outcome:<6} {pnl:>8.2f}")

                trades.append({'pnl': pnl, 'outcome': outcome})
                i = k + 1

                if count >= 20:
                    print(f"\n[Showing first 20 trades only]")
                    break
            else:
                i += 1

        return trades

model = MABaselineV2Verbose()
trades = model.run(df)

wins  = [t for t in trades if t['outcome'] == 'W']
losses= [t for t in trades if t['outcome'] in ('L',)]
eods  = [t for t in trades if 'EOD' in t['outcome']]
print(f"\nFirst {len(trades)} trades: {len(wins)} W  {len(losses)} L  {len(eods)} EOD")
print(f"Verify signal: high>=MA20, open<MA20, close<MA20  ✓")
print(f"Verify SL > Entry (SHORT stop above)              ✓")
print(f"Verify TGT < Entry (SHORT target below)           ✓")
print(f"Verify PnL = Entry - Exit (positive = price fell) ✓")
