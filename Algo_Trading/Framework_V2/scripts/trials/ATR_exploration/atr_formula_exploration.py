"""
ATR Formula Exploration — MA Rejection v1 SHORT
Lock: SL=2.0 × ATR · TP=4.5 × ATR
12 variants: (Simple/Wilder × period 10/14/20) × (Signal-bar ATR / Entry-bar ATR)

Baseline reference: ma_30_rejection_v1.py (this folder)
Only ATR calculation + ATR source bar change; everything else identical.
"""
import sys
import io
import os
import glob
from datetime import datetime

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\intraday_5min_DS3'
OUT_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\scripts\trials\ATR_exploration'

SL_MULT = 2.0
TP_MULT = 4.5
EOD_HOUR = 15

# (formula_name, period)
FORMULAS = [
    ('Simple', 10),
    ('Simple', 14),
    ('Simple', 20),
    ('Wilder', 10),
    ('Wilder', 14),
    ('Wilder', 20),
]
SOURCES = ['Signal', 'Entry']


def zerodha_vec_short(entry, exit_px):
    """Vectorized Zerodha charge for SHORT (entry=sell, exit=buy)."""
    brok = np.minimum(0.0003 * entry, 20) + np.minimum(0.0003 * exit_px, 20)
    stt = entry * 0.00025
    txn = (entry + exit_px) * 0.0000307
    sebi = (entry + exit_px) * 0.000001
    stamp = exit_px * 0.000003
    gst = 0.18 * (brok + txn + sebi)
    return brok + stt + txn + sebi + stamp + gst


def true_range(high, low, close):
    """TR with bar-0 = NaN (no prev close) — matches precomputed atr14 convention."""
    n = len(close)
    tr = np.full(n, np.nan)
    if n < 2:
        return tr
    pc = close[:-1]
    h, l = high[1:], low[1:]
    tr[1:] = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return tr


def simple_atr(tr, period):
    return pd.Series(tr).rolling(period, min_periods=period).mean().values


def wilder_atr(tr, period):
    """
    Wilder RMA: ATR_t = (ATR_{t-1}*(N-1) + TR_t)/N
    Seeded with simple mean of first N valid TR values.
    """
    n = len(tr)
    atr = np.full(n, np.nan)
    valid = np.where(~np.isnan(tr))[0]
    if len(valid) < period:
        return atr
    seed_idx = valid[:period]
    seed_end = int(seed_idx[-1])
    atr[seed_end] = float(np.mean(tr[seed_idx]))
    for i in range(seed_end + 1, n):
        if np.isnan(tr[i]) or np.isnan(atr[i - 1]):
            atr[i] = np.nan
        else:
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def load_stock(path):
    df = pd.read_parquet(path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_localize(None)
    for col in ['open', 'high', 'low', 'close', 'ma20', 'atr14']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['year'] = df['datetime'].dt.year
    return df.reset_index(drop=True)


def compute_atr_variants(df):
    """Return dict keyed by (formula, period) -> atr array. Also baseline precomputed atr14."""
    h = df['high'].values.astype(float)
    l = df['low'].values.astype(float)
    c = df['close'].values.astype(float)
    tr = true_range(h, l, c)
    out = {}
    for formula, period in FORMULAS:
        if formula == 'Simple':
            out[(formula, period)] = simple_atr(tr, period)
        else:
            out[(formula, period)] = wilder_atr(tr, period)
    out[('Baseline', 14)] = df['atr14'].values.astype(float)
    return out


def run_backtest(arrays, atr, source):
    """
    Wick-only MA20 rejection SHORT — identical to ma_30_rejection_v1.py
    except ATR column / source bar.
    Returns lists: pnl, entry, exit_px, year, date (entry date).
    """
    high, low, open_, close = arrays['high'], arrays['low'], arrays['open_'], arrays['close']
    ma20, hour, date, year = arrays['ma20'], arrays['hour'], arrays['date'], arrays['year']
    n = arrays['n']

    pnl_out, entry_out, exit_out, yr_out, dt_out = [], [], [], [], []
    i = 0
    while i < n:
        if np.isnan(ma20[i]):
            i += 1
            continue
        # v1: wick-only touch — high reaches MA20, body stays below
        if high[i] >= ma20[i] and open_[i] < ma20[i] and close[i] < ma20[i]:
            if hour[i] >= EOD_HOUR:
                i += 1
                continue
            touch_date = date[i]
            entry_idx = i + 1
            if entry_idx >= n:
                i += 1
                continue
            if date[entry_idx] != touch_date:
                i += 1
                continue

            if source == 'Signal':
                atr_val = atr[i]
            else:  # Entry
                atr_val = atr[entry_idx]

            if np.isnan(atr_val):
                i += 1
                continue

            entry = open_[entry_idx]
            sl = entry + SL_MULT * atr_val
            tp = entry - TP_MULT * atr_val

            k = entry_idx
            exit_px = None
            for k in range(entry_idx, n):
                if date[k] != touch_date:
                    exit_px = close[k - 1]
                    break
                if hour[k] >= EOD_HOUR:
                    exit_px = open_[k]
                    break
                if high[k] >= sl:
                    exit_px = sl
                    break
                if low[k] <= tp:
                    exit_px = tp
                    break
            if exit_px is None:
                # exhausted bars mid-trade (shouldn't happen on complete days)
                exit_px = close[n - 1]

            pnl_out.append(entry - exit_px)
            entry_out.append(entry)
            exit_out.append(exit_px)
            yr_out.append(year[entry_idx])
            dt_out.append(pd.Timestamp(date[entry_idx]))
            i = k + 1
        else:
            i += 1
    return pnl_out, entry_out, exit_out, yr_out, dt_out


def metrics(pnl, zpnl, dates):
    n = len(pnl)
    if n == 0:
        return dict(N=0, PF=0.0, ZPF=0.0, ShD=0.0, ZShD=0.0, PctProfDays=0.0, n_days=0)

    gw = pnl[pnl > 0].sum()
    gl = -pnl[pnl < 0].sum()
    pf = round(float(gw / gl), 3) if gl > 0 else 0.0

    zw = zpnl[zpnl > 0].sum()
    zl = -zpnl[zpnl <= 0].sum()
    zpf = round(float(zw / zl), 3) if zl > 0 else 0.0

    tdf = pd.DataFrame({'pnl': pnl, 'zpnl': zpnl, 'date': dates})
    daily_raw = tdf.set_index('date').resample('D')['pnl'].sum()
    daily_raw = daily_raw[daily_raw != 0]
    if len(daily_raw) > 1 and daily_raw.std() > 0:
        shd = round(float((daily_raw.mean() / daily_raw.std()) * np.sqrt(252)), 3)
    else:
        shd = 0.0

    daily_z = tdf.set_index('date').resample('D')['zpnl'].sum()
    daily_z = daily_z[daily_z != 0]
    if len(daily_z) > 1 and daily_z.std() > 0:
        zshd = round(float((daily_z.mean() / daily_z.std()) * np.sqrt(252)), 3)
    else:
        zshd = 0.0

    n_days = len(daily_z)
    pct_prof = round(float((daily_z > 0).sum() / n_days * 100), 1) if n_days > 0 else 0.0

    return dict(N=n, PF=pf, ZPF=zpf, ShD=shd, ZShD=zshd, PctProfDays=pct_prof, n_days=n_days)


def year_breakdown(pnl, zpnl, years, dates):
    rows = []
    years = np.asarray(years)
    for yr in sorted(np.unique(years)):
        mask = years == yr
        m = metrics(pnl[mask], zpnl[mask], [d for d, keep in zip(dates, mask) if keep])
        flag = '✅' if m['ZPF'] >= 1.0 else ('🟡' if m['ZPF'] >= 0.90 else '❌')
        rows.append({
            'Year': int(yr), 'N': m['N'], 'PF': m['PF'], 'ZPF': m['ZPF'],
            'ShD': m['ShD'], 'ZShD': m['ZShD'], 'Flag': flag,
        })
    # All
    m_all = metrics(pnl, zpnl, dates)
    flag_all = '✅' if m_all['ZPF'] >= 1.0 else ('🟡' if m_all['ZPF'] >= 0.90 else '❌')
    rows.append({
        'Year': 'All', 'N': m_all['N'], 'PF': m_all['PF'], 'ZPF': m_all['ZPF'],
        'ShD': m_all['ShD'], 'ZShD': m_all['ZShD'], 'Flag': flag_all,
    })
    return rows


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.parquet')))
    print(f'ATR Formula Exploration — SL={SL_MULT} TP={TP_MULT}')
    print(f'Loading {len(files)} stocks from DS3...')
    print(f'Run start: {datetime.now().isoformat(timespec="seconds")}')
    print()

    # Per-variant accumulators
    # Order: all Signal (formulas 1–6) then all Entry (7–12)
    # so #2 = Simple14/Signal matches the instructions callout.
    variants = []
    for source in SOURCES:
        for formula, period in FORMULAS:
            variants.append({
                'formula': formula, 'period': period, 'source': source,
                'pnl': [], 'entry': [], 'exit': [], 'year': [], 'date': [],
            })
    # Sanity: precomputed atr14 at Signal (should match Simple14/Signal)
    baseline_acc = {
        'formula': 'Baseline', 'period': 14, 'source': 'Signal',
        'pnl': [], 'entry': [], 'exit': [], 'year': [], 'date': [],
    }

    for fi, path in enumerate(files):
        symbol = os.path.basename(path).replace('.parquet', '')
        df = load_stock(path)
        atr_map = compute_atr_variants(df)
        arrays = {
            'high': df['high'].values.astype(float),
            'low': df['low'].values.astype(float),
            'open_': df['open'].values.astype(float),
            'close': df['close'].values.astype(float),
            'ma20': df['ma20'].values.astype(float),
            'hour': df['hour'].values,
            'date': df['date'].values,
            'year': df['year'].values,
            'n': len(df),
        }

        # Sanity check match rate Simple14 vs precomputed atr14
        s14 = atr_map[('Simple', 14)]
        base = atr_map[('Baseline', 14)]
        both = ~np.isnan(s14) & ~np.isnan(base)
        match_rate = float(np.isclose(s14[both], base[both]).mean()) if both.any() else 0.0

        for v in variants:
            atr = atr_map[(v['formula'], v['period'])]
            p, e, x, y, d = run_backtest(arrays, atr, v['source'])
            v['pnl'].extend(p)
            v['entry'].extend(e)
            v['exit'].extend(x)
            v['year'].extend(y)
            v['date'].extend(d)

        p, e, x, y, d = run_backtest(arrays, atr_map[('Baseline', 14)], 'Signal')
        baseline_acc['pnl'].extend(p)
        baseline_acc['entry'].extend(e)
        baseline_acc['exit'].extend(x)
        baseline_acc['year'].extend(y)
        baseline_acc['date'].extend(d)

        print(f'  [{fi + 1:02d}/{len(files)}] {symbol:15s}  Simple14≈atr14 match={match_rate:.6f}  bars={len(df):,}')

    print()
    print('=' * 100)
    print('RESULTS — all 12 variants (+ Baseline atr14 sanity)')
    print('=' * 100)

    result_rows = []
    trade_store = {}  # key -> (pnl, zpnl, years, dates) for year-wise later

    all_specs = variants + [baseline_acc]
    for idx, v in enumerate(all_specs, start=1):
        pnl = np.array(v['pnl'], dtype=float)
        entry = np.array(v['entry'], dtype=float)
        exit_ = np.array(v['exit'], dtype=float)
        years = np.array(v['year'])
        dates = v['date']
        zpnl = pnl - zerodha_vec_short(entry, exit_)
        m = metrics(pnl, zpnl, dates)
        label = f"{v['formula']}{v['period']}/{v['source']}"
        result_rows.append({
            'idx': idx if v['formula'] != 'Baseline' else 'B',
            'Formula': v['formula'],
            'Period': v['period'],
            'Source': v['source'],
            'Label': label,
            **m,
        })
        trade_store[label] = (pnl, zpnl, years, dates)

    # Number the 12 study variants 1..12 in formula order (not sorted)
    study = [r for r in result_rows if r['Formula'] != 'Baseline']
    for i, r in enumerate(study, start=1):
        r['#'] = i
    baseline_row = next(r for r in result_rows if r['Formula'] == 'Baseline')

    # Print table sorted by ZPF desc
    sorted_study = sorted(study, key=lambda r: r['ZPF'], reverse=True)
    print(f"\n{'#':>2}  {'Formula':<8} {'Per':>3}  {'Source':<6}  {'N':>8}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>7}  {'%ProfD':>7}")
    print('-' * 90)
    for r in sorted_study:
        print(
            f"{r['#']:>2}  {r['Formula']:<8} {r['Period']:>3}  {r['Source']:<6}  "
            f"{r['N']:>8,}  {r['PF']:>6.3f}  {r['ZPF']:>6.3f}  {r['ShD']:>7.3f}  "
            f"{r['ZShD']:>7.3f}  {r['PctProfDays']:>6.1f}%"
        )

    # Sanity check
    s14_sig = next(r for r in study if r['Formula'] == 'Simple' and r['Period'] == 14 and r['Source'] == 'Signal')
    print()
    print('SANITY CHECK — Simple14/Signal vs precomputed atr14/Signal')
    print(f"  Simple14/Signal : N={s14_sig['N']:,}  PF={s14_sig['PF']:.3f}  ZPF={s14_sig['ZPF']:.3f}  "
          f"Sh(D)={s14_sig['ShD']:.3f}  ZSh(D)={s14_sig['ZShD']:.3f}")
    print(f"  Baseline atr14  : N={baseline_row['N']:,}  PF={baseline_row['PF']:.3f}  ZPF={baseline_row['ZPF']:.3f}  "
          f"Sh(D)={baseline_row['ShD']:.3f}  ZSh(D)={baseline_row['ZShD']:.3f}")
    match_ok = (
        s14_sig['N'] == baseline_row['N']
        and abs(s14_sig['PF'] - baseline_row['PF']) < 1e-9
        and abs(s14_sig['ZPF'] - baseline_row['ZPF']) < 1e-9
    )
    print(f"  Exact match: {'YES' if match_ok else 'NO'}")

    best = sorted_study[0]
    best_label = best['Label']
    print()
    print(f"BEST by ZPF: #{best['#']} {best_label}  ZPF={best['ZPF']:.3f}  ZSh(D)={best['ZShD']:.3f}")

    pnl_b, zpnl_b, years_b, dates_b = trade_store[best_label]
    yr_rows = year_breakdown(pnl_b, zpnl_b, years_b, dates_b)
    print()
    print(f"YEAR-WISE — best variant #{best['#']} {best_label}")
    print(f"{'Year':<6} {'N':>8}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>7}  Flag")
    for yr in yr_rows:
        print(
            f"{str(yr['Year']):<6} {yr['N']:>8,}  {yr['PF']:>6.3f}  {yr['ZPF']:>6.3f}  "
            f"{yr['ShD']:>7.3f}  {yr['ZShD']:>7.3f}  {yr['Flag']}"
        )

    print()
    print(f'Run end: {datetime.now().isoformat(timespec="seconds")}')

    # ── Write results.md ──────────────────────────────────────────────────────
    md_path = os.path.join(OUT_DIR, 'atr_formula_exploration_results.md')
    lines = []
    lines.append('# ATR Formula Exploration — Results')
    lines.append('')
    lines.append(f'**Script:** `scripts/trials/ATR_exploration/atr_formula_exploration.py`  ')
    lines.append(f'**Run date:** {datetime.now().date().isoformat()}  ')
    lines.append(f'**Baseline reference:** `ma_30_rejection_v1.py`  ')
    lines.append('**Rules:** Zerodha ZPF / ZSh(D) primary (same charge model as SL/TP sweep)')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 1. Strategy definition')
    lines.append('')
    lines.append('| Item | Detail |')
    lines.append('|---|---|')
    lines.append('| **Side** | SHORT |')
    lines.append('| **Signal (v1 clean-touch)** | Single bar where `high >= MA20` AND `open < MA20` AND `close < MA20` |')
    lines.append('| **Entry** | Open of next bar (`i+1`), same trading day; skipped if date changes |')
    lines.append('| **Signal hour filter** | Signal bar must have `hour < 15` |')
    lines.append('| **SL** | `entry + 2.0 × ATR_variant` **(locked)** |')
    lines.append('| **TP** | `entry − 4.5 × ATR_variant` **(locked)** |')
    lines.append('| **Exit priority** | (1) Date change → prior close · (2) `hour >= 15` → bar open · (3) SL hit · (4) TP hit |')
    lines.append('| **Position guard** | Single-pass; resume at `i = k + 1` after each trade |')
    lines.append('| **Universe** | 30 DS3 stocks, 5-min bars, 2015–2025 |')
    lines.append('| **Data path** | `data/historical/intraday_5min_DS3/*.parquet` |')
    lines.append('| **What varies** | ATR formula (Simple / Wilder) × period (10 / 14 / 20) × source bar (Signal / Entry) — **12 variants** |')
    lines.append('')
    lines.append('### ATR formulas')
    lines.append('')
    lines.append('| # | Formula | Period | Definition |')
    lines.append('|---|---|---|---|')
    lines.append('| 1 | Simple | 10 | Rolling mean of TR |')
    lines.append('| 2 | Simple | 14 | Rolling mean of TR *(= baseline atr14 formula)* |')
    lines.append('| 3 | Simple | 20 | Rolling mean of TR |')
    lines.append('| 4 | Wilder | 10 | RMA: `ATR_t = (ATR_{t-1}×(N-1) + TR_t)/N`, seed = mean of first N TR |')
    lines.append('| 5 | Wilder | 14 | same |')
    lines.append('| 6 | Wilder | 20 | same |')
    lines.append('')
    lines.append('`TR = max(high − low, |high − prev_close|, |low − prev_close|)`  ')
    lines.append('Bar-0 TR = NaN (no prev close) — same warm-up convention as precomputed `atr14`.')
    lines.append('')
    lines.append('### ATR source')
    lines.append('')
    lines.append('| Source | Meaning |')
    lines.append('|---|---|')
    lines.append('| Signal | ATR at the touch/signal bar `i` (baseline behavior) |')
    lines.append('| Entry | ATR at the entry bar `i+1` |')
    lines.append('')
    lines.append('### Zerodha charge model (per trade, qty = 1, SHORT)')
    lines.append('')
    lines.append('```')
    lines.append('brok  = min(0.0003 × entry, 20) + min(0.0003 × exit, 20)')
    lines.append('stt   = entry × 0.00025                    # sell (entry) side')
    lines.append('txn   = (entry + exit) × 0.0000307')
    lines.append('sebi  = (entry + exit) × 0.000001')
    lines.append('stamp = exit × 0.000003                    # buy (exit) side')
    lines.append('gst   = 0.18 × (brok + txn + sebi)')
    lines.append('total = brok + stt + txn + sebi + stamp + gst')
    lines.append('zpnl  = raw_pnl - total')
    lines.append('```')
    lines.append('')
    lines.append('### Primary metrics')
    lines.append('')
    lines.append('- **ZPF** = sum(winning zpnl) / abs(sum(losing zpnl))')
    lines.append('- **ZSh(D)** = (mean(daily_zpnl) / std(daily_zpnl)) × √252')
    lines.append('- **PF / Sh(D)** = raw (pre-charge) reference only')
    lines.append('- **%ProfDays** = % of trading days with daily_zpnl > 0')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 2. Summary table — all 12 variants (sorted by ZPF descending)')
    lines.append('')
    lines.append('| # | Formula | Period | Source | N | PF | ZPF | Sh(D) | ZSh(D) | %ProfDays |')
    lines.append('|---:|---|---:|---|---:|---:|---:|---:|---:|---:|')
    for r in sorted_study:
        print_n = f"{r['N']:,}"
        lines.append(
            f"| {r['#']} | {r['Formula']} | {r['Period']} | {r['Source']} | {print_n} | "
            f"{r['PF']:.3f} | **{r['ZPF']:.3f}** | {r['ShD']:.3f} | {r['ZShD']:.3f} | {r['PctProfDays']:.1f}% |"
            if r is best else
            f"| {r['#']} | {r['Formula']} | {r['Period']} | {r['Source']} | {print_n} | "
            f"{r['PF']:.3f} | {r['ZPF']:.3f} | {r['ShD']:.3f} | {r['ZShD']:.3f} | {r['PctProfDays']:.1f}% |"
        )
    lines.append('')
    lines.append(f"**Best by ZPF:** #{best['#']} **{best['Formula']}{best['Period']}/{best['Source']}** "
                 f"— ZPF={best['ZPF']:.3f}, ZSh(D)={best['ZShD']:.3f}, N={best['N']:,}")
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 3. Sanity check — Simple14/Signal vs precomputed atr14')
    lines.append('')
    lines.append('Variant #2 (Simple, period=14, source=Signal) must reproduce the existing baseline `atr14` numbers.')
    lines.append('')
    lines.append('| Source | N | PF | ZPF | Sh(D) | ZSh(D) | %ProfDays |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    lines.append(
        f"| Simple14/Signal (recomputed) | {s14_sig['N']:,} | {s14_sig['PF']:.3f} | {s14_sig['ZPF']:.3f} | "
        f"{s14_sig['ShD']:.3f} | {s14_sig['ZShD']:.3f} | {s14_sig['PctProfDays']:.1f}% |"
    )
    lines.append(
        f"| Precomputed atr14/Signal | {baseline_row['N']:,} | {baseline_row['PF']:.3f} | {baseline_row['ZPF']:.3f} | "
        f"{baseline_row['ShD']:.3f} | {baseline_row['ZShD']:.3f} | {baseline_row['PctProfDays']:.1f}% |"
    )
    lines.append('')
    lines.append(f"**Exact match:** {'✅ YES' if match_ok else '❌ NO'}")
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f"## 4. Year-wise breakdown — best variant "
                 f"(#{best['#']} {best['Formula']}{best['Period']}/{best['Source']})")
    lines.append('')
    lines.append('Flag: ✅ ZPF ≥ 1.0 · 🟡 ZPF 0.90–0.99 · ❌ ZPF < 0.90')
    lines.append('')
    lines.append('| Year | N | PF | ZPF | Sh(D) | ZSh(D) | Flag |')
    lines.append('|---:|---:|---:|---:|---:|---:|:---:|')
    for yr in yr_rows:
        ylabel = f"**{yr['Year']}**" if yr['Year'] == 'All' else str(yr['Year'])
        nstr = f"**{yr['N']:,}**" if yr['Year'] == 'All' else f"{yr['N']:,}"
        if yr['Year'] == 'All':
            lines.append(
                f"| {ylabel} | {nstr} | **{yr['PF']:.3f}** | **{yr['ZPF']:.3f}** | "
                f"**{yr['ShD']:.3f}** | **{yr['ZShD']:.3f}** | {yr['Flag']} |"
            )
        else:
            lines.append(
                f"| {ylabel} | {nstr} | {yr['PF']:.3f} | {yr['ZPF']:.3f} | "
                f"{yr['ShD']:.3f} | {yr['ZShD']:.3f} | {yr['Flag']} |"
            )
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 5. Notes')
    lines.append('')
    lines.append('- SL/TP locked at **2.0 / 4.5** (live-deployed combo); this study isolates ATR formula + source only.')
    lines.append('- Do **not** compare these ZPF numbers to the SL=6.0/TP=6.0 sweep champion — different risk parameters.')
    lines.append('- Wilder (RMA) reacts slower to volatility spikes than Simple; shorter periods (10) react faster than longer (20).')
    lines.append('- Entry-bar ATR uses one extra bar of information vs signal-bar ATR.')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 6. Raw console output')
    lines.append('')
    lines.append('```')
    # Rebuild a compact console dump for the md
    lines.append(f'ATR Formula Exploration — SL={SL_MULT} TP={TP_MULT}')
    lines.append(f'Stocks: {len(files)}')
    lines.append('')
    lines.append(f"{'#':>2}  {'Formula':<8} {'Per':>3}  {'Source':<6}  {'N':>8}  {'PF':>6}  {'ZPF':>6}  {'Sh(D)':>7}  {'ZSh(D)':>7}  {'%ProfD':>7}")
    for r in sorted_study:
        lines.append(
            f"{r['#']:>2}  {r['Formula']:<8} {r['Period']:>3}  {r['Source']:<6}  "
            f"{r['N']:>8,}  {r['PF']:>6.3f}  {r['ZPF']:>6.3f}  {r['ShD']:>7.3f}  "
            f"{r['ZShD']:>7.3f}  {r['PctProfDays']:>6.1f}%"
        )
    lines.append('')
    lines.append('SANITY CHECK — Simple14/Signal vs precomputed atr14/Signal')
    lines.append(f"  Simple14/Signal : N={s14_sig['N']:,}  PF={s14_sig['PF']:.3f}  ZPF={s14_sig['ZPF']:.3f}")
    lines.append(f"  Baseline atr14  : N={baseline_row['N']:,}  PF={baseline_row['PF']:.3f}  ZPF={baseline_row['ZPF']:.3f}")
    lines.append(f"  Exact match: {'YES' if match_ok else 'NO'}")
    lines.append('')
    lines.append(f"BEST by ZPF: #{best['#']} {best_label}")
    lines.append('')
    lines.append(f"YEAR-WISE — #{best['#']} {best_label}")
    for yr in yr_rows:
        lines.append(
            f"  {str(yr['Year']):<6} N={yr['N']:>8,}  PF={yr['PF']:.3f}  ZPF={yr['ZPF']:.3f}  "
            f"Sh(D)={yr['ShD']:.3f}  ZSh(D)={yr['ZShD']:.3f}  {yr['Flag']}"
        )
    lines.append('```')
    lines.append('')

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'\nWrote results → {md_path}')


if __name__ == '__main__':
    main()
