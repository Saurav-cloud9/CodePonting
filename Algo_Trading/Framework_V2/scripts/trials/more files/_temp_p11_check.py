"""
Temp script — p11 check (entry_open > bounce_close) vs p11_close (entry_close > bounce_close)
No file writes. Reads existing signal CSVs + OHLCV CSVs only.
"""
import pandas as pd, numpy as np, json, os

OHLCV_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
SIG_DIR    = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals'
OPT_DIR    = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022'

STOCKS = ['POWERGRID', 'NTPC', 'RELIANCE', 'HDFCBANK', 'INFY']

print(f"{'Stock/TB':20s}  {'N_pass':>6}  {'p11=1':>6}  {'p11=1':>10}  {'lost':>5}  {'lost%':>6}  {'lost_W':>6}  {'lost_L':>6}  {'lost_EOD+':>9}  {'lost_EOD-':>9}")
print('-'*105)

for stock in STOCKS:
    # Load OHLCV once per stock
    ohlcv_path = os.path.join(OHLCV_DIR, f'{stock}_5min.csv')
    ohlcv = pd.read_csv(ohlcv_path)
    ohlcv.columns = [c.strip() for c in ohlcv.columns]
    ohlcv['datetime'] = pd.to_datetime(ohlcv['datetime'].str.strip())
    ohlcv_idx = ohlcv.set_index('datetime')['close']

    for tb in [3, 9]:
        sig_path = os.path.join(SIG_DIR, f'{stock.lower()}_2022_h5_signals_tb{tb}.csv')
        opt_path = os.path.join(OPT_DIR, f'{stock.lower()}_2022_optuna_tb{tb}.json')

        df = pd.read_csv(sig_path, parse_dates=['bounce_datetime'])
        df['bounce_datetime'] = pd.to_datetime(df['bounce_datetime'])

        with open(opt_path) as f:
            j = json.load(f)

        # Get passing signals from JSON params (reuse eval from parity check)
        # Simpler: just use the p11=1 signals from the passing set
        # We need to re-eval to get passing set — use existing JSON n_passing signals
        # Shortcut: apply all active filters from JSON, find passing signals
        bp = j['best_params']

        # Build passing mask using vectorised approach (approximate — matches Python eval for non-NaN cols)
        af_p11 = bool(bp['p11'])

        # Get bounce_close from OHLCV
        def get_bounce_close(row):
            try:
                return ohlcv_idx.loc[row['bounce_datetime']]
            except:
                return np.nan

        df['bounce_close'] = df.apply(get_bounce_close, axis=1)
        df['p11'] = (df['entry_price'] > df['bounce_close']).astype(int)

        # Load passing signal IDs using exact Python eval
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
            p09raw = sig.get('p09','')
            p09v = None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
            bounce_idx = fval('bounce_bar_index')
            p11v = int(float(sig.get('p11',0)))
            p12raw = sig.get('p12','')
            p12v = None if str(p12raw).strip() in ('','NaN','nan') else int(float(p12raw))
            g1_01 = 'P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v>=p['p01'] else 'F'))
            g1_02 = 'P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v>=p['p02'] else 'F'))
            g1_03 = 'P' if not af['p03'] else ('P' if p03v>=p['p03'] else 'F')
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

        p04mxf = max(bp['p04_min'],bp['p04_max'])
        p05mxf = max(bp['p05_min'],bp['p05_max'])
        af = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
              'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
              'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':bp['p12']}
        p = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
             'p04min':bp['p04_min'],'p04max':p04mxf,
             'p05min':bp['p05_min'],'p05max':p05mxf,
             'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

        signals = df.to_dict('records')
        passing_ids = set(s['signal_id'] for s in signals if eval_sig(s, p, af))
        passing = df[df['signal_id'].isin(passing_ids)].copy()

        n_pass    = len(passing)
        p11_true  = (passing['p11'] == 1).sum()
        p11  = (passing['p11'] == 1).sum()
        lost      = int(p11_true) - int(p11)  # had p11 close, lost with open
        lost_pct  = lost / n_pass * 100 if n_pass else 0

        # Breakdown of lost signals by outcome
        lost_sigs = passing[(passing['p11']==1) & (passing['p11']==0)]
        lost_W    = (lost_sigs['outcome']=='W').sum()
        lost_L    = (lost_sigs['outcome']=='L').sum()
        lost_Ep   = (lost_sigs['outcome']=='EOD+').sum()
        lost_Em   = (lost_sigs['outcome']=='EOD-').sum()

        name = f'{stock}_tb{tb}'
        print(f"{name:20s}  {n_pass:6d}  {p11_true:6d}  {p11:10d}  {lost:5d}  {lost_pct:5.1f}%  {lost_W:6d}  {lost_L:6d}  {lost_Ep:9d}  {lost_Em:9d}")
