"""
H5 Signal Quality Filter — Optuna IS/OOS
IS : 2022-2023, 30 stocks pooled
OOS: 2024-2025, 30 stocks pooled
Metrics: p01-p11 (all, each can be switched on/off per trial)
Winners: W + EOD+
Coverage floor: 15% of IS signals
Target OOS PF: > 1.01
Trials: 500
"""

import pandas as pd
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

SIGNALS_DIR     = Path("Algo_Trading/Framework_V2/outputs/h5/signals")
OUT_DIR         = Path("Algo_Trading/Framework_V2/outputs/backtest/signal_filter")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IS_YEARS        = [2022, 2023]
OOS_YEARS       = [2024, 2025]
WINNER_OUTCOMES = {'W', 'EOD+'}
LOSER_OUTCOMES  = {'L', 'EOD-'}
COVERAGE_FLOOR  = 0.15
TARGET_PF       = 1.01
N_TRIALS        = 500

CONTINUOUS = ['p01', 'p02', 'p05', 'p06', 'p08', 'p09']
INTEGERS   = ['p03', 'p04', 'p10']
BINARY     = ['p11']


# ── helpers ──────────────────────────────────────────────────────────────────

def pf(df):
    w = df[df['outcome'].isin(WINNER_OUTCOMES)]['pnl'].sum()
    l = df[df['outcome'].isin(LOSER_OUTCOMES)]['pnl'].abs().sum()
    return round(w / l, 4) if l > 0 else 0.0

def apply_gates(df, params):
    mask = pd.Series(True, index=df.index)

    for m in CONTINUOUS:
        if not params[f'{m}_active']:
            continue
        thresh = params[f'{m}_thresh']
        if params[f'{m}_dir'] == '>=':
            mask &= df[m] >= thresh
        else:
            mask &= df[m] <= thresh

    for m in INTEGERS:
        if not params[f'{m}_active']:
            continue
        thresh = params[f'{m}_thresh']
        if params[f'{m}_dir'] == '>=':
            mask &= df[m] >= thresh
        else:
            mask &= df[m] <= thresh

    # p07 — exclude NA rows when active
    if params['p07_active']:
        mask &= df['p07_na'] == 0
        thresh = params['p07_thresh']
        if params['p07_dir'] == '>=':
            mask &= df['p07'] >= thresh
        else:
            mask &= df['p07'] <= thresh

    # p11 — binary
    if params['p11_active']:
        mask &= df['p11'] == params['p11_val']

    return df[mask]


# ── load data ─────────────────────────────────────────────────────────────────

print("Loading signal CSVs...")
dfs = []
for f in sorted(SIGNALS_DIR.glob("*_h5_signals_tb3.csv")):
    df = pd.read_csv(f, parse_dates=['datetime'])
    df['year'] = df['datetime'].dt.year
    dfs.append(df)

all_data = pd.concat(dfs, ignore_index=True)
is_data  = all_data[all_data['year'].isin(IS_YEARS)].reset_index(drop=True)
oos_data = all_data[all_data['year'].isin(OOS_YEARS)].reset_index(drop=True)

is_total  = len(is_data)
floor_n   = int(is_total * COVERAGE_FLOOR)

print(f"IS  signals : {is_total:>8,}  (2022-2023)")
print(f"OOS signals : {len(oos_data):>8,}  (2024-2025)")
print(f"Coverage floor (15%): {floor_n:,}")
print(f"IS  baseline PF: {pf(is_data):.4f}")
print(f"OOS baseline PF: {pf(oos_data):.4f}")
print(f"Running {N_TRIALS} Optuna trials...\n")

# pre-compute metric bounds from IS data
bounds = {}
for m in CONTINUOUS + INTEGERS:
    col = is_data[m].dropna()
    bounds[m] = (float(col.min()), float(col.max()))

p07_valid = is_data[is_data['p07_na'] == 0]['p07'].dropna()
bounds['p07'] = (float(p07_valid.min()), float(p07_valid.max()))


# ── objective ─────────────────────────────────────────────────────────────────

def objective(trial):
    params = {}

    for m in CONTINUOUS:
        params[f'{m}_active'] = trial.suggest_categorical(f'{m}_active', [True, False])
        params[f'{m}_thresh'] = trial.suggest_float(f'{m}_thresh', bounds[m][0], bounds[m][1])
        params[f'{m}_dir']    = trial.suggest_categorical(f'{m}_dir', ['>=', '<='])

    for m in INTEGERS:
        params[f'{m}_active'] = trial.suggest_categorical(f'{m}_active', [True, False])
        params[f'{m}_thresh'] = trial.suggest_int(f'{m}_thresh', int(bounds[m][0]), int(bounds[m][1]))
        params[f'{m}_dir']    = trial.suggest_categorical(f'{m}_dir', ['>=', '<='])

    # p07 separate (NA handling)
    params['p07_active'] = trial.suggest_categorical('p07_active', [True, False])
    params['p07_thresh'] = trial.suggest_float('p07_thresh', bounds['p07'][0], bounds['p07'][1])
    params['p07_dir']    = trial.suggest_categorical('p07_dir', ['>=', '<='])

    # p11 binary
    params['p11_active'] = trial.suggest_categorical('p11_active', [True, False])
    params['p11_val']    = trial.suggest_categorical('p11_val', [0, 1])

    filtered = apply_gates(is_data, params)
    if len(filtered) < floor_n:
        return 0.0

    return pf(filtered)


# ── run ───────────────────────────────────────────────────────────────────────

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

best_params = study.best_trial.params
best_is_pf  = study.best_trial.value

# evaluate OOS with IS-derived params
is_filtered  = apply_gates(is_data,  best_params)
oos_filtered = apply_gates(oos_data, best_params)

best_oos_pf = pf(oos_filtered)

# active gates summary
active_gates = []
for m in CONTINUOUS + INTEGERS + ['p07']:
    if best_params.get(f'{m}_active'):
        d = best_params[f'{m}_dir']
        t = best_params[f'{m}_thresh']
        active_gates.append(f"{m} {d} {t:.4f}")
if best_params.get('p11_active'):
    active_gates.append(f"p11 == {best_params['p11_val']}")


# ── output ────────────────────────────────────────────────────────────────────

print("=" * 70)
print("BEST TRIAL RESULT")
print("=" * 70)
print(f"IS  PF : {best_is_pf:.4f}   (N={len(is_filtered):,} / {is_total:,} = {len(is_filtered)/is_total*100:.1f}%)")
print(f"OOS PF : {best_oos_pf:.4f}   (N={len(oos_filtered):,})")
print(f"Pass   : {'YES' if best_oos_pf >= TARGET_PF else 'NO'}")
print()
print("Active gates:")
if active_gates:
    for g in active_gates:
        print(f"  {g}")
else:
    print("  (none — all gates off)")

# top 10 trials
trials_df = study.trials_dataframe()
trials_df = trials_df[['number', 'value']].rename(columns={'value': 'is_pf'})
trials_df = trials_df[trials_df['is_pf'] > 0].sort_values('is_pf', ascending=False).head(10)
print(f"\nTop 10 IS PF trials:")
print(trials_df.to_string(index=False))

# save
out = pd.DataFrame([{
    'is_pf': best_is_pf, 'oos_pf': best_oos_pf,
    'is_n': len(is_filtered), 'oos_n': len(oos_filtered),
    'pass': best_oos_pf >= TARGET_PF,
    'active_gates': ' | '.join(active_gates),
    **{k: v for k, v in best_params.items()}
}])
out.to_csv(OUT_DIR / "h5_signal_optuna_results.csv", index=False)
print(f"\nSaved -> {OUT_DIR / 'h5_signal_optuna_results.csv'}")
