"""
Temp script — compare current (p11_close, p12 as-is) vs live-compatible (p11_open, p12 off)
No file writes. Read-only.
"""
import pandas as pd, numpy as np, json, os

OHLCV_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SIG_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals'
OPT_DIR   = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022'
STOCKS    = ['POWERGRID', 'NTPC', 'RELIANCE', 'HDFCBANK', 'INFY']

def _agg(results):
    non_na = [r for r in results if r != 'NA']
    if not non_na: return 'NA'
    return 'P' if all(r == 'P' for r in non_na) else 'F'

def eval_sig(sig, p, af):
    def fval(col):
        v = sig.get(col, np.nan)
        try: return float(v)
        except: return np.nan
    p01v=fval('p01'); p02v=fval('p02'); p03v=fval('p03'); p04v=fval('p04')
    p05v=fval('p05'); p07v=fval('p07'); p07na=int(fval('p07_na') or 0)
    p08v=fval('p08')
    p09raw=sig.get('p09','')
    p09v=None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
    bounce_idx=fval('bounce_bar_index')
    p11v=int(float(sig.get('p11',0)))
    p12raw=sig.get('p12','')
    p12v=None if str(p12raw).strip() in ('','NaN','nan') else int(float(p12raw))
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
    g3_12='P' if not af['p12'] else ('NA' if p12v is None else ('P' if p12v==1 else 'F'))
    g3=_agg([g3_11,g3_12])
    return g1=='P' and g2=='P' and g3=='P'

def get_metrics(passing):
    n = len(passing)
    if n == 0: return 0, 0.0, 0.0
    pnls = [s['pnl'] for s in passing]
    gp = sum(x for x in pnls if x > 0)
    gl = abs(sum(x for x in pnls if x < 0))
    pf = gp/gl if gl > 0 else 9999.0
    wins = sum(1 for s in passing if str(s.get('outcome','')).strip() in ('W','EOD+'))
    return n, round(wins/n*100, 1), round(pf, 2)

# Cache OHLCV per stock
ohlcv_cache = {}
for stock in STOCKS:
    ohlcv = pd.read_csv(os.path.join(OHLCV_DIR, f'{stock}_5min.csv'))
    ohlcv.columns = [c.strip() for c in ohlcv.columns]
    ohlcv['datetime'] = pd.to_datetime(ohlcv['datetime'].str.strip())
    ohlcv_cache[stock] = ohlcv.set_index('datetime')['close']

results = {}
for stock in STOCKS:
    results[stock] = {}
    for tb in [3, 9]:
        with open(os.path.join(OPT_DIR, f'{stock.lower()}_2022_optuna_tb{tb}.json')) as f:
            j = json.load(f)
        bp = j['best_params']
        p04mxf = max(bp['p04_min'], bp['p04_max'])
        p05mxf = max(bp['p05_min'], bp['p05_max'])
        af = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
              'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
              'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':bp['p12']}
        p = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
             'p04min':bp['p04_min'],'p04max':p04mxf,
             'p05min':bp['p05_min'],'p05max':p05mxf,
             'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

        df = pd.read_csv(os.path.join(SIG_DIR, f'{stock.lower()}_2022_h5_signals_tb{tb}.csv'))
        df['bounce_datetime'] = pd.to_datetime(df['bounce_datetime'])

        # bounce_close lookup
        ohlcv_idx = ohlcv_cache[stock]
        df['bounce_close'] = df['bounce_datetime'].map(ohlcv_idx)
        df['p11_open'] = (df['entry_price'] > df['bounce_close']).astype(int)

        signals = df.to_dict('records')

        # OLD: current (p11_close, p12 as-is)
        passing_old = [s for s in signals if eval_sig(s, p, af)]
        n_old, wr_old, pf_old = get_metrics(passing_old)

        # NEW: p11_open replacing p11, p12 silenced
        af_new = dict(af)
        af_new['p11'] = True   # keep p11 active but evaluate differently below
        af_new['p12'] = False  # silence p12

        def eval_sig_new(sig, p, af):
            def fval(col):
                v = sig.get(col, np.nan)
                try: return float(v)
                except: return np.nan
            p01v=fval('p01'); p02v=fval('p02'); p03v=fval('p03'); p04v=fval('p04')
            p05v=fval('p05'); p07v=fval('p07'); p07na=int(fval('p07_na') or 0)
            p08v=fval('p08')
            p09raw=sig.get('p09','')
            p09v=None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
            bounce_idx=fval('bounce_bar_index')
            p11_open_v=int(float(sig.get('p11_open',0)))  # use p11_open column
            p12raw=sig.get('p12','')
            p12v=None if str(p12raw).strip() in ('','NaN','nan') else int(float(p12raw))
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
            g3_11='P' if not af['p11'] else ('P' if p11_open_v==1 else 'F')
            g3_12='P'  # p12 silenced
            g3=_agg([g3_11,g3_12])
            return g1=='P' and g2=='P' and g3=='P'

        passing_new = [s for s in signals if eval_sig_new(s, p, af_new)]
        n_new, wr_new, pf_new = get_metrics(passing_new)

        results[stock][tb] = {
            'old': (n_old, wr_old, pf_old),
            'new': (n_new, wr_new, pf_new)
        }

# Print OLD table
print("OLD (p11=close, p12 as-is):")
print(f"{'Stock':12s}  {'tb3 N':>6}  {'tb3 WR':>7}  {'tb3 PF':>7}  {'tb9 N':>6}  {'tb9 WR':>7}  {'tb9 PF':>7}  Winner")
print('-'*75)
for stock in STOCKS:
    t3 = results[stock][3]['old']
    t9 = results[stock][9]['old']
    winner = 'tb3' if t3[2] > t9[2] else 'tb9'
    print(f"{stock:12s}  {t3[0]:6d}  {t3[1]:6.1f}%  {t3[2]:7.2f}  {t9[0]:6d}  {t9[1]:6.1f}%  {t9[2]:7.2f}  {winner}")

print()

# Print NEW table
print("NEW (p11=open, p12 silenced):")
print(f"{'Stock':12s}  {'tb3 N':>6}  {'tb3 WR':>7}  {'tb3 PF':>7}  {'tb9 N':>6}  {'tb9 WR':>7}  {'tb9 PF':>7}  Winner")
print('-'*75)
for stock in STOCKS:
    t3 = results[stock][3]['new']
    t9 = results[stock][9]['new']
    winner = 'tb3' if t3[2] > t9[2] else 'tb9'
    print(f"{stock:12s}  {t3[0]:6d}  {t3[1]:6.1f}%  {t3[2]:7.2f}  {t9[0]:6d}  {t9[1]:6.1f}%  {t9[2]:7.2f}  {winner}")
