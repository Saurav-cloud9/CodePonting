import pandas as pd, numpy as np, os, json

STOCKS  = ['POWERGRID','HDFCBANK','ITC','NATIONALUM','PNB']
YEARS   = [2022,2023,2024,2025]
TB      = [3,9]
SIG_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OPT_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022"

def _agg(results):
    non_na=[r for r in results if r!='NA']
    if not non_na: return 'NA'
    return 'P' if all(r=='P' for r in non_na) else 'F'

def eval_signal(sig,p,af):
    def fval(col):
        v=sig.get(col,np.nan)
        try: return float(v)
        except: return np.nan
    p01v=fval('p01');p02v=fval('p02');p03v=fval('p03');p04v=fval('p04')
    p05v=fval('p05');p07v=fval('p07');p07na=int(fval('p07_na') or 0);p08v=fval('p08')
    p09raw=sig.get('p09','')
    p09v=None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
    bounce_idx=fval('bounce_bar_index')
    p11v=int(float(sig.get('p11_open',0)))
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
    g3=_agg([g3_11])
    return g1=='P' and g2=='P' and g3=='P'

def metrics(sigs):
    n=len(sigs)
    if n==0: return dict(n=0,wr=0.0,pf=0.0,net=0.0)
    pnls=[float(s['pnl']) for s in sigs]
    gp=sum(x for x in pnls if x>0); gl=abs(sum(x for x in pnls if x<0))
    wins=sum(1 for x in pnls if x>0)
    return dict(n=n,wr=round(wins/n*100,1),pf=round(gp/gl,2) if gl else 9999,net=round(sum(pnls),0))

print("WFA — Train: 2022 params (frozen) | Validate: 2023 / 2024 / 2025")
print("="*85)
print(f"{'STOCK':<12} {'TB':>3}  {'METRIC':>6}  {'2022(TRAIN)':>11}  {'2023':>10}  {'2024':>10}  {'2025':>10}")
print("-"*85)

for stock in STOCKS:
    for tb in TB:
        jpath = os.path.join(OPT_DIR, f"{stock.lower()}_2022_optuna_tb{tb}.json")
        if not os.path.exists(jpath):
            print(f"  MISSING: {jpath}"); continue
        with open(jpath) as f: j=json.load(f)
        bp=j['best_params']
        p04mxf=max(bp['p04_min'],bp['p04_max'])
        p05mxf=max(bp['p05_min'],bp['p05_max'])
        af={'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
            'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
            'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':False}
        p={'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
           'p04min':bp['p04_min'],'p04max':p04mxf,
           'p05min':bp['p05_min'],'p05max':p05mxf,
           'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

        yr_m={}
        for yr in YEARS:
            fpath=os.path.join(SIG_DIR,f"{stock.lower()}_{yr}_h5_signals_tb{tb}.csv")
            if not os.path.exists(fpath): yr_m[yr]=dict(n=0,wr=0,pf=0,net=0); continue
            df=pd.read_csv(fpath); df.columns=df.columns.str.strip()
            passing=[s for s in df.to_dict('records') if eval_signal(s,p,af)]
            yr_m[yr]=metrics(passing)

        m=yr_m
        tag=f"{stock:<12} tb{tb}"
        print(f"{tag}  {'N':>6}  {m[2022]['n']:>11}  {m[2023]['n']:>10}  {m[2024]['n']:>10}  {m[2025]['n']:>10}")
        print(f"{'':12} {'':3}  {'WR%':>6}  {str(m[2022]['wr'])+'%':>11}  {str(m[2023]['wr'])+'%':>10}  {str(m[2024]['wr'])+'%':>10}  {str(m[2025]['wr'])+'%':>10}")
        print(f"{'':12} {'':3}  {'PF':>6}  {m[2022]['pf']:>11}  {m[2023]['pf']:>10}  {m[2024]['pf']:>10}  {m[2025]['pf']:>10}")
        print(f"{'':12} {'':3}  {'NetPnL':>6}  {m[2022]['net']:>11,.0f}  {m[2023]['net']:>10,.0f}  {m[2024]['net']:>10,.0f}  {m[2025]['net']:>10,.0f}")
        print()
