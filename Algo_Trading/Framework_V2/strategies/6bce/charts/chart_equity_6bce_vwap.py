import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np, glob, os, pandas as pd
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

plt.style.use('dark_background')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
EOD_HOUR = 15; WINDOW = 6
SL_M = 6.0; TP_M = 6.0


def zerodha_charge(entry, exit_px):
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def add_vwap(df):
    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3.0
    df['cum_tpv'] = df.groupby('date', sort=False).apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date', sort=False)['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol']
    return df


print('Running 6BCE SHORT + Below VWAP  SL=6.0 / TP=6.0 (Best Consistency)...')
daily = defaultdict(float)
N = 0; gp = 0.0; gl = 0.0

for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet'))):
    df = pd.read_parquet(f)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    for col in ['open', 'high', 'low', 'close', 'volume', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df = add_vwap(df)

    close = df['close'].values; high = df['high'].values; low = df['low'].values
    open_ = df['open'].values; atr  = df['atr14'].values; vwap = df['vwap'].values
    hour  = df['hour'].values; date = df['date'].values; n = len(df)

    i = WINDOW - 1
    while i < n:
        if np.isnan(atr[i]) or np.isnan(vwap[i]) or hour[i] >= EOD_HOUR: i += 1; continue
        w = close[i - WINDOW + 1: i + 1]
        if np.any(np.isnan(w)) or close[i] < np.max(w): i += 1; continue
        if not (close[i] < vwap[i]): i += 1; continue
        ei = i + 1
        if ei >= n or date[ei] != date[i] or hour[ei] >= EOD_HOUR: i += 1; continue

        ep = open_[ei]; sl = ep + SL_M * atr[i]; tp = ep - TP_M * atr[i]
        td = date[i]; edt = date[i]; k = ei; xp = ep

        while k < n:
            if date[k] != td:        xp = close[k-1]; edt = date[k-1]; break
            if hour[k] >= EOD_HOUR:  xp = open_[k];  edt = date[k];   break
            if high[k] >= sl:        xp = sl;         edt = date[k];   break
            if low[k]  <= tp:        xp = tp;         edt = date[k];   break
            k += 1
        else:
            xp = close[k-1]; edt = date[k-1]

        zpnl = (ep - xp) - zerodha_charge(ep, xp)
        daily[edt] += zpnl
        if zpnl > 0: gp += zpnl
        else:        gl += abs(zpnl)
        N += 1; i = k + 1

dates_sorted = sorted(daily.keys())
zpnl_series  = np.array([daily[d] for d in dates_sorted])
equity       = np.cumsum(zpnl_series)
peak         = np.maximum.accumulate(equity)
drawdown     = equity - peak

zpf    = round(gp / gl, 4) if gl > 0 else 0.0
max_dd = drawdown.min()
peak_eq = equity.max()
print(f'N={N}  ZPF={zpf}  PeakEquity=Rs{peak_eq:,.2f}  MaxDD=Rs{max_dd:,.2f}')

# ── CHART ─────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True,
                                gridspec_kw={'height_ratios': [2, 1], 'hspace': 0.04})
fig.suptitle(
    '6BCE SHORT + Below VWAP Filter — Equity Curve & Drawdown\n'
    f'SL=6.0 / TP=6.0 (Best Consistency)  |  30 stocks · DS3 2015–2025  |  '
    f'N={N:,}  ZPF={zpf}  MaxDD=₹{max_dd:,.0f}',
    fontsize=11, color='white', y=1.02)

date_nums = mdates.date2num(dates_sorted)

# ── TOP: Equity curve ─────────────────────────────────────────────────────────
ax1.plot(date_nums, equity, color='#00ccff', linewidth=1.0, alpha=0.9)
ax1.axhline(0, color='#555555', linewidth=0.8, linestyle='--')
ax1.fill_between(date_nums, equity, 0, where=(equity >= 0), color='#00ccff', alpha=0.08)
ax1.fill_between(date_nums, equity, 0, where=(equity <  0), color='#ff4444', alpha=0.10)

for yr in range(2015, 2026):
    ax1.axvline(mdates.date2num(pd.Timestamp(f'{yr}-01-01').date()),
                color='#333333', linewidth=0.6, linestyle=':')

ax1.set_ylabel('Cumulative ZPnL (₹ per share)', fontsize=10, labelpad=8)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'₹{x:,.0f}'))
ax1.grid(True, linestyle='--', alpha=0.12, linewidth=0.6)

# ── BOTTOM: Drawdown ──────────────────────────────────────────────────────────
ax2.fill_between(date_nums, drawdown, 0, color='#ff4444', alpha=0.45)
ax2.plot(date_nums, drawdown, color='#ff6666', linewidth=0.7, alpha=0.8)
ax2.axhline(0, color='#555555', linewidth=0.8, linestyle='--')

for yr in range(2015, 2026):
    ax2.axvline(mdates.date2num(pd.Timestamp(f'{yr}-01-01').date()),
                color='#333333', linewidth=0.6, linestyle=':')

ax2.set_ylabel('Drawdown (₹ per share)', fontsize=10, labelpad=8)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'₹{x:,.0f}'))
ax2.grid(True, linestyle='--', alpha=0.12, linewidth=0.6)

ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.setp(ax2.xaxis.get_majorticklabels(), fontsize=10)

plt.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chart_equity_6bce_vwap.png')
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved: {out}')
