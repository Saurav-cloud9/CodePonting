"""
MA Bounce LONG — 30 stocks · 2015-2025 · DS3
Fixed params: SL=1.5x ATR, TP=3.5x ATR
Metrics: PF + ZPF (Zerodha charges) + ZSh(D) (daily Sharpe after charges)
Per-stock breakdown + overall + year-wise
"""
import sys, io, os, glob
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
SL_MULT    = 1.5
TP_MULT    = 3.5
MAX_TB_GAP = 3
EOD_HOUR   = 15


def zerodha_long(entry, exit_px):
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = exit_px * 0.00025      # STT on sell side (exit for long)
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = entry * 0.000003       # stamp duty on buy side (entry for long)
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load_arrays(path):
    df = pd.read_parquet(path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['year'] = df['datetime'].dt.year
    return {
        'high':  df['high'].values,  'low':   df['low'].values,
        'open_': df['open'].values,  'close': df['close'].values,
        'ma20':  df['ma20'].values,  'atr14': df['atr14'].values,
        'hour':  df['hour'].values,  'date':  df['date'].values,
        'year':  df['year'].values,  'n':     len(df),
    }


def run_stock(arr):
    high, low, open_, close = arr['high'], arr['low'], arr['open_'], arr['close']
    ma20, atr14 = arr['ma20'], arr['atr14']
    hour, date, year = arr['hour'], arr['date'], arr['year']
    n = arr['n']
    trades = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        if low[i] <= ma20[i] and hour[i] < EOD_HOUR:
            touch_date = date[i]; atr = atr14[i]; bounce = -1
            for j in range(i, min(i + MAX_TB_GAP + 1, n)):
                if date[j] != touch_date or hour[j] >= EOD_HOUR: break
                if close[j] > ma20[j]: bounce = j; break
            if bounce < 0: i += 1; continue
            ei = bounce + 1
            if ei >= n or date[ei] != touch_date: i += 1; continue
            entry = open_[ei]; sl = entry - SL_MULT * atr; tp = entry + TP_MULT * atr
            k = ei
            for k in range(ei, n):
                if date[k] != touch_date:
                    exit_px = close[k - 1]; pnl = exit_px - entry; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; pnl = exit_px - entry; break
                if low[k] <= sl:
                    exit_px = sl; pnl = exit_px - entry; break
                if high[k] >= tp:
                    exit_px = tp; pnl = exit_px - entry; break
            trades.append({'pnl': pnl, 'entry': entry, 'exit_px': exit_px,
                           'year': year[ei], 'date': pd.Timestamp(date[ei])})
            i = k + 1
        else:
            i += 1
    return trades


def calc_metrics(trades):
    if not trades: return 0, 0.0, 0.0, 0.0
    tdf = pd.DataFrame(trades)
    tdf['zpnl'] = tdf.apply(lambda r: r['pnl'] - zerodha_long(r['entry'], r['exit_px']), axis=1)
    gp = tdf[tdf['pnl'] > 0]['pnl'].sum();  gl = -tdf[tdf['pnl'] <= 0]['pnl'].sum()
    zw = tdf[tdf['zpnl'] > 0]['zpnl'].sum(); zl = -tdf[tdf['zpnl'] <= 0]['zpnl'].sum()
    pf  = round(gp / gl, 3) if gl > 0 else 0.0
    zpf = round(zw / zl, 3) if zl > 0 else 0.0
    daily = tdf.set_index('date').resample('D')['zpnl'].sum()
    daily = daily[daily != 0]
    zshd = round((daily.mean() / daily.std()) * np.sqrt(252), 3) if len(daily) > 1 else 0.0
    return len(tdf), pf, zpf, zshd


# ── Run all stocks ─────────────────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks...')
all_trades = []; rows = []

for f in files:
    sym = os.path.basename(f).replace('.parquet', '')
    arr = load_arrays(f)
    trades = run_stock(arr)
    if not trades: continue
    n, pf, zpf, zshd = calc_metrics(trades)
    prof_wr = sum(1 for t in trades if t['pnl'] > 0) / n * 100
    rows.append({'Symbol': sym, 'N': n,
                 'Prof_WR%': round(prof_wr, 1),
                 'PF': pf, 'ZPF': zpf, 'ZSh(D)': zshd})
    all_trades.extend(trades)

print(pd.DataFrame(rows).sort_values('ZPF', ascending=False).reset_index(drop=True).to_string(index=False))

# ── Overall summary ────────────────────────────────────────────────────────────
print()
n_all, pf_all, zpf_all, zshd_all = calc_metrics(all_trades)
prof_wr_all = sum(1 for t in all_trades if t['pnl'] > 0) / n_all * 100
print(f"TOTAL  N={n_all:,}  Prof_WR={prof_wr_all:.1f}%  PF={pf_all}  ZPF={zpf_all}  ZSh(D)={zshd_all}")

# ── Year-wise breakdown ────────────────────────────────────────────────────────
print()
all_df = pd.DataFrame(all_trades)
all_df['zpnl'] = all_df.apply(lambda r: r['pnl'] - zerodha_long(r['entry'], r['exit_px']), axis=1)
print(f"{'Year':<6} {'N':>6}  {'PF':>6}  {'ZPF':>6}  {'ZSh(D)':>8}")
for yr, g in all_df.groupby('year'):
    gp_y = g[g['pnl'] > 0]['pnl'].sum();  gl_y = abs(g[g['pnl'] <= 0]['pnl'].sum())
    zw_y = g[g['zpnl'] > 0]['zpnl'].sum(); zl_y = abs(g[g['zpnl'] <= 0]['zpnl'].sum())
    pf_y  = round(gp_y / gl_y, 3) if gl_y > 0 else 0.0
    zpf_y = round(zw_y / zl_y, 3) if zl_y > 0 else 0.0
    daily_y = g.set_index('date').resample('D')['zpnl'].sum()
    daily_y = daily_y[daily_y != 0]
    zshd_y = round((daily_y.mean() / daily_y.std()) * np.sqrt(252), 3) if len(daily_y) > 1 else 0.0
    flag = '✅' if zpf_y >= 1.0 else ('🟡' if zpf_y >= 0.9 else '❌')
    print(f"  {yr}  {len(g):>6}  {pf_y:>6.3f}  {zpf_y:>6.3f}  {zshd_y:>8.3f}  {flag}")
