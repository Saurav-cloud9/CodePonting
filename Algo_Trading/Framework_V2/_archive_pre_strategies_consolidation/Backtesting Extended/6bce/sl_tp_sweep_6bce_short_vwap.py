import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
import glob
import os

# 6BCE + Below-VWAP filter — SHORT — 90-combo SL/TP sweep
# Signal: close[i] == highest close of last 6 bars (i-5 to i inclusive), hour[i] < 15
# Filter: close[i] < VWAP[i]  (strict; ties at VWAP excluded — not bearish confirmation)
# Entry:  SHORT at open[i+1], same day, hour[i+1] < 15
# Exit:   per backtesting_rules_v2.md Section 4 (date change → hour≥15 → SL → TP)
# Guard:  §13 inline single-pass, i = k+1, exit loop starts at k = ei
# Metrics: ZPF + ZSh(D) primary (Zerodha charges); PF + Sh(D) reference
# Cache:   sweep_cache_6bce_vwap.npz  (overall_grid, yearly_grid, yearly_zshd_grid)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
CACHE_PATH = os.path.join(SCRIPT_DIR, 'sweep_cache_6bce_vwap.npz')
EOD_HOUR   = 15
WINDOW     = 6
YEARS      = list(range(2015, 2026))

SL_VALS  = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
TP_VALS = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def zerodha_charge(entry, exit_px):
    # SHORT: entry = sell side, exit = buy side
    brok  = min(0.0003 * entry, 20) + min(0.0003 * exit_px, 20)
    stt   = entry  * 0.00025       # STT on sell side (entry)
    txn   = (entry + exit_px) * 0.0000307
    sebi  = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003     # stamp duty on buy side (exit)
    gst   = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def add_vwap(df):
    """Intraday VWAP, resets each calendar day. TP = (H+L+C)/3."""
    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3.0
    df['cum_tpv'] = df.groupby('date', sort=False).apply(
        lambda g: (g['tp'] * g['volume']).cumsum(), include_groups=False
    ).reset_index(level=0, drop=True)
    df['cum_vol'] = df.groupby('date', sort=False)['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol']
    return df


def load_stocks():
    stocks = []
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
        stocks.append({
            'open':  df['open'].values,
            'high':  df['high'].values,
            'low':   df['low'].values,
            'close': df['close'].values,
            'atr14': df['atr14'].values,
            'vwap':  df['vwap'].values,
            'hour':  df['hour'].values,
            'date':  df['date'].values,
            'n':     len(df),
        })
    return stocks


def run_combo(stocks, sl_m, tp_m):
    all_pnl   = []
    all_zpnl  = []
    all_dates = []

    for s in stocks:
        close = s['close']; high = s['high']; low  = s['low']
        open_ = s['open'];  atr  = s['atr14']; vwap = s['vwap']
        hour  = s['hour'];  date = s['date'];  n   = s['n']

        i = WINDOW - 1
        while i < n:
            # skip if ATR/VWAP missing or EOD
            if np.isnan(atr[i]) or np.isnan(vwap[i]) or hour[i] >= EOD_HOUR:
                i += 1
                continue
            # signal: close[i] must be highest close over last 6 bars
            window = close[i - WINDOW + 1: i + 1]
            if np.any(np.isnan(window)) or close[i] < np.max(window):
                i += 1
                continue
            # filter: body closes strictly below session VWAP (ties excluded)
            if not (close[i] < vwap[i]):
                i += 1
                continue
            # entry bar: must be same day and before EOD
            ei = i + 1
            if ei >= n or date[ei] != date[i] or hour[ei] >= EOD_HOUR:
                i += 1
                continue
            # enter SHORT
            entry_px   = open_[ei]
            sl         = entry_px + sl_m  * atr[i]
            tp        = entry_px - tp_m * atr[i]
            trade_date = date[i]
            # exit loop — priority: date change → hour≥15 → SL → TP  (§13: k = ei)
            k = ei
            exit_px = entry_px
            exit_dt = trade_date
            while k < n:
                if date[k] != trade_date:
                    exit_px = close[k - 1]; exit_dt = date[k - 1]; break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]; exit_dt = date[k]; break
                if high[k] >= sl:
                    exit_px = sl; exit_dt = date[k]; break
                if low[k] <= tp:
                    exit_px = tp; exit_dt = date[k]; break
                k += 1
            else:
                # end of data without break
                exit_px = close[k - 1]; exit_dt = date[k - 1]

            pnl  = entry_px - exit_px
            zpnl = pnl - zerodha_charge(entry_px, exit_px)
            all_pnl.append(pnl)
            all_zpnl.append(zpnl)
            all_dates.append(exit_dt)
            i = k + 1  # §13 position guard

    return all_pnl, all_zpnl, all_dates


def compute_metrics(pnl_list, zpnl_list, date_list):
    if not pnl_list:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0
    pnl  = np.array(pnl_list)
    zpnl = np.array(zpnl_list)
    gp   = pnl[pnl > 0].sum();   gl  = abs(pnl[pnl < 0].sum())
    zgp  = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
    pf   = round(gp  / gl,  3) if gl  > 0 else 0.0
    zpf  = round(zgp / zgl, 3) if zgl > 0 else 0.0
    daily = (pd.DataFrame({'pnl': pnl, 'zpnl': zpnl, 'date': date_list})
               .groupby('date')[['pnl', 'zpnl']].sum())
    shd  = round((daily['pnl'].mean()  / daily['pnl'].std())  * np.sqrt(252), 3) if daily['pnl'].std()  > 0 else 0.0
    zshd = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0
    pct  = round((daily['zpnl'] > 0).sum() / len(daily) * 100, 1)
    return len(pnl), pf, zpf, shd, zshd, pct


def year_metrics(pnl_list, zpnl_list, date_list):
    df = pd.DataFrame({'pnl': pnl_list, 'zpnl': zpnl_list, 'date': date_list})
    df['year'] = pd.to_datetime(df['date']).dt.year
    rows = []
    for yr, g in df.groupby('year'):
        pnl  = g['pnl'].values;  zpnl = g['zpnl'].values
        gp   = pnl[pnl > 0].sum();   gl  = abs(pnl[pnl < 0].sum())
        zgp  = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
        pf   = round(gp  / gl,  3) if gl  > 0 else 0.0
        zpf  = round(zgp / zgl, 3) if zgl > 0 else 0.0
        daily = g.groupby('date')[['pnl', 'zpnl']].sum()
        nd   = len(daily)
        shd  = round((daily['pnl'].mean()  / daily['pnl'].std())  * np.sqrt(252), 3) if daily['pnl'].std()  > 0 else 0.0
        zshd = round((daily['zpnl'].mean() / daily['zpnl'].std()) * np.sqrt(252), 3) if daily['zpnl'].std() > 0 else 0.0
        pct  = round((daily['zpnl'] > 0).sum() / nd * 100, 1) if nd > 0 else 0.0
        flag = '✅' if zpf >= 1.0 else ('🟡' if zpf >= 0.90 else '❌')
        rows.append({'Year': yr, 'N': len(g), 'Days': nd,
                     'PF': pf, 'ZPF': zpf, 'Sh(D)': shd, 'ZSh(D)': zshd,
                     '%ProfDays': pct, '': flag})
    return rows


def consistency_score(pnl_list, zpnl_list, date_list, lam=1.0):
    """Consistency Score = mean(yearly ZSh) - λ × std(yearly ZSh), λ=1.0 (rules §11)."""
    rows = year_metrics(pnl_list, zpnl_list, date_list)
    if len(rows) < 2:
        return 0.0
    ys = np.array([r['ZSh(D)'] for r in rows], dtype=float)
    return round(float(ys.mean() - lam * ys.std(ddof=0)), 3)


def yearly_zpf_zshd_arrays(pnl_list, zpnl_list, date_list):
    """Per-year ZPF and ZSh(D) aligned to YEARS (missing years → 0)."""
    zpf_arr  = np.zeros(len(YEARS))
    zshd_arr = np.zeros(len(YEARS))
    if not date_list:
        return zpf_arr, zshd_arr
    by_year = {r['Year']: r for r in year_metrics(pnl_list, zpnl_list, date_list)}
    for yi, yr in enumerate(YEARS):
        if yr in by_year:
            zpf_arr[yi]  = by_year[yr]['ZPF']
            zshd_arr[yi] = by_year[yr]['ZSh(D)']
    return zpf_arr, zshd_arr


# ── MAIN ──────────────────────────────────────────────────────────────────────
print('Strategy: 6BCE SHORT + below-VWAP filter')
print('  Signal: close[i] == max(close[i-5..i]), hour[i]<15')
print('  Filter: close[i] < VWAP[i]  (strict; ties excluded)')
print('  Entry:  SHORT open[i+1], same day, hour[i+1]<15')
print('Rules: backtesting_rules_v2.md | Data: DS3 30 stocks 2015-2025\n')
print('Loading stocks (+ VWAP)...')
stocks = load_stocks()
print(f'Loaded {len(stocks)} stocks. Running {len(SL_VALS)} × {len(TP_VALS)} = {len(SL_VALS)*len(TP_VALS)} combos...\n')

results = {}          # (sl,tp) -> metrics tuple
trade_cache = {}      # (sl,tp) -> (pnl, zpnl, dates)

overall_grid     = np.zeros((len(SL_VALS), len(TP_VALS)))
yearly_grid      = np.zeros((len(SL_VALS), len(TP_VALS), len(YEARS)))
yearly_zshd_grid = np.zeros((len(SL_VALS), len(TP_VALS), len(YEARS)))

for si, sl in enumerate(SL_VALS):
    for ti, tp in enumerate(TP_VALS):
        pnl, zpnl, dates = run_combo(stocks, sl, tp)
        n, pf, zpf, shd, zshd, pct = compute_metrics(pnl, zpnl, dates)
        ndays = len(set(dates)) if dates else 0
        cs = consistency_score(pnl, zpnl, dates)
        results[(sl, tp)] = (n, ndays, pf, zpf, shd, zshd, pct, cs)
        trade_cache[(sl, tp)] = (pnl, zpnl, dates)

        overall_grid[si, ti] = zpf
        y_zpf, y_zshd = yearly_zpf_zshd_arrays(pnl, zpnl, dates)
        yearly_grid[si, ti, :]      = y_zpf
        yearly_zshd_grid[si, ti, :] = y_zshd
    print(f'  SL={sl} done')

# ── CACHE (same keys as 6BCE baseline for chart scripts) ──────────────────────
np.savez(CACHE_PATH,
         overall_grid=overall_grid,
         yearly_grid=yearly_grid,
         yearly_zshd_grid=yearly_zshd_grid)
print(f'\nCache saved: {CACHE_PATH}\n')

# ── FULL 90-COMBO TABLE (rules §9) ────────────────────────────────────────────
print('=' * 90)
print('90-COMBO SWEEP TABLE')
print('=' * 90)
hdr = (f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"Days":>5}  {"PF":>6}  {"ZPF":>6}  '
       f'{"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfD":>7}  {"ConsScr":>8}')
print(hdr)
print('  ' + '-' * 86)
for sl in SL_VALS:
    for tp in TP_VALS:
        n, ndays, pf, zpf, shd, zshd, pct, cs = results[(sl, tp)]
        print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {ndays:>5}  {pf:6.3f}  {zpf:6.3f}  '
              f'{shd:7.3f}  {zshd:8.3f}  {pct:7.1f}  {cs:8.3f}')

print()

# ── ZPF GRID ──────────────────────────────────────────────────────────────────
print('ZPF Grid (rows=SL, cols=TP):')
print('  SL\\TP ' + ''.join(f'  {t:4.1f}' for t in TP_VALS))
for sl in SL_VALS:
    print(f'  {sl:5.1f} ' + ''.join(f' {results[(sl,tp)][3]:5.3f}' for tp in TP_VALS))

print()

# ── PF GRID ───────────────────────────────────────────────────────────────────
print('PF Grid (rows=SL, cols=TP):')
print('  SL\\TP ' + ''.join(f'  {t:4.1f}' for t in TP_VALS))
for sl in SL_VALS:
    print(f'  {sl:5.1f} ' + ''.join(f' {results[(sl,tp)][2]:5.3f}' for tp in TP_VALS))

print()

# ── TOP 5 ─────────────────────────────────────────────────────────────────────
ranked_zpf  = sorted(results.items(), key=lambda x: x[1][3], reverse=True)
ranked_zshd = sorted(results.items(), key=lambda x: x[1][5], reverse=True)
ranked_cs   = sorted(results.items(), key=lambda x: x[1][7], reverse=True)

hdr2 = f'  {"SL":>5}  {"TP":>5}  {"N":>8}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}  {"ConsScr":>8}'
print('Top 5 by ZPF:')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_zpf[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

print()
print('Top 5 by ZSh(D):')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_zshd[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

print()
print('Top 5 by Consistency Score (mean yearly ZSh - std yearly ZSh):')
print(hdr2)
for (sl, tp), (n, ndays, pf, zpf, shd, zshd, pct, cs) in ranked_cs[:5]:
    print(f'  {sl:5.1f}  {tp:5.1f}  {n:>8,}  {pf:6.3f}  {zpf:6.3f}  {shd:7.3f}  {zshd:8.3f}  {pct:>10.1f}  {cs:8.3f}')

print()

# ── BEST BY ZPF — OVERALL + YEAR-WISE ────────────────────────────────────────
(best_sl, best_tp) = ranked_zpf[0][0]
best_n, best_ndays, best_pf, best_zpf, best_shd, best_zshd, best_pct, best_cs = results[(best_sl, best_tp)]

print('=' * 90)
print(f'Best combo by ZPF: SL={best_sl}x  TP={best_tp}x')
print(f'Overall: N={best_n:,}  Days={best_ndays}  PF={best_pf}  ZPF={best_zpf}  '
      f'Sh(D)={best_shd}  ZSh(D)={best_zshd}  ProfDays={best_pct}%  ConsScr={best_cs}')
print()
print('Year-wise (best ZPF combo):')
pnl, zpnl, dates = trade_cache[(best_sl, best_tp)]
yr_rows = year_metrics(pnl, zpnl, dates)
print(f'  {"Year":>5}  {"N":>7}  {"Days":>5}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}  {"":>2}')
for r in yr_rows:
    print(f'  {r["Year"]:>5}  {r["N"]:>7,}  {r["Days"]:>5}  {r["PF"]:6.3f}  {r["ZPF"]:6.3f}  '
          f'{r["Sh(D)"]:7.3f}  {r["ZSh(D)"]:8.3f}  {r["%ProfDays"]:>10.1f}  {r[""]:>2}')

# ── BEST BY CONSISTENCY — OVERALL + YEAR-WISE (rules §11 preferred) ──────────
(cs_sl, cs_tp) = ranked_cs[0][0]
cs_n, cs_ndays, cs_pf, cs_zpf, cs_shd, cs_zshd, cs_pct, cs_cs = results[(cs_sl, cs_tp)]
print()
print('=' * 90)
print(f'Best combo by Consistency Score: SL={cs_sl}x  TP={cs_tp}x')
print(f'Overall: N={cs_n:,}  Days={cs_ndays}  PF={cs_pf}  ZPF={cs_zpf}  '
      f'Sh(D)={cs_shd}  ZSh(D)={cs_zshd}  ProfDays={cs_pct}%  ConsScr={cs_cs}')
print()
print('Year-wise (best Consistency combo):')
pnl, zpnl, dates = trade_cache[(cs_sl, cs_tp)]
yr_rows = year_metrics(pnl, zpnl, dates)
print(f'  {"Year":>5}  {"N":>7}  {"Days":>5}  {"PF":>6}  {"ZPF":>6}  {"Sh(D)":>7}  {"ZSh(D)":>8}  {"%ProfDays":>10}  {"":>2}')
for r in yr_rows:
    print(f'  {r["Year"]:>5}  {r["N"]:>7,}  {r["Days"]:>5}  {r["PF"]:6.3f}  {r["ZPF"]:6.3f}  '
          f'{r["Sh(D)"]:7.3f}  {r["ZSh(D)"]:8.3f}  {r["%ProfDays"]:>10.1f}  {r[""]:>2}')

# ── VIABILITY ─────────────────────────────────────────────────────────────────
print()
print('=' * 90)
print('Viability (rules §12): need ZPF > 1.0 AND ZSh(D) > 0')
print(f'  Best ZPF combo      SL={best_sl}/{best_tp}: ZPF={best_zpf}  ZSh(D)={best_zshd}  → '
      f'{"PASS" if best_zpf > 1.0 and best_zshd > 0 else "FAIL"}')
print(f'  Best ConsScr combo  SL={cs_sl}/{cs_tp}: ZPF={cs_zpf}  ZSh(D)={cs_zshd}  → '
      f'{"PASS" if cs_zpf > 1.0 and cs_zshd > 0 else "FAIL"}')
