import pandas as pd, numpy as np, json, os

SIG_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals'
OPT_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022'

STOCKS = ['POWERGRID', 'HDFCBANK', 'ITC', 'NATIONALUM', 'PNB']

def _agg(r):
    non_na = [x for x in r if x != 'NA']
    if not non_na: return 'NA'
    return 'P' if all(x == 'P' for x in non_na) else 'F'

def eval_sig(sig, p, af):
    def fval(c):
        v = sig.get(c, np.nan)
        try: return float(v)
        except: return np.nan
    p01v=fval('p01');p02v=fval('p02');p03v=fval('p03');p04v=fval('p04')
    p05v=fval('p05');p07v=fval('p07');p07na=int(fval('p07_na') or 0);p08v=fval('p08')
    p09raw=sig.get('p09','')
    p09v=None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
    bounce_idx=fval('bounce_bar_index')
    p11v=int(float(sig.get('p11',0)))
    g1_01='P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v>=p['p01'] else 'F'))
    g1_02='P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v>=p['p02'] else 'F'))
    g1_03='P' if not af['p03'] else ('P' if p03v>=p['p03'] else 'F')
    if not af['p04']:     g1_04='P'
    elif g1_03=='F':      g1_04='NA'
    elif np.isnan(p04v):  g1_04='NA'
    else: g1_04='P' if p['p04min']<=p04v<=p['p04max'] else 'F'
    g1=_agg([g1_01,g1_02,g1_03,g1_04])
    g2_05='P' if not af['p05'] else ('P' if p['p05min']<=p05v<=p['p05max'] else 'F')
    g2_06='P' if not af['p06'] else ('P' if fval('p06')<=p['p06'] else 'F')
    g2_07='P' if not af['p07'] else ('NA' if p07na==1 else ('P' if p07v>=p['p07'] else 'F'))
    g2_08='P' if not af['p08'] else ('P' if p08v>=p['p08'] else 'F')
    g2_09='P' if not af['p09'] else ('NA' if p09v is None else ('P' if p09v==1 else 'F'))
    g2_10='P' if not af['p10'] else ('P' if bounce_idx<=p['p10'] else 'F')
    g2=_agg([g2_05,g2_06,g2_07,g2_08,g2_09,g2_10])
    g3_11='P' if not af['p11'] else ('P' if p11v==1 else 'F')
    g3=_agg([g3_11,'P'])
    return g1=='P' and g2=='P' and g3=='P'

print(f"{'Stock/TB':18s}  {'N':>5}  {'WR':>6}  {'PF':>5}  {'AvgW':>7}  {'AvgL':>7}  {'R/R':>5}")
print('-'*65)

for stock in STOCKS:
    for tb in [3, 9]:
        with open(f'{OPT_DIR}/{stock.lower()}_2022_optuna_tb{tb}.json') as f:
            j = json.load(f)
        bp = j['best_params']
        p04mxf=max(bp['p04_min'],bp['p04_max']); p05mxf=max(bp['p05_min'],bp['p05_max'])
        af={'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
            'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
            'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':False}
        p={'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
           'p04min':bp['p04_min'],'p04max':p04mxf,
           'p05min':bp['p05_min'],'p05max':p05mxf,
           'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

        df = pd.read_csv(f'{SIG_DIR}/{stock.lower()}_2022_h5_signals_tb{tb}.csv')
        signals = df.to_dict('records')
        passing = [s for s in signals if eval_sig(s, p, af)]

        n = len(passing)
        pnls = [s['pnl'] for s in passing]
        wins = [x for x in pnls if x > 0]
        losses = [x for x in pnls if x < 0]
        wr = len(wins)/n*100 if n else 0
        gp = sum(wins); gl = abs(sum(losses))
        pf = gp/gl if gl else 9999
        avg_w = np.mean(wins) if wins else 0
        avg_l = abs(np.mean(losses)) if losses else 0
        rr = avg_w/avg_l if avg_l else 9999

        print(f"{stock+'_tb'+str(tb):18s}  {n:5d}  {wr:5.1f}%  {pf:5.2f}  {avg_w:7.2f}  {avg_l:7.2f}  {rr:5.2f}")
    print()
