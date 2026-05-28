import pandas as pd, numpy as np, json

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
    p05v=fval('p05'); p07v=fval('p07'); p07na=int(fval('p07_na') or 0)
    p08v=fval('p08')
    p09raw = sig.get('p09', '')
    p09v = None if str(p09raw).strip() in ('', 'NaN', 'nan') else int(float(p09raw))
    bounce_idx = fval('bounce_bar_index')
    p11v = int(float(sig.get('p11', 0)))
    p12raw = sig.get('p12', '')
    p12v = None if str(p12raw).strip() in ('', 'NaN', 'nan') else int(float(p12raw))
    g1_01 = 'P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v >= p['p01'] else 'F'))
    g1_02 = 'P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v >= p['p02'] else 'F'))
    g1_03 = 'P' if not af['p03'] else ('P' if p03v >= p['p03'] else 'F')
    if not af['p04']:      g1_04 = 'P'
    elif g1_03 == 'F':     g1_04 = 'NA'
    elif np.isnan(p04v):   g1_04 = 'NA'
    else: g1_04 = 'P' if p['p04min'] <= p04v <= p['p04max'] else 'F'
    g1 = _agg([g1_01, g1_02, g1_03, g1_04])
    g2_05 = 'P' if not af['p05'] else ('P' if p['p05min'] <= p05v <= p['p05max'] else 'F')
    g2_07 = 'P' if not af['p07'] else ('NA' if p07na == 1 else ('P' if p07v >= p['p07'] else 'F'))
    g2_08 = 'P' if not af['p08'] else ('P' if p08v >= p['p08'] else 'F')
    g2_09 = 'P' if not af['p09'] else ('NA' if p09v is None else ('P' if p09v == 1 else 'F'))
    g2_10 = 'P' if not af['p10'] else ('P' if bounce_idx <= p['p10'] else 'F')
    g2 = _agg([g2_05, g2_07, g2_08, g2_09, g2_10])
    g3_11 = 'P' if not af['p11'] else ('P' if p11v == 1 else 'F')
    g3_12 = 'P' if not af['p12'] else ('NA' if p12v is None else ('P' if p12v == 1 else 'F'))
    g3 = _agg([g3_11, g3_12])
    return g1 == 'P' and g2 == 'P' and g3 == 'P'

with open('Algo_Trading/Framework_V2/outputs/h5/optuna/2022/infy_2022_optuna_tb9.json') as f:
    j = json.load(f)
bp = j['best_params']

p04_max_f = max(bp['p04_min'], bp['p04_max'])
p05_max_f = max(bp['p05_min'], bp['p05_max'])
af = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
      'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
      'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':bp['p12']}

p_exact   = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
             'p04min':bp['p04_min'],'p04max':p04_max_f,
             'p05min':bp['p05_min'],'p05max':p05_max_f,
             'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}
p_rounded = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
             'p04min':bp['p04_min'],'p04max':p04_max_f,
             'p05min':bp['p05_min'],'p05max':round(p05_max_f,4),
             'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

df = pd.read_csv('Algo_Trading/Framework_V2/outputs/h5/signals/infy_2022_h5_signals_tb9.csv')
signals = df.to_dict('records')

pass_exact   = set(s['signal_id'] for s in signals if eval_signal(s, p_exact, af))
pass_rounded = set(s['signal_id'] for s in signals if eval_signal(s, p_rounded, af))

extra = pass_rounded - pass_exact
print('p05_max exact =', p05_max_f, '  rounded =', round(p05_max_f, 4))
print('Extra signal in rounded (not in exact):')
for sid in extra:
    row = df[df['signal_id'] == sid].iloc[0]
    print('  ID:', sid, ' date:', row['datetime'], ' outcome:', row['outcome'], ' pnl:', row['pnl'], ' p05:', row['p05'])
