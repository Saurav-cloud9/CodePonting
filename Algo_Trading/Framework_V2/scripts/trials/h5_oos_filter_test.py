"""
H5 Signal Quality Filter — IS/OOS Test
IS : 2022-2023 (30 stocks pooled)
OOS: 2024-2025 (30 stocks pooled)
Metrics: p01-p11 (p07 tested on non-NA subset)
Winners: W + EOD+
Coverage floor: 15% of IS signal count
Target OOS PF: > 1.01
"""

import pandas as pd
import numpy as np
from pathlib import Path

SIGNALS_DIR = Path("Algo_Trading/Framework_V2/outputs/h5/signals")
OUT_DIR     = Path("Algo_Trading/Framework_V2/outputs/backtest/signal_filter")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IS_YEARS        = [2022, 2023]
OOS_YEARS       = [2024, 2025]
WINNER_OUTCOMES = {'W', 'EOD+'}
LOSER_OUTCOMES  = {'L', 'EOD-'}
COVERAGE_FLOOR  = 0.15
TARGET_PF       = 1.01
PERCENTILES     = list(range(5, 96, 5))

METRICS = ['p01', 'p02', 'p03', 'p04', 'p05', 'p06', 'p07', 'p08', 'p09', 'p10', 'p11']
BINARY  = {'p11'}       # test =0 and =1 only
INTEGER = {'p03', 'p04', 'p10'}   # still sweep percentiles, just note they're integers


# ── helpers ──────────────────────────────────────────────────────────────────

def pf(df):
    w = df[df['outcome'].isin(WINNER_OUTCOMES)]['pnl'].sum()
    l = df[df['outcome'].isin(LOSER_OUTCOMES)]['pnl'].abs().sum()
    return round(w / l, 4) if l > 0 else np.nan

def we_pct(df):
    return round(df['outcome'].isin(WINNER_OUTCOMES).mean() * 100, 2) if len(df) else np.nan

def stats(df):
    return {'n': len(df), 'pf': pf(df), 'we_pct': we_pct(df)}


# ── load all CSVs ─────────────────────────────────────────────────────────────

print("Loading signal CSVs...")
dfs = []
for f in sorted(SIGNALS_DIR.glob("*_h5_signals_tb3.csv")):
    df = pd.read_csv(f, parse_dates=['datetime'])
    df['year'] = df['datetime'].dt.year
    dfs.append(df)

all_data = pd.concat(dfs, ignore_index=True)
is_data  = all_data[all_data['year'].isin(IS_YEARS)].copy()
oos_data = all_data[all_data['year'].isin(OOS_YEARS)].copy()

is_total  = len(is_data)
floor_n   = int(is_total * COVERAGE_FLOOR)

print(f"IS  signals : {is_total:>8,}  (2022-2023)")
print(f"OOS signals : {len(oos_data):>8,}  (2024-2025)")
print(f"Coverage floor (15%): {floor_n:,}")
print(f"IS  baseline  — PF: {pf(is_data):.4f}  W+E+%: {we_pct(is_data):.1f}%")
print(f"OOS baseline  — PF: {pf(oos_data):.4f}  W+E+%: {we_pct(oos_data):.1f}%")
print()


# ── sweep ─────────────────────────────────────────────────────────────────────

rows = []

for metric in METRICS:
    # subset for p07 (exclude NA rows)
    if metric == 'p07':
        is_m  = is_data[is_data['p07_na'] == 0].dropna(subset=['p07'])
        oos_m = oos_data[oos_data['p07_na'] == 0].dropna(subset=['p07'])
    else:
        is_m  = is_data.dropna(subset=[metric])
        oos_m = oos_data.dropna(subset=[metric])

    # binary: test =0 and =1
    if metric in BINARY:
        for val in [0, 1]:
            is_sub  = is_m[is_m[metric] == val]
            oos_sub = oos_m[oos_m[metric] == val]
            if len(is_sub) < floor_n:
                continue
            is_s  = stats(is_sub)
            oos_s = stats(oos_sub)
            rows.append({
                'metric': metric, 'direction': f'={val}', 'threshold': val,
                'is_n': is_s['n'], 'is_pf': is_s['pf'], 'is_we_pct': is_s['we_pct'],
                'oos_n': oos_s['n'], 'oos_pf': oos_s['pf'], 'oos_we_pct': oos_s['we_pct'],
            })
        continue

    # continuous / integer: percentile sweep, both directions
    vals = is_m[metric].dropna()
    thresholds = [(p, float(np.percentile(vals, p))) for p in PERCENTILES]

    best_is_pf = -np.inf
    best_row   = None

    for pct, thresh in thresholds:
        for direction in ['>=', '<=']:
            is_sub  = is_m[is_m[metric] >= thresh] if direction == '>=' else is_m[is_m[metric] <= thresh]
            oos_sub = oos_m[oos_m[metric] >= thresh] if direction == '>=' else oos_m[oos_m[metric] <= thresh]

            if len(is_sub) < floor_n:
                continue

            is_s = stats(is_sub)
            if pd.isna(is_s['pf']):
                continue

            if is_s['pf'] > best_is_pf:
                best_is_pf = is_s['pf']
                oos_s = stats(oos_sub)
                best_row = {
                    'metric': metric, 'direction': direction,
                    'threshold': round(thresh, 4), 'pct_cutoff': pct,
                    'is_n': is_s['n'], 'is_pf': is_s['pf'], 'is_we_pct': is_s['we_pct'],
                    'oos_n': oos_s['n'], 'oos_pf': oos_s['pf'], 'oos_we_pct': oos_s['we_pct'],
                }

    if best_row:
        rows.append(best_row)


# ── output ────────────────────────────────────────────────────────────────────

res = pd.DataFrame(rows).sort_values('oos_pf', ascending=False).reset_index(drop=True)

W = 100
print("=" * W)
print(f"{'Metric':<8} {'Dir':<4} {'Thresh':>10} {'%ile':>5} "
      f"{'IS_N':>8} {'IS_PF':>7} {'IS_W+E+%':>9} "
      f"{'OOS_N':>8} {'OOS_PF':>8} {'OOS_W+E+%':>10}  {'Pass?'}")
print("=" * W)

for _, r in res.iterrows():
    pct_col = f"{int(r['pct_cutoff'])}" if 'pct_cutoff' in r and pd.notna(r.get('pct_cutoff')) else "—"
    flag    = "PASS" if r['oos_pf'] >= TARGET_PF else ""
    print(
        f"{r['metric']:<8} {r['direction']:<4} {r['threshold']:>10.4f} {pct_col:>5} "
        f"{int(r['is_n']):>8,} {r['is_pf']:>7.4f} {r['is_we_pct']:>9.1f}% "
        f"{int(r['oos_n']):>8,} {r['oos_pf']:>8.4f} {r['oos_we_pct']:>10.1f}%  {flag}"
    )

print("=" * W)
passing = res[res['oos_pf'] >= TARGET_PF]
print(f"\nMetrics passing OOS PF > {TARGET_PF}: {len(passing)}/{len(res)}")

# save
out_path = OUT_DIR / "h5_oos_filter_results.csv"
res.to_csv(out_path, index=False)
print(f"Saved -> {out_path}")
