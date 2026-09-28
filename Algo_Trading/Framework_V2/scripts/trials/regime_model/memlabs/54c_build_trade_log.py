"""
Step 54c (file 1/3) — build a full per-trade log for the locked FLAGSHIP_6BCEH_SHORT_VWAP_RSI60
combo (SL=1.5 / TP=4.5 / RSI>60), for regime-feature screening.

Reuses add_vwap / add_rsi_wilder / zerodha_charge from strategies/flagship/11_..._rsi.py
(the frozen engine) — does NOT touch that file. Adds what the aggregate engine doesn't
track: stock symbol + full signal-bar datetime per trade, needed to join against daily
regime features later.

Per §4's design spec (54_...baseline.md): target logged as BOTH continuous zpnl (leads)
and binary win/loss (fast screen) — win := zpnl > 0. Signal-bar datetime used (not the
entry bar) — that's the decision point a regime filter would gate at.

Output: 54c_trade_log.csv — one row per trade:
  symbol, signal_dt, entry_dt, exit_dt, entry_px, exit_px, exit_type, pnl, zpnl, win
  (exit_dt added 2026-09-19 for the hedge-overlay side-thread — was already computed
  internally, just wasn't exported before)
"""
import sys, io, types, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np

ENGINE = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/strategies/flagship/11_6bceh_short_vwap_rsi.py'
DATA_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SL, TP, RSI_THRESH = 1.5, 4.5, 60
WINDOW = 6
LAST_TOUCH_TIME = None   # set below from engine module
ENTRY_CUTOFF_TIME = None
EOD_HOUR = 15

with open(ENGINE) as f:
    src = f.read().split('# ── MAIN')[0]
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n", '')
eng = types.ModuleType('eng'); eng.__dict__['__file__'] = ENGINE
exec(compile(src, ENGINE, 'exec'), eng.__dict__)
LAST_TOUCH_TIME = eng.LAST_TOUCH_TIME
ENTRY_CUTOFF_TIME = eng.ENTRY_CUTOFF_TIME


def load_stocks_with_symbol():
    stocks = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet'))):
        symbol = os.path.splitext(os.path.basename(f))[0]
        df = pd.read_parquet(f)
        df['datetime'] = pd.to_datetime(df['datetime'])
        if df['datetime'].dt.tz is not None:
            df['datetime'] = df['datetime'].dt.tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'volume', 'atr14']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['time'] = df['datetime'].dt.time
        df = eng.add_vwap(df)
        df = eng.add_rsi_wilder(df)
        stocks.append({
            'symbol': symbol,
            'open': df['open'].values, 'high': df['high'].values, 'low': df['low'].values,
            'close': df['close'].values, 'atr14': df['atr14'].values,
            'vwap': df['vwap'].values, 'rsi': df['rsi'].values,
            'hour': df['hour'].values, 'date': df['date'].values, 'time': df['time'].values,
            'datetime': df['datetime'].values, 'n': len(df),
        })
    return stocks


def run_combo_logged(stocks, sl_m, tp_m, rsi_thresh):
    records = []
    for s in stocks:
        symbol = s['symbol']
        close = s['close']; high = s['high']; low = s['low']
        open_ = s['open']; atr = s['atr14']; vwap = s['vwap']; rsi = s['rsi']
        hour = s['hour']; date = s['date']; time_ = s['time']; dt = s['datetime']; n = s['n']

        i = WINDOW - 1
        while i < n:
            if (np.isnan(atr[i]) or np.isnan(vwap[i]) or np.isnan(rsi[i])
                    or time_[i] > LAST_TOUCH_TIME):
                i += 1; continue
            window = close[i - WINDOW + 1: i + 1]
            if np.any(np.isnan(window)) or close[i] < np.max(window):
                i += 1; continue
            if not (close[i] < vwap[i]):
                i += 1; continue
            if not (rsi[i] > rsi_thresh):
                i += 1; continue
            ei = i + 1
            if ei >= n or date[ei] != date[i] or time_[ei] > ENTRY_CUTOFF_TIME:
                i += 1; continue
            entry_px = open_[ei]
            if np.isnan(entry_px):
                i += 1; continue
            sl = entry_px + sl_m * atr[i]
            tp = entry_px - tp_m * atr[i]
            trade_date = date[i]
            k = ei
            exit_px = entry_px; exit_dt = trade_date; etype = 'EOD'
            while k < n:
                if date[k] != trade_date:
                    exit_px = close[k - 1]; exit_dt = date[k - 1]; etype = 'EOD'; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; exit_dt = date[k]; etype = 'EOD'; break
                if high[k] >= sl:
                    exit_px = sl; exit_dt = date[k]; etype = 'SL'; break
                if low[k] <= tp:
                    exit_px = tp; exit_dt = date[k]; etype = 'TP'; break
                k += 1
            else:
                exit_px = close[k - 1]; exit_dt = date[k - 1]; etype = 'EOD'

            pnl = entry_px - exit_px
            zpnl = pnl - eng.zerodha_charge(entry_px, exit_px)
            if np.isfinite(pnl) and np.isfinite(zpnl):
                records.append(dict(
                    symbol=symbol, signal_dt=dt[i], entry_dt=dt[ei], exit_dt=exit_dt,
                    entry_px=round(float(entry_px), 2), exit_px=round(float(exit_px), 2),
                    exit_type=etype, pnl=round(float(pnl), 4), zpnl=round(float(zpnl), 4),
                    win=int(zpnl > 0),
                ))
            i = k + 1
    return records


print(f'Building trade log at SL={SL}/TP={TP}/RSI>{RSI_THRESH}...')
stocks = load_stocks_with_symbol()
print(f'Loaded {len(stocks)} stocks (+symbol). Running combo...')
records = run_combo_logged(stocks, SL, TP, RSI_THRESH)
df = pd.DataFrame(records).sort_values('signal_dt').reset_index(drop=True)

out = os.path.join(SCRIPT_DIR, '54c_trade_log.csv')
df.to_csv(out, index=False)

n = len(df)
win_rate = df['win'].mean() * 100
print(f'\n{n:,} trades logged -> {out}')
print(f'Win rate (zpnl>0): {win_rate:.1f}%')
print(f'Exit mix: ' + ', '.join(f'{k}={v}' for k, v in df["exit_type"].value_counts().items()))
print(f'net_zpnl (sanity check vs master CSV -2436.26): {df["zpnl"].sum():.2f}')
print(f'date range: {df["signal_dt"].min()} -> {df["signal_dt"].max()}')
print('\nDone.')
