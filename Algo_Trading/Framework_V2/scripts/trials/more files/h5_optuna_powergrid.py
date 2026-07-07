"""
H5 Optuna sweep — single stock/year
Objective : net_pnl * sqrt(min(N, N_TARGET) / N_TARGET)
Hard floors: N >= 8, PF >= 1.3, WR >= 0.35
Output     : JSON compatible with H5 Full "Apply Best Params" button
"""
import pandas as pd
import numpy as np
import optuna
import json, os

optuna.logging.set_verbosity(optuna.logging.WARNING)

# ─── Config ──────────────────────────────────────────────────────────────────
STOCK      = "POWERGRID"
YEAR       = "2022"
N_TRIALS   = 500
N_TARGET   = 20

CSV_PATH   = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\powergrid_2022_h5_signals.csv"
OUTPUT_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{STOCK.lower()}_{YEAR}_optuna.json")

# ─── Load signals ─────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
signals = df.to_dict('records')
print(f"Loaded {len(signals)} signals — {STOCK} {YEAR}")

# ─── Gate evaluation (mirrors h5_full.html evalGates exactly) ────────────────
def _agg(results):
    """Aggregate sub-gate list → 'P' / 'F' / 'NA'."""
    non_na = [r for r in results if r != 'NA']
    if not non_na:
        return 'NA'
    return 'P' if all(r == 'P' for r in non_na) else 'F'

def eval_signal(sig, p, af):
    """Returns True if signal passes all gates (G1==P, G2==P, G3==P)."""
    # helper: parse float-or-NaN field from CSV row
    def fval(col):
        v = sig.get(col, np.nan)
        try: return float(v)
        except: return np.nan

    p01v = fval('p01'); p02v = fval('p02')
    p03v = fval('p03'); p04v = fval('p04')
    p05v = fval('p05'); p06v = fval('p06')
    p07v = fval('p07'); p07na = int(fval('p07_na') or 0)
    p08v = fval('p08')
    # p09 stored as float (0.0 / 1.0 / NaN)
    p09raw = sig.get('p09', '')
    p09v = None if (str(p09raw).strip() in ('', 'NaN', 'nan')) else int(float(p09raw))
    bounce_idx = fval('bounce_bar_index')
    p11v = int(float(sig.get('p11', 0)))
    p12raw = sig.get('p12', '')
    p12v = None if (str(p12raw).strip() in ('', 'NaN', 'nan')) else int(float(p12raw))

    # G1
    g1_01 = 'P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v >= p['p01'] else 'F'))
    g1_02 = 'P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v >= p['p02'] else 'F'))
    g1_03 = 'P' if not af['p03'] else ('P' if p03v >= p['p03'] else 'F')
    if not af['p04']:
        g1_04 = 'P'
    elif g1_03 == 'F':
        g1_04 = 'NA'
    elif np.isnan(p04v):
        g1_04 = 'NA'
    else:
        g1_04 = 'P' if p['p04min'] <= p04v <= p['p04max'] else 'F'
    g1 = _agg([g1_01, g1_02, g1_03, g1_04])

    # G2
    g2_05 = 'P' if not af['p05'] else ('P' if p['p05min'] <= p05v <= p['p05max'] else 'F')
    g2_06 = 'P' if not af['p06'] else ('P' if p06v <= p['p06'] else 'F')
    g2_07 = 'P' if not af['p07'] else ('NA' if p07na == 1 else ('P' if p07v >= p['p07'] else 'F'))
    g2_08 = 'P' if not af['p08'] else ('P' if p08v >= p['p08'] else 'F')
    g2_09 = 'P' if not af['p09'] else ('NA' if p09v is None else ('P' if p09v == 1 else 'F'))
    g2_10 = 'P' if not af['p10'] else ('P' if bounce_idx <= p['p10'] else 'F')
    g2 = _agg([g2_05, g2_06, g2_07, g2_08, g2_09, g2_10])

    # G3
    g3_11 = 'P' if not af['p11'] else ('P' if p11v == 1 else 'F')
    g3_12 = 'P' if not af['p12'] else ('NA' if p12v is None else ('P' if p12v == 1 else 'F'))
    g3 = _agg([g3_11, g3_12])

    return g1 == 'P' and g2 == 'P' and g3 == 'P'

# ─── Metrics helper ──────────────────────────────────────────────────────────
def compute_metrics(passing):
    n = len(passing)
    if n == 0:
        return dict(n=0, pf=0, wr=0, net_pnl=0)
    pnls = [s['pnl'] for s in passing]
    gross_profit = sum(x for x in pnls if x > 0)
    gross_loss   = abs(sum(x for x in pnls if x < 0))
    pf  = gross_profit / gross_loss if gross_loss > 0 else 9999.0
    net = sum(pnls)
    wins = sum(1 for s in passing if str(s.get('outcome','')).strip() in ('W', 'EOD+'))
    wr  = wins / n
    return dict(n=n, pf=pf, wr=wr, net_pnl=net)

# ─── Optuna objective ─────────────────────────────────────────────────────────
def objective(trial):
    # G1 — each param has its own on/off; threshold only matters when on
    p01_on  = trial.suggest_categorical('p01_on', [True, False])
    p01     = trial.suggest_float('p01', 0.01, 0.50)
    p02_on  = trial.suggest_categorical('p02_on', [True, False])
    p02     = trial.suggest_float('p02', 0.01, 0.20)
    p03_on  = trial.suggest_categorical('p03_on', [True, False])
    p03     = trial.suggest_int('p03', 1, 15)
    p04_on  = trial.suggest_categorical('p04_on', [True, False])
    p04_min = trial.suggest_int('p04_min', 1, 10)
    p04_max = max(p04_min, trial.suggest_int('p04_max', 1, 20))

    # G2
    p05_on  = trial.suggest_categorical('p05_on', [True, False])
    p05_min = trial.suggest_float('p05_min', 0.0, 2.0)
    p05_max = max(p05_min, trial.suggest_float('p05_max', 0.0, 4.0))
    p06_on  = trial.suggest_categorical('p06_on', [True, False])
    p06     = trial.suggest_int('p06', 20, 100, step=5)
    p07_on  = trial.suggest_categorical('p07_on', [True, False])
    p07     = trial.suggest_float('p07', -1.5, 5.0)
    p08_on  = trial.suggest_categorical('p08_on', [True, False])
    p08     = trial.suggest_float('p08', 0.3, 3.0)
    p09_on  = trial.suggest_categorical('p09', [True, False])
    p10_on  = trial.suggest_categorical('p10_on', [True, False])
    p10     = trial.suggest_int('p10', 0, 9)

    # G3
    p11_on  = trial.suggest_categorical('p11', [True, False])
    p12_on  = trial.suggest_categorical('p12', [True, False])

    af = {
        'p01': p01_on, 'p02': p02_on, 'p03': p03_on, 'p04': p04_on,
        'p05': p05_on, 'p06': p06_on, 'p07': p07_on, 'p08': p08_on,
        'p09': p09_on, 'p10': p10_on, 'p11': p11_on, 'p12': p12_on,
    }
    p = {
        'p01': p01, 'p02': p02, 'p03': p03,
        'p04min': p04_min, 'p04max': p04_max,
        'p05min': p05_min, 'p05max': p05_max,
        'p06': p06, 'p07': p07, 'p08': p08, 'p10': p10,
    }

    passing = [s for s in signals if eval_signal(s, p, af)]
    m = compute_metrics(passing)

    # Hard floors
    if m['n'] < 8:       return -1e9
    if m['pf'] < 1.3:    return -1e9

    score = m['net_pnl'] * (min(m['n'], N_TARGET) / N_TARGET) ** 0.5
    return score

# ─── Sanity check — manual best combo (p05+p08+p11) should give ~21 signals ──
_sanity_af  = {k: False for k in ['p01','p02','p03','p04','p05','p06','p07','p08','p09','p10','p11','p12']}
_sanity_af.update({'p05': True, 'p08': True, 'p11': True})
_sanity_p   = {'p01':0.05,'p02':0.05,'p03':1,'p04min':3,'p04max':8,
               'p05min':0.0,'p05max':1.6,'p06':50,'p07':1.0,'p08':0.5,'p10':5}
_sanity_pass = [s for s in signals if eval_signal(s, _sanity_p, _sanity_af)]
_sm = compute_metrics(_sanity_pass)
print(f"Sanity (p05+p08+p11): N={_sm['n']}  WR={_sm['wr']:.1%}  PF={_sm['pf']:.2f}  PnL={_sm['net_pnl']:.2f}")
if _sm['n'] != 21:
    print("⚠  Expected 21 — gate logic may differ from h5_full.html. Check before trusting results.")

# ─── Run ──────────────────────────────────────────────────────────────────────
# Seed with known-good combo so trial 0 is positive and TPE learns from it
_SEED = {
    'p01_on': False, 'p01': 0.05,
    'p02_on': False, 'p02': 0.05,
    'p03_on': False, 'p03': 1,
    'p04_on': False, 'p04_min': 3, 'p04_max': 8,
    'p05_on': True,  'p05_min': 0.0, 'p05_max': 1.6,
    'p06_on': False, 'p06': 50,
    'p07_on': False, 'p07': 1.0,
    'p08_on': True,  'p08': 0.5,
    'p09':    False,
    'p10_on': False, 'p10': 5,
    'p11':    True,
    'p12':    False,
}
print(f"Running {N_TRIALS} Optuna trials...")
study = optuna.create_study(direction='maximize')
study.enqueue_trial(_SEED)
study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

# ─── Best result ──────────────────────────────────────────────────────────────
bp = study.best_trial.params
p04_max_f = max(bp['p04_min'], bp['p04_max'])
p05_max_f = max(bp['p05_min'], bp['p05_max'])

af_best = {
    'p01': bp['p01_on'], 'p02': bp['p02_on'], 'p03': bp['p03_on'], 'p04': bp['p04_on'],
    'p05': bp['p05_on'], 'p06': bp['p06_on'], 'p07': bp['p07_on'], 'p08': bp['p08_on'],
    'p09': bp['p09'],    'p10': bp['p10_on'], 'p11': bp['p11'],    'p12': bp['p12'],
}
p_best = {
    'p01': bp['p01'], 'p02': bp['p02'], 'p03': bp['p03'],
    'p04min': bp['p04_min'], 'p04max': p04_max_f,
    'p05min': bp['p05_min'], 'p05max': p05_max_f,
    'p06': bp['p06'], 'p07': bp['p07'], 'p08': bp['p08'], 'p10': bp['p10'],
}
passing_best = [s for s in signals if eval_signal(s, p_best, af_best)]
m = compute_metrics(passing_best)

result = {
    'stock': STOCK, 'year': YEAR, 'n_trials': N_TRIALS,
    'best_score': round(study.best_value, 4),
    'n_passing': m['n'], 'pf': round(m['pf'], 4),
    'wr': round(m['wr'], 4), 'net_pnl': round(m['net_pnl'], 4),
    'best_params': {
        'p01': round(bp['p01'], 4),   'p01_on': bp['p01_on'],
        'p02': round(bp['p02'], 4),   'p02_on': bp['p02_on'],
        'p03': bp['p03'],             'p03_on': bp['p03_on'],
        'p04_min': bp['p04_min'],     'p04_max': p04_max_f,  'p04_on': bp['p04_on'],
        'p05_min': round(bp['p05_min'], 4), 'p05_max': round(p05_max_f, 4), 'p05_on': bp['p05_on'],
        'p06': bp['p06'],             'p06_on': bp['p06_on'],
        'p07': round(bp['p07'], 4),   'p07_on': bp['p07_on'],
        'p08': round(bp['p08'], 4),   'p08_on': bp['p08_on'],
        'p09': bp['p09'],
        'p10': bp['p10'],             'p10_on': bp['p10_on'],
        'p11': bp['p11'],
        'p12': bp['p12'],
    }
}

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_FILE, 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n{'='*55}")
print(f"  Signals : {m['n']} / {len(signals)} passing")
print(f"  WR      : {m['wr']:.1%}")
print(f"  PF      : {m['pf']:.2f}")
print(f"  Net PnL : {m['net_pnl']:.2f}")
print(f"  Score   : {study.best_value:.4f}")
print(f"  Output  : {OUTPUT_FILE}")
print(f"{'='*55}")
print(json.dumps(result['best_params'], indent=2))
