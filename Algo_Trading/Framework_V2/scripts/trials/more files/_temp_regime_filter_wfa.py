"""
Regime filter WFA — apply ATR% + Vol_StdDev% day filters to worst-performing stock-years
Before: all signals from pre-computed CSV (no param filtering)
After : signals on days where ATR14% >= 2.25 AND Vol_StdDev20% >= 65
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime

DATA_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
SIG_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OUT_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5"

ATR_FLOOR     = 2.25   # ATR14% threshold
VOL_STD_FLOOR = 65.0   # 20-day volume CoV% threshold

WORST = [
    ('POWERGRID', 2025, 0.57),
    ('ITC',       2023, 0.72),
    ('HDFCBANK',  2023, 0.76),
    ('HDFCBANK',  2025, 0.78),
    ('NATIONALUM',2024, 0.83),
]

# ─── Build daily regime flags from 5-min CSV ─────────────────────────────────
def build_daily_regime(stock, year):
    fpath = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(fpath)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'].dt.year == year].copy()
    if len(df) == 0:
        return pd.DataFrame()

    df.set_index('datetime', inplace=True)
    daily = df.resample('D').agg(
        open=('open', 'first'), high=('high', 'max'),
        low=('low', 'min'), close=('close', 'last'),
        volume=('volume', 'sum')
    ).dropna(subset=['close'])
    daily = daily[daily['volume'] > 0].copy()

    # ATR14 (daily true range)
    prev = daily['close'].shift(1)
    tr = pd.concat([
        daily['high'] - daily['low'],
        (daily['high'] - prev).abs(),
        (daily['low']  - prev).abs()
    ], axis=1).max(axis=1)
    daily['atr14']    = tr.rolling(14, min_periods=14).mean()
    daily['atr_pct']  = daily['atr14'] / daily['close'] * 100

    # 20-day volume coefficient of variation (std / mean * 100)
    daily['vol_std20'] = (
        daily['volume'].rolling(20, min_periods=20).std() /
        daily['volume'].rolling(20, min_periods=20).mean() * 100
    )

    daily['regime_ok'] = (
        (daily['atr_pct']  >= ATR_FLOOR) &
        (daily['vol_std20'] >= VOL_STD_FLOOR)
    )

    return daily[['atr_pct', 'vol_std20', 'regime_ok']].copy()

# ─── Metrics ─────────────────────────────────────────────────────────────────
def metrics(sigs):
    n = len(sigs)
    if n == 0:
        return dict(n=0, wr=0.0, pf=0.0, net=0.0)
    pnls = [float(s['pnl']) for s in sigs]
    gp   = sum(x for x in pnls if x > 0)
    gl   = abs(sum(x for x in pnls if x < 0))
    wins = sum(1 for x in pnls if x > 0)
    return dict(
        n   = n,
        wr  = round(wins / n * 100, 1),
        pf  = round(gp / gl, 3) if gl > 0 else 9999.0,
        net = round(sum(pnls), 0)
    )

# ─── Run ─────────────────────────────────────────────────────────────────────
results = []

for stock, year, wfa_pf in WORST:
    print(f"Processing {stock} {year}...")

    # Load daily regime flags
    regime = build_daily_regime(stock, year)
    if regime.empty:
        print(f"  No price data found — skipping")
        continue
    regime.index = pd.to_datetime(regime.index.date)  # normalize to date only

    # Load signals
    sig_path = os.path.join(SIG_DIR, f"{stock.lower()}_{year}_h5_signals_tb3.csv")
    if not os.path.exists(sig_path):
        print(f"  No signal file found — skipping")
        continue
    df_sig = pd.read_csv(sig_path)
    df_sig.columns = df_sig.columns.str.strip()
    df_sig['date'] = pd.to_datetime(df_sig['datetime']).dt.date
    df_sig['date'] = pd.to_datetime(df_sig['date'])

    # Join regime flag to each signal
    df_sig['regime_ok'] = df_sig['date'].map(regime['regime_ok']).fillna(False)
    df_sig['atr_pct']   = df_sig['date'].map(regime['atr_pct'])
    df_sig['vol_std20'] = df_sig['date'].map(regime['vol_std20'])

    all_sigs     = df_sig.to_dict('records')
    regime_sigs  = df_sig[df_sig['regime_ok']].to_dict('records')

    m_before = metrics(all_sigs)
    m_after  = metrics(regime_sigs)

    # Count days filtered
    sig_days_total   = df_sig['date'].nunique()
    sig_days_ok      = df_sig[df_sig['regime_ok']]['date'].nunique()

    # ATR filter breakdown
    atr_fail_days = df_sig[df_sig['atr_pct'] < ATR_FLOOR]['date'].nunique()
    vol_fail_days = df_sig[df_sig['vol_std20'] < VOL_STD_FLOOR]['date'].nunique()

    pf_delta = round(m_after['pf'] - m_before['pf'], 3)
    wr_delta = round(m_after['wr'] - m_before['wr'], 1)

    row = {
        'stock'          : stock,
        'year'           : year,
        'wfa_pf'         : wfa_pf,
        'n_before'       : m_before['n'],
        'n_after'        : m_after['n'],
        'pct_kept'       : round(m_after['n'] / m_before['n'] * 100, 1) if m_before['n'] else 0,
        'wr_before'      : m_before['wr'],
        'wr_after'       : m_after['wr'],
        'wr_delta'       : wr_delta,
        'pf_before'      : m_before['pf'],
        'pf_after'       : m_after['pf'],
        'pf_delta'       : pf_delta,
        'net_before'     : m_before['net'],
        'net_after'      : m_after['net'],
        'net_delta'      : round(m_after['net'] - m_before['net'], 0),
        'days_total'     : sig_days_total,
        'days_ok'        : sig_days_ok,
        'atr_fail_days'  : atr_fail_days,
        'vol_fail_days'  : vol_fail_days,
    }
    results.append(row)
    print(f"  Before: N={m_before['n']} WR={m_before['wr']}% PF={m_before['pf']} Net={m_before['net']:,.0f}")
    print(f"  After : N={m_after['n']}  WR={m_after['wr']}% PF={m_after['pf']} Net={m_after['net']:,.0f}  "
          f"(kept {row['pct_kept']}% of signals)")

# ─── Print table ─────────────────────────────────────────────────────────────
W = 115
print()
print("="*W)
print("REGIME FILTER IMPACT — Worst-Performing Stock-Years")
print(f"  Filter 1: ATR14% >= {ATR_FLOOR}%  |  Filter 2: Vol_StdDev20% >= {VOL_STD_FLOOR}%")
print("="*W)
print(f"{'STOCK':<12} {'YEAR':>4} {'WFA_PF':>7}  "
      f"{'N_BEF':>6} {'N_AFT':>6} {'KEPT%':>6}  "
      f"{'WR_BEF':>7} {'WR_AFT':>7} {'WR_D':>6}  "
      f"{'PF_BEF':>7} {'PF_AFT':>7} {'PF_D':>7}  "
      f"{'NET_BEF':>9} {'NET_AFT':>9} {'NET_D':>9}")
print("-"*W)

for r in results:
    pf_sym  = "+" if r['pf_delta']  > 0 else "-"
    wr_sym  = "+" if r['wr_delta']  > 0 else "-"
    net_sym = "+" if r['net_delta'] > 0 else "-"
    print(f"{r['stock']:<12} {r['year']:>4} {r['wfa_pf']:>7.2f}  "
          f"{r['n_before']:>6} {r['n_after']:>6} {r['pct_kept']:>5.1f}%  "
          f"{r['wr_before']:>6.1f}% {r['wr_after']:>6.1f}% {wr_sym}{abs(r['wr_delta']):>4.1f}%  "
          f"{r['pf_before']:>7.3f} {r['pf_after']:>7.3f} {pf_sym}{abs(r['pf_delta']):>6.3f}  "
          f"{r['net_before']:>9,.0f} {r['net_after']:>9,.0f} {net_sym}{abs(r['net_delta']):>8,.0f}")

print("="*W)

# Filter breakdown
print("\nFILTER BREAKDOWN — Days removed per filter")
print(f"{'STOCK':<12} {'YEAR':>4}  {'TOTAL_DAYS':>10} {'DAYS_OK':>8} {'ATR_FAIL':>9} {'VOL_FAIL':>9}")
print("-"*60)
for r in results:
    print(f"{r['stock']:<12} {r['year']:>4}  {r['days_total']:>10} {r['days_ok']:>8} "
          f"{r['atr_fail_days']:>9} {r['vol_fail_days']:>9}")
print("-"*60)

# ─── Verdict ─────────────────────────────────────────────────────────────────
print("\nVERDICT PER STOCK-YEAR:")
for r in results:
    if r['pf_after'] > 1.0 and r['pf_delta'] > 0:
        verdict = f"IMPROVED [+]  PF {r['pf_before']} -> {r['pf_after']} (+{r['pf_delta']:.3f}) -- filter WORKS"
    elif r['pf_delta'] > 0:
        verdict = f"PARTIAL  [+]  PF {r['pf_before']} -> {r['pf_after']} (+{r['pf_delta']:.3f}) -- improved but still <1.0"
    else:
        verdict = f"NO HELP  [-]  PF {r['pf_before']} -> {r['pf_after']} ({r['pf_delta']:.3f}) -- filter doesn't help"
    print(f"  {r['stock']:<12} {r['year']}: {verdict}")

# ─── Save CSV ─────────────────────────────────────────────────────────────────
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out_csv = os.path.join(OUT_DIR, f"regime_filter_wfa_{ts}.csv")
pd.DataFrame(results).to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")
