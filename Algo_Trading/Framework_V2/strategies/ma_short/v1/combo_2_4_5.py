"""One-combo detail: MA Rejection v1 SHORT, SL=2.0, TP=4.5"""
import glob, os
import pandas as pd
import numpy as np

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
EOD_HOUR = 15
SL_M, TP_M = 2.0, 4.5


def zerodha_vec_short(entry, exit_px):
    brok  = np.minimum(0.0003 * entry, 20) + np.minimum(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def load(f):
    df = pd.read_parquet(f)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['year'] = df['datetime'].dt.year
    return df.reset_index(drop=True)


def run_combo(arrays, sl_m, tp_m):
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, atr14 = arrays['ma20'], arrays['atr14']
    hour, date, year = arrays['hour'], arrays['date'], arrays['year']
    n = arrays['n']
    pnl_out = []; entry_out = []; exit_out = []; yr_out = []; dt_out = []
    i = 0
    while i < n:
        if np.isnan(ma20[i]) or np.isnan(atr14[i]):
            i += 1; continue
        if (high[i] >= ma20[i] and open_[i] < ma20[i] and
                close[i] < ma20[i] and hour[i] < EOD_HOUR):
            ei = i + 1
            if ei >= n or date[ei] != date[i] or hour[ei] >= EOD_HOUR:
                i += 1; continue
            entry = open_[ei]; atr = atr14[i]
            sl = entry + sl_m * atr; tp = entry - tp_m * atr
            signal_date = date[i]
            k = ei
            for k in range(ei, n):
                if date[k] != signal_date:
                    exit_px = close[k - 1]; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; break
                if high[k] >= sl:
                    exit_px = sl; break
                if low[k] <= tp:
                    exit_px = tp; break
            pnl_out.append(entry - exit_px)
            entry_out.append(entry); exit_out.append(exit_px)
            yr_out.append(year[ei]); dt_out.append(pd.Timestamp(date[ei]))
            i = k + 1
        else:
            i += 1
    return pnl_out, entry_out, exit_out, yr_out, dt_out


def pf_from(pnl):
    gw = pnl[pnl > 0].sum(); gl = -pnl[pnl < 0].sum()
    return round(float(gw / gl), 3) if gl > 0 else 0.0


def zpf_from(zpnl):
    zw = zpnl[zpnl > 0].sum(); zl = -zpnl[zpnl <= 0].sum()
    return round(float(zw / zl), 3) if zl > 0 else 0.0


def shd(vals, dates):
    tdf = pd.DataFrame({'v': vals, 'date': dates})
    daily = tdf.set_index('date').resample('D')['v'].sum()
    daily = daily[daily != 0]
    if len(daily) <= 1 or daily.std() == 0:
        return 0.0
    return round(float((daily.mean() / daily.std()) * np.sqrt(252)), 3)


files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
print(f'Loading {len(files)} stocks...')
stock_arrays = []
for f in files:
    df = load(f)
    stock_arrays.append({
        'high': df['high'].values, 'low': df['low'].values,
        'open_': df['open'].values, 'close': df['close'].values,
        'ma20': df['ma20'].values, 'atr14': df['atr14'].values,
        'hour': df['hour'].values, 'date': df['date'].values,
        'year': df['year'].values, 'n': len(df),
    })

all_pnl = []; all_entry = []; all_exit = []; all_yr = []; all_dt = []
for arr in stock_arrays:
    p, e, x, y, d = run_combo(arr, SL_M, TP_M)
    all_pnl.extend(p); all_entry.extend(e); all_exit.extend(x)
    all_yr.extend(y); all_dt.extend(d)

pnl = np.array(all_pnl, float)
entry = np.array(all_entry, float)
exit_ = np.array(all_exit, float)
zpnl = pnl - zerodha_vec_short(entry, exit_)
yrs = np.array(all_yr)

tdf = pd.DataFrame({'zpnl': zpnl, 'date': all_dt})
daily = tdf.set_index('date').resample('D')['zpnl'].sum()
daily = daily[daily != 0]
pct = round(float((daily > 0).mean() * 100), 1) if len(daily) else 0.0

print(f'Combo: SL={SL_M}x  TP={TP_M}x')
print(f'Overall: N={len(pnl):,}  Days={len(daily):,}  '
      f'PF={pf_from(pnl):.3f}  ZPF={zpf_from(zpnl):.3f}  '
      f'Sh(D)={shd(pnl, all_dt):.3f}  ZSh(D)={shd(zpnl, all_dt):.3f}  '
      f'%ProfDays={pct:.1f}%')
print()
print(f"{'Year':<6} {'N':>6}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>8}  Flag")
for yr in range(2015, 2026):
    mask = yrs == yr
    if mask.sum() == 0:
        continue
    p_y = pnl[mask]; z_y = zpnl[mask]
    d_y = [d for d, m in zip(all_dt, mask) if m]
    pf_y = pf_from(p_y); zpf_y = zpf_from(z_y)
    flag = 'OK' if zpf_y >= 1.0 else ('YEL' if zpf_y >= 0.9 else 'NO')
    print(f'  {yr}  {mask.sum():>6}  {pf_y:>6.3f}  {zpf_y:>6.3f}  '
          f'{shd(p_y, d_y):>7.3f}  {shd(z_y, d_y):>8.3f}  {flag}')
