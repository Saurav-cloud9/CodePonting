"""
Regime analysis: worst vs best stock-years from WFA
Metrics per stock-year: avg ATR, ATR%, MA50 slope, avg daily volume, trend bias
"""
import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"

WORST = [('POWERGRID',2025,0.57),('ITC',2023,0.72),('HDFCBANK',2023,0.76),
         ('HDFCBANK',2025,0.78),('NATIONALUM',2024,0.83)]
BEST  = [('ITC',2022,1.94),('POWERGRID',2022,1.78),('NATIONALUM',2023,1.41),
         ('PNB',2022,1.49),('NATIONALUM',2022,1.44)]

def load_daily(stock, year):
    fpath = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(fpath)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'].dt.year == year].copy()
    if len(df) == 0: return None

    # resample 5-min -> daily OHLCV
    df.set_index('datetime', inplace=True)
    daily = df.resample('D').agg(
        open=('open','first'), high=('high','max'),
        low=('low','min'), close=('close','last'),
        volume=('volume','sum')
    ).dropna(subset=['close'])
    daily = daily[daily['volume'] > 0]

    # ATR14 (daily)
    prev = daily['close'].shift(1)
    tr = pd.concat([
        daily['high'] - daily['low'],
        (daily['high'] - prev).abs(),
        (daily['low']  - prev).abs()
    ], axis=1).max(axis=1)
    daily['atr14'] = tr.rolling(14, min_periods=14).mean()
    daily['atr_pct'] = daily['atr14'] / daily['close'] * 100  # normalised

    # MA50 slope — % change over trailing 50 days
    daily['ma50'] = daily['close'].rolling(50, min_periods=50).mean()
    daily['ma50_slope'] = daily['ma50'].pct_change(20) * 100  # 20-day slope of MA50

    # up/down day ratio (trend bias)
    daily['up'] = (daily['close'] > daily['open']).astype(int)

    return daily

def year_metrics(stock, year):
    daily = load_daily(stock, year)
    if daily is None or len(daily) < 20:
        return None
    d = daily.dropna(subset=['atr14','ma50_slope'])
    return {
        'avg_atr_pct' : round(d['atr_pct'].mean(), 2),       # volatility (normalised)
        'avg_atr_abs' : round(d['atr14'].mean(), 2),          # absolute ATR
        'ma50_slope'  : round(d['ma50_slope'].mean(), 3),     # avg MA50 slope % (trend)
        'up_day_pct'  : round(d['up'].mean() * 100, 1),       # % up days (trend bias)
        'avg_vol_cr'  : round(d['volume'].mean() / 1e7, 2),   # avg daily vol (crores)
        'vol_stddev'  : round(d['volume'].std() / d['volume'].mean() * 100, 1),  # vol consistency %
        'n_days'      : len(d),
    }

# ─── Collect metrics ──────────────────────────────────────────────────────────
rows = []
for group, cases in [('WORST', WORST), ('BEST', BEST)]:
    for stock, year, pf in cases:
        m = year_metrics(stock, year)
        if m:
            rows.append({'group':group, 'stock':stock, 'year':year, 'pf':pf, **m})

df = pd.DataFrame(rows)

# ─── Print table ──────────────────────────────────────────────────────────────
W = 105
print("="*W)
print("REGIME ANALYSIS — WORST vs BEST stock-years (WFA tb3)")
print("="*W)
print(f"{'GROUP':<6} {'STOCK':<12} {'YEAR':>4} {'PF':>5}  "
      f"{'ATR%':>6} {'ATR_ABS':>8} {'MA50_SLP':>9} {'UP_DAY%':>8} {'VOL(Cr)':>8} {'VOL_STD%':>9}")
print("-"*W)

for grp in ['BEST','WORST']:
    sub = df[df['group']==grp].sort_values('pf', ascending=grp=='WORST')
    for _, r in sub.iterrows():
        print(f"{r['group']:<6} {r['stock']:<12} {int(r['year']):>4} {r['pf']:>5.2f}  "
              f"{r['avg_atr_pct']:>6.2f} {r['avg_atr_abs']:>8.2f} {r['ma50_slope']:>9.3f} "
              f"{r['up_day_pct']:>8.1f} {r['avg_vol_cr']:>8.2f} {r['vol_stddev']:>9.1f}")
    if grp == 'BEST':
        print("-"*W)

# ─── Averages comparison ──────────────────────────────────────────────────────
print("="*W)
print("\nAVERAGE COMPARISON — BEST vs WORST")
print("-"*60)
metrics_cols = ['avg_atr_pct','avg_atr_abs','ma50_slope','up_day_pct','avg_vol_cr','vol_stddev']
labels       = ['ATR%','ATR_ABS','MA50_slope','Up-day%','Vol(Cr)','Vol_StdDev%']

best_avg  = df[df['group']=='BEST'][metrics_cols].mean()
worst_avg = df[df['group']=='WORST'][metrics_cols].mean()

print(f"{'METRIC':<14} {'BEST_AVG':>10} {'WORST_AVG':>10} {'DIFF':>10} {'SIGNAL':>10}")
print("-"*60)
for col, lbl in zip(metrics_cols, labels):
    b = best_avg[col]; w = worst_avg[col]
    diff = w - b
    pct_diff = (diff / abs(b) * 100) if b != 0 else 0
    signal = '<<< HIGHER in WORST' if diff > 0 else '>>> LOWER in WORST'
    print(f"{lbl:<14} {b:>10.3f} {w:>10.3f} {diff:>+10.3f}   {signal}")

print("="*W)
print("\nINTERPRETATION KEY:")
print("  ATR%       : Avg daily range as % of price — higher = more volatile market")
print("  MA50_slope : Avg 20-day slope of MA50 — negative = downtrend / choppy")
print("  Up-day%    : % of days that closed green — below 50% = bearish bias")
print("  Vol(Cr)    : Avg daily volume in crores — proxy for participation")
print("  Vol_StdDev%: Volume consistency — high = erratic/news-driven activity")
