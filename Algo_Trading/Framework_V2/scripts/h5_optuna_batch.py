"""
H5 Optuna batch — 5 stocks × 2022 × 2 tb variants (tb3 / tb9).
Objective : net_pnl * sqrt(min(N, N_TARGET) / N_TARGET)
Hard floors: N >= 8, PF >= 1.3
p10 range  : 0–3 for tb3, 0–9 for tb9
Seed       : p05+p08+p11 manual best (POWERGRID validated)
"""
import pandas as pd
import numpy as np
import optuna
import json, os

optuna.logging.set_verbosity(optuna.logging.WARNING)

STOCKS      = ['POWERGRID','NTPC','RELIANCE','HDFCBANK','INFY','ADANIPORTS','ASHOKLEY',
               'AXISBANK','BAJFINANCE','BANDHANBNK','BHARTIARTL','CIPLA','COALINDIA',
               'DABUR','DIVISLAB','HINDALCO','ICICIBANK','INDUSINDBK','ITC','JSWSTEEL',
               'NATIONALUM','ONGC','PNB','SBIN','SUNPHARMA','TATAMOTORS','TATASTEEL',
               'TECHM','VEDL','WIPRO']
YEAR        = 2022
TB_VARIANTS = [3, 9]
N_TRIALS    = 500
N_TARGET    = 20
SIG_DIR     = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OUT_DIR     = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022"

os.makedirs(OUT_DIR, exist_ok=True)

# ─── Gate helpers ─────────────────────────────────────────────────────────────
def _agg(results):
    non_na = [r for r in results if r != 'NA']
    if not non_na: return 'NA'
    return 'P' if all(r == 'P' for r in non_na) else 'F'

def eval_signal(sig, p, af):
    def fval(col):
        v = sig.get(col, np.nan)
        try: return float(v)
        except: return np.nan

    p01v=fval('p01'); p02v=fval('p02'); p03v=fval('p03'); p04v=fval('p04')
    p05v=fval('p05'); p06v=fval('p06'); p07v=fval('p07'); p07na=int(fval('p07_na') or 0)
    p08v=fval('p08')
    p09raw = sig.get('p09', '')
    p09v = None if str(p09raw).strip() in ('', 'NaN', 'nan') else int(float(p09raw))
    bounce_idx = fval('bounce_bar_index')
    p11v = int(float(sig.get('p11_open', 0)))   # live-compatible: entry open > bounce close

    g1_01 = 'P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v >= p['p01'] else 'F'))
    g1_02 = 'P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v >= p['p02'] else 'F'))
    g1_03 = 'P' if not af['p03'] else ('P' if p03v >= p['p03'] else 'F')
    if not af['p04']:           g1_04 = 'P'
    elif g1_03 == 'F':          g1_04 = 'NA'
    elif np.isnan(p04v):        g1_04 = 'NA'
    else: g1_04 = 'P' if p['p04min'] <= p04v <= p['p04max'] else 'F'
    g1 = _agg([g1_01, g1_02, g1_03, g1_04])

    g2_05 = 'P' if not af['p05'] else ('P' if p['p05min'] <= p05v <= p['p05max'] else 'F')
    g2_06 = 'P' if not af['p06'] else ('P' if p06v <= p['p06'] else 'F')
    g2_07 = 'P' if not af['p07'] else ('NA' if p07na == 1 else ('P' if p07v >= p['p07'] else 'F'))
    g2_08 = 'P' if not af['p08'] else ('P' if p08v >= p['p08'] else 'F')
    g2_09 = 'P' if not af['p09'] else ('NA' if p09v is None else ('P' if p09v == 1 else 'F'))
    g2_10 = 'P' if not af['p10'] else ('P' if bounce_idx <= p['p10'] else 'F')
    g2 = _agg([g2_05, g2_06, g2_07, g2_08, g2_09, g2_10])

    g3_11 = 'P' if not af['p11'] else ('P' if p11v == 1 else 'F')
    g3_12 = 'P'  # p12 dropped
    g3 = _agg([g3_11, g3_12])

    return g1 == 'P' and g2 == 'P' and g3 == 'P'

def compute_metrics(passing):
    n = len(passing)
    if n == 0: return dict(n=0, pf=0, wr=0, net_pnl=0)
    pnls = [s['pnl'] for s in passing]
    gp = sum(x for x in pnls if x > 0)
    gl = abs(sum(x for x in pnls if x < 0))
    pf = gp / gl if gl > 0 else 9999.0
    wins = sum(1 for s in passing if str(s.get('outcome','')).strip() in ('W', 'EOD+'))
    return dict(n=n, pf=pf, wr=wins/n, net_pnl=sum(pnls))

# ─── Optuna objective factory ──────────────────────────────────────────────────
def make_objective(signals, p10_max, n_target=20):
    def objective(trial):
        p01_on  = trial.suggest_categorical('p01_on', [True, False])
        p01     = trial.suggest_float('p01', 0.01, 0.50)
        p02_on  = trial.suggest_categorical('p02_on', [True, False])
        p02     = trial.suggest_float('p02', 0.01, 0.20)
        p03_on  = trial.suggest_categorical('p03_on', [True, False])
        p03     = trial.suggest_int('p03', 1, 15)
        p04_on  = trial.suggest_categorical('p04_on', [True, False])
        p04_min = trial.suggest_int('p04_min', 1, 10)
        p04_max = max(p04_min, trial.suggest_int('p04_max', 1, 20))
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
        p10     = trial.suggest_int('p10', 0, p10_max)        # ← variant-aware
        p11_on  = trial.suggest_categorical('p11', [True, False])
        p12_on  = False  # dropped — entry bar volume not available at entry open

        af = {'p01':p01_on,'p02':p02_on,'p03':p03_on,'p04':p04_on,
              'p05':p05_on,'p06':p06_on,'p07':p07_on,'p08':p08_on,
              'p09':p09_on,'p10':p10_on,'p11':p11_on,'p12':p12_on}
        p  = {'p01':p01,'p02':p02,'p03':p03,'p04min':p04_min,'p04max':p04_max,
              'p05min':p05_min,'p05max':p05_max,'p06':p06,'p07':p07,'p08':p08,'p10':p10}

        passing = [s for s in signals if eval_signal(s, p, af)]
        m = compute_metrics(passing)
        if m['n'] < n_target: return -1e9
        if m['pf'] < 1.3:    return -1e9
        return m['pf'] * (min(m['n'], n_target) / n_target) ** 0.5
    return objective

# ─── Run ──────────────────────────────────────────────────────────────────────
print(f"Running Optuna: {len(STOCKS)} stocks × {len(TB_VARIANTS)} variants × {N_TRIALS} trials\n")
summary = []

for stock in STOCKS:
    for tb in TB_VARIANTS:
        sig_file   = os.path.join(SIG_DIR, f"{stock.lower()}_{YEAR}_h5_signals_tb{tb}.csv")
        out_file   = os.path.join(OUT_DIR, f"{stock.lower()}_{YEAR}_optuna_tb{tb}.json")

        if not os.path.exists(sig_file):
            print(f"  {stock} tb{tb}: signals file not found — skipping")
            continue

        df = pd.read_csv(sig_file)
        df.columns = df.columns.str.strip()
        signals = df.to_dict('records')
        print(f"  {stock} tb{tb}: {len(signals)} signals loaded", end='', flush=True)

        # Seed with known-good combo
        seed = {
            'p01_on':False,'p01':0.05,'p02_on':False,'p02':0.05,
            'p03_on':False,'p03':1,'p04_on':False,'p04_min':3,'p04_max':8,
            'p05_on':True, 'p05_min':0.0,'p05_max':1.6,
            'p06_on':False,'p06':50,'p07_on':False,'p07':1.0,
            'p08_on':True, 'p08':0.5,
            'p09':False,'p10_on':False,'p10':min(5, tb),
            'p11':True,'p12':False,
        }

        n_target = max(20, int(len(signals) * 0.10))
        study = optuna.create_study(direction='maximize')
        study.enqueue_trial(seed)
        study.optimize(make_objective(signals, tb, n_target), n_trials=N_TRIALS, show_progress_bar=False)

        bp  = study.best_trial.params
        p04_max_f = max(bp['p04_min'], bp['p04_max'])
        p05_max_f = max(bp['p05_min'], bp['p05_max'])

        af_best = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
                   'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
                   'p09':bp['p09'],   'p10':bp['p10_on'],'p11':bp['p11'],   'p12':False}
        p_best  = {'p01':round(bp['p01'],4),'p02':round(bp['p02'],4),'p03':bp['p03'],
                   'p04min':bp['p04_min'],'p04max':p04_max_f,
                   'p05min':round(bp['p05_min'],4),'p05max':round(p05_max_f,4),
                   'p06':bp['p06'],'p07':round(bp['p07'],4),'p08':round(bp['p08'],4),'p10':bp['p10']}
        passing = [s for s in signals if eval_signal(s, p_best, af_best)]
        m = compute_metrics(passing)

        result = {
            'stock':stock,'year':YEAR,'tb_variant':tb,'n_trials':N_TRIALS,
            'best_score':round(study.best_value,4),
            'n_total':len(signals),'n_passing':m['n'],
            'pf':round(m['pf'],4),'wr':round(m['wr'],4),'net_pnl':round(m['net_pnl'],4),
            'best_params':{
                'p01':round(bp['p01'],4),'p01_on':bp['p01_on'],
                'p02':round(bp['p02'],4),'p02_on':bp['p02_on'],
                'p03':bp['p03'],         'p03_on':bp['p03_on'],
                'p04_min':bp['p04_min'],'p04_max':p04_max_f,'p04_on':bp['p04_on'],
                'p05_min':round(bp['p05_min'],4),'p05_max':round(p05_max_f,4),'p05_on':bp['p05_on'],
                'p06':bp['p06'],         'p06_on':bp['p06_on'],
                'p07':round(bp['p07'],4),'p07_on':bp['p07_on'],
                'p08':round(bp['p08'],4),'p08_on':bp['p08_on'],
                'p09':bp['p09'],
                'p10':bp['p10'],         'p10_on':bp['p10_on'],
                'p11':bp['p11'],
                'p12':False,
            }
        }
        with open(out_file, 'w') as f:
            json.dump(result, f, indent=2)

        summary.append(result)
        print(f" -> N={m['n']} WR={m['wr']:.1%} PF={m['pf']:.2f} Score={study.best_value:.4f}")

# ─── Summary table ────────────────────────────────────────────────────────────
print(f"\n{'-'*70}")
print(f"{'STOCK':<14} {'TB':>4} {'N_TOT':>6} {'N_PASS':>7} {'WR':>7} {'PF':>7} {'SCORE':>9}")
print(f"{'-'*70}")

for r in summary:
    print(f"{r['stock']:<14} {r['tb_variant']:>4} {r['n_total']:>6} {r['n_passing']:>7} "
          f"{r['wr']:>7.1%} {r['pf']:>7.2f} {r['best_score']:>9.4f}")
print(f"{'-'*70}")
