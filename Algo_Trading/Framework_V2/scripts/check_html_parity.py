import pandas as pd, numpy as np, json, os

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
    g2_06 = 'P' if not af['p06'] else ('P' if p06v <= p['p06'] else 'F')
    g2_07 = 'P' if not af['p07'] else ('NA' if p07na == 1 else ('P' if p07v >= p['p07'] else 'F'))
    g2_08 = 'P' if not af['p08'] else ('P' if p08v >= p['p08'] else 'F')
    g2_09 = 'P' if not af['p09'] else ('NA' if p09v is None else ('P' if p09v == 1 else 'F'))
    g2_10 = 'P' if not af['p10'] else ('P' if bounce_idx <= p['p10'] else 'F')
    g2 = _agg([g2_05, g2_06, g2_07, g2_08, g2_09, g2_10])
    g3_11 = 'P' if not af['p11'] else ('P' if p11v == 1 else 'F')
    g3_12 = 'P' if not af['p12'] else ('NA' if p12v is None else ('P' if p12v == 1 else 'F'))
    g3 = _agg([g3_11, g3_12])
    return g1 == 'P' and g2 == 'P' and g3 == 'P'

sig_dir = 'Algo_Trading/Framework_V2/outputs/h5/signals'
opt_dir = 'Algo_Trading/Framework_V2/outputs/h5/optuna/2022'

print(f"{'Stock+Variant':28s}  JSON_N  Python  Match")
print('-'*55)
all_ok = True
for fname in sorted(os.listdir(opt_dir)):
    if 'tb' not in fname:
        continue
    with open(f'{opt_dir}/{fname}') as f:
        j = json.load(f)
    bp = j['best_params']
    p04max_f = max(bp['p04_min'], bp['p04_max'])
    af = {k.replace('_on',''): bool(bp[k]) for k in bp if k.endswith('_on')}
    af['p09'] = bool(bp['p09']); af['p11'] = bool(bp['p11']); af['p12'] = bool(bp['p12'])
    p = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
         'p04min':bp['p04_min'],'p04max':p04max_f,
         'p05min':bp['p05_min'],'p05max':bp['p05_max'],
         'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}
    stock = j['stock'].lower(); tb = j['tb_variant']
    df = pd.read_csv(f'{sig_dir}/{stock}_2022_h5_signals_tb{tb}.csv')
    signals = df.to_dict('records')
    n = sum(1 for s in signals if eval_signal(s, p, af))
    json_n = j['n_passing']
    match = 'OK' if n == json_n else f'MISMATCH ({n} vs {json_n})'
    if n != json_n: all_ok = False
    name = fname.replace('_2022_optuna','').replace('.json','')
    print(f"{name:28s}  {json_n:6d}  {n:6d}  {match}")

print()
print('All OK' if all_ok else 'MISMATCHES FOUND — check above')
