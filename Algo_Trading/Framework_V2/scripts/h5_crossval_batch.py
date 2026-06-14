"""
Cross-validation batch — 5 stocks × 2023/2024/2025 × tb3/tb9
Step 1: Export signals per year (in-memory signal gen, writes CSVs)
Step 2: Run Optuna per year (500 trials, frozen p11, p12 dropped)
Output:
  Signals : outputs/h5/signals/{stock}_{year}_h5_signals_tb{n}.csv
  Optuna  : outputs/h5/optuna/{year}/{stock}_{year}_optuna_tb{n}.json
"""
import pandas as pd
import numpy as np
import optuna
import json, os

optuna.logging.set_verbosity(optuna.logging.WARNING)

STOCKS      = ['POWERGRID', 'HDFCBANK', 'ITC', 'NATIONALUM', 'PNB']
YEARS       = [2023, 2024, 2025]
TB_VARIANTS = [3, 9]
N_TRIALS    = 500

DATA_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
SIG_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OPT_BASE = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna"

os.makedirs(SIG_DIR, exist_ok=True)
for y in YEARS:
    os.makedirs(os.path.join(OPT_BASE, str(y)), exist_ok=True)

# ─── Signal export ─────────────────────────────────────────────────────────────
def export_signals(stock, year, max_tb_gap):
    csv_path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    out_file = os.path.join(SIG_DIR, f"{stock.lower()}_{year}_h5_signals_tb{max_tb_gap}.csv")

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df = df[df['datetime'].dt.year == year].copy().reset_index(drop=True)
    if len(df) == 0: return 0

    prev_close   = df['close'].shift(1)
    df['tr']     = np.maximum(df['high']-df['low'],
                   np.maximum(abs(df['high']-prev_close), abs(df['low']-prev_close)))
    df['atr14']  = df['tr'].rolling(14, min_periods=14).mean()
    df['vol_ma20'] = df['volume'].rolling(20, min_periods=20).mean()
    df['vr']     = df['volume'] / df['vol_ma20']
    df['day_idx'] = df.groupby('date').cumcount()

    signals = []
    i = 20
    while i < len(df) - 2:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1; continue
        if row['low'] <= row['ma20']:
            T0=i; t0_date=row['date']; t0r=df.iloc[T0]
            bounce_bar=None
            for j in range(T0, min(T0+max_tb_gap+1, len(df)-1)):
                brow=df.iloc[j]
                if brow['date']!=t0_date: break
                if brow['close']>brow['ma20']: bounce_bar=j; break
            if bounce_bar is None: i+=1; continue
            entry_bar=bounce_bar+1
            if entry_bar>=len(df) or df.iloc[entry_bar]['date']!=t0_date: i+=1; continue
            bounce_bar_index=bounce_bar-T0
            br=df.iloc[bounce_bar]; er=df.iloc[entry_bar]
            if er['datetime'].time()>=pd.Timestamp('14:40').time(): i+=1; continue

            p01=((t0r['ma20']-df.iloc[T0-5]['ma20'])/t0r['ma20'])*100 \
                if t0r['day_idx']>=5 and df.iloc[T0-5]['date']==t0_date else np.nan
            p02=((df.iloc[T0-3]['ma20']-df.iloc[T0-8]['ma20'])/df.iloc[T0-3]['ma20'])*100 \
                if t0r['day_idx']>=8 and df.iloc[T0-8]['date']==t0_date \
                and pd.notna(df.iloc[T0-3]['ma20']) and df.iloc[T0-3]['ma20']!=0 else np.nan
            p03=0
            for k in range(T0-1,-1,-1):
                bk=df.iloc[k]
                if bk['date']!=t0_date: break
                if pd.notna(bk['ma20']) and bk['low']>bk['ma20']: p03+=1
                else: break
            swing_idx,best_high=None,-np.inf
            for k in range(T0-1,-1,-1):
                bk=df.iloc[k]
                if bk['date']!=t0_date: break
                if bk['low']<=bk['ma20']: break
                if bk['high']>=best_high: best_high=bk['high']; swing_idx=k
            p04=(T0-swing_idx) if swing_idx is not None else np.nan
            atr=t0r['atr14']
            p05=(t0r['ma20']-t0r['low'])/atr if atr>0 else np.nan
            cr=t0r['high']-t0r['low']
            p06=(abs(t0r['close']-t0r['open'])/cr*100) if cr>0 else 100.0
            ma20=t0r['ma20']; body_low=min(t0r['open'],t0r['close']); denom=ma20-t0r['low']
            if denom==0: p07,p07_na=np.nan,1
            else: p07,p07_na=round((body_low-ma20)/denom,4),0
            p08=br['vr'] if pd.notna(br['vr']) else np.nan
            same_candle=1 if bounce_bar==T0 else 0
            p09=np.nan if (same_candle or pd.isna(br['vr']) or pd.isna(t0r['vr'])) \
                else (1 if br['vr']>t0r['vr'] else 0)
            p11=1 if er['close']>br['close'] else 0
            p11=1 if er['open']>br['close'] else 0
            p12=(1 if er['vr']>=br['vr'] else 0) \
                if (pd.notna(er['vr']) and pd.notna(br['vr'])) else np.nan

            entry_price=er['open']; sl=entry_price-(2.5*atr); target=entry_price+(4.5*atr)
            outcome,pnl,exit_bar=None,None,None
            for j in range(entry_bar,len(df)):
                bar=df.iloc[j]
                if bar['low']<=sl and bar['high']>=target:
                    outcome,pnl=('L',round(-2.5*atr,4)) if abs(bar['open']-sl)<=abs(bar['open']-target) else ('W',round(4.5*atr,4))
                    exit_bar=j; break
                if bar['low']<=sl: outcome,pnl='L',round(-2.5*atr,4); exit_bar=j; break
                if bar['high']>=target: outcome,pnl='W',round(4.5*atr,4); exit_bar=j; break
                if bar['datetime'].time()>=pd.Timestamp('15:00').time():
                    pnl=round(bar['open']-entry_price,2)
                    outcome='EOD+' if bar['open']>entry_price else 'EOD-'
                    exit_bar=j; break
                if bar['date']!=t0_date:
                    last=df.iloc[j-1]
                    pnl=round(last['close']-entry_price,2)
                    outcome='EOD+' if last['close']>entry_price else 'EOD-'
                    exit_bar=j-1; break
            else:
                last=df.iloc[-1]
                pnl=round(last['close']-entry_price,4)
                outcome='EOD+' if last['close']>entry_price else 'EOD-'
                exit_bar=len(df)-1

            signals.append({
                'signal_id':f"S{len(signals)+1:03d}",'stock':stock,
                'datetime':t0r['datetime'],
                'p01':round(p01,4) if pd.notna(p01) else np.nan,
                'p02':round(p02,4) if pd.notna(p02) else np.nan,
                'p03':int(p03),
                'p04':int(p04) if pd.notna(p04) else np.nan,
                'p05':round(float(p05),4) if pd.notna(p05) else np.nan,
                'p06':round(float(p06),2) if pd.notna(p06) else np.nan,
                'p07':p07 if pd.notna(p07) else np.nan,'p07_na':p07_na,
                'p08':round(float(p08),4) if pd.notna(p08) else np.nan,
                'p09':p09,'p10':bounce_bar_index,
                'p11':p11,'p11':p11,'p12':p12,
                'same_candle_tb':same_candle,
                'bounce_bar_index':bounce_bar_index,
                'entry_bar_index':bounce_bar_index+1,
                'bounce_datetime':df.iloc[bounce_bar]['datetime'],
                'entry_datetime':df.iloc[entry_bar]['datetime'],
                'exit_datetime':df.iloc[exit_bar]['datetime'],
                'entry_price':entry_price,'sl':sl,'target':target,
                'pnl':pnl,'outcome':outcome,
            })
            i=entry_bar+1
        else:
            i+=1

    pd.DataFrame(signals).to_csv(out_file, index=False, encoding='utf-8', lineterminator='\n')
    return len(signals)

# ─── Gate eval ─────────────────────────────────────────────────────────────────
def _agg(results):
    non_na=[r for r in results if r!='NA']
    if not non_na: return 'NA'
    return 'P' if all(r=='P' for r in non_na) else 'F'

def eval_signal(sig, p, af):
    def fval(col):
        v=sig.get(col,np.nan)
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

def compute_metrics(passing):
    n=len(passing)
    if n==0: return dict(n=0,pf=0,wr=0,net_pnl=0)
    pnls=[s['pnl'] for s in passing]
    gp=sum(x for x in pnls if x>0); gl=abs(sum(x for x in pnls if x<0))
    pf=gp/gl if gl>0 else 9999.0
    wins=sum(1 for s in passing if str(s.get('outcome','')).strip() in ('W','EOD+'))
    return dict(n=n,pf=pf,wr=wins/n,net_pnl=sum(pnls))

# ─── Optuna objective ──────────────────────────────────────────────────────────
def make_objective(signals, p10_max, n_target):
    def objective(trial):
        p01_on=trial.suggest_categorical('p01_on',[True,False]); p01=trial.suggest_float('p01',0.01,0.50)
        p02_on=trial.suggest_categorical('p02_on',[True,False]); p02=trial.suggest_float('p02',0.01,0.20)
        p03_on=trial.suggest_categorical('p03_on',[True,False]); p03=trial.suggest_int('p03',1,15)
        p04_on=trial.suggest_categorical('p04_on',[True,False])
        p04_min=trial.suggest_int('p04_min',1,10)
        p04_max=max(p04_min,trial.suggest_int('p04_max',1,20))
        p05_on=trial.suggest_categorical('p05_on',[True,False])
        p05_min=trial.suggest_float('p05_min',0.0,2.0)
        p05_max=max(p05_min,trial.suggest_float('p05_max',0.0,4.0))
        p06_on=trial.suggest_categorical('p06_on',[True,False]); p06=trial.suggest_int('p06',20,100,step=5)
        p07_on=trial.suggest_categorical('p07_on',[True,False]); p07=trial.suggest_float('p07',-1.5,5.0)
        p08_on=trial.suggest_categorical('p08_on',[True,False]); p08=trial.suggest_float('p08',0.3,3.0)
        p09_on=trial.suggest_categorical('p09',[True,False])
        p10_on=trial.suggest_categorical('p10_on',[True,False]); p10=trial.suggest_int('p10',0,p10_max)
        p11_on=trial.suggest_categorical('p11',[True,False])
        p12_on=False
        af={'p01':p01_on,'p02':p02_on,'p03':p03_on,'p04':p04_on,
            'p05':p05_on,'p06':p06_on,'p07':p07_on,'p08':p08_on,
            'p09':p09_on,'p10':p10_on,'p11':p11_on,'p12':p12_on}
        p={'p01':p01,'p02':p02,'p03':p03,'p04min':p04_min,'p04max':p04_max,
           'p05min':p05_min,'p05max':p05_max,'p06':p06,'p07':p07,'p08':p08,'p10':p10}
        passing=[s for s in signals if eval_signal(s,p,af)]
        m=compute_metrics(passing)
        if m['n']<n_target: return -1e9
        if m['pf']<1.3:     return -1e9
        return m['pf']*(min(m['n'],n_target)/n_target)**0.5
    return objective

# ─── Run ──────────────────────────────────────────────────────────────────────
print(f"Cross-validation: {len(STOCKS)} stocks × {YEARS} × {TB_VARIANTS} variants × {N_TRIALS} trials\n")

for year in YEARS:
    print(f"{'='*60}")
    print(f"YEAR: {year}")
    print(f"{'='*60}")
    for stock in STOCKS:
        for tb in TB_VARIANTS:
            sig_file = os.path.join(SIG_DIR, f"{stock.lower()}_{year}_h5_signals_tb{tb}.csv")
            out_file = os.path.join(OPT_BASE, str(year), f"{stock.lower()}_{year}_optuna_tb{tb}.json")

            # Export signals
            n_sig = export_signals(stock, year, tb)
            print(f"  {stock} tb{tb} ({year}): {n_sig} signals", end='', flush=True)

            if n_sig == 0:
                print(" -> skipped (no data)")
                continue

            df = pd.read_csv(sig_file)
            df.columns = df.columns.str.strip()
            signals = df.to_dict('records')
            n_target = max(8, int(len(signals)*0.10))

            seed={'p01_on':False,'p01':0.05,'p02_on':False,'p02':0.05,
                  'p03_on':False,'p03':1,'p04_on':False,'p04_min':3,'p04_max':8,
                  'p05_on':True,'p05_min':0.0,'p05_max':1.6,
                  'p06_on':False,'p06':50,'p07_on':False,'p07':1.0,
                  'p08_on':True,'p08':0.5,
                  'p09':False,'p10_on':False,'p10':min(5,tb),
                  'p11':True,'p12':False}

            study=optuna.create_study(direction='maximize')
            study.enqueue_trial(seed)
            study.optimize(make_objective(signals,tb,n_target),n_trials=N_TRIALS,show_progress_bar=False)

            bp=study.best_trial.params
            p04mxf=max(bp['p04_min'],bp['p04_max']); p05mxf=max(bp['p05_min'],bp['p05_max'])
            af_best={'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
                     'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
                     'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':False}
            p_best={'p01':round(bp['p01'],4),'p02':round(bp['p02'],4),'p03':bp['p03'],
                    'p04min':bp['p04_min'],'p04max':p04mxf,
                    'p05min':round(bp['p05_min'],4),'p05max':round(p05mxf,4),
                    'p06':bp['p06'],'p07':round(bp['p07'],4),'p08':round(bp['p08'],4),'p10':bp['p10']}
            passing=[s for s in signals if eval_signal(s,p_best,af_best)]
            m=compute_metrics(passing)

            result={
                'stock':stock,'year':year,'tb_variant':tb,'n_trials':N_TRIALS,
                'best_score':round(study.best_value,4),
                'n_total':len(signals),'n_passing':m['n'],
                'pf':round(m['pf'],4),'wr':round(m['wr'],4),'net_pnl':round(m['net_pnl'],4),
                'best_params':{
                    'p01':round(bp['p01'],4),'p01_on':bp['p01_on'],
                    'p02':round(bp['p02'],4),'p02_on':bp['p02_on'],
                    'p03':bp['p03'],'p03_on':bp['p03_on'],
                    'p04_min':bp['p04_min'],'p04_max':p04mxf,'p04_on':bp['p04_on'],
                    'p05_min':round(bp['p05_min'],4),'p05_max':round(p05mxf,4),'p05_on':bp['p05_on'],
                    'p06':bp['p06'],'p06_on':bp['p06_on'],
                    'p07':round(bp['p07'],4),'p07_on':bp['p07_on'],
                    'p08':round(bp['p08'],4),'p08_on':bp['p08_on'],
                    'p09':bp['p09'],
                    'p10':bp['p10'],'p10_on':bp['p10_on'],
                    'p11':bp['p11'],
                    'p12':False,
                }
            }
            with open(out_file,'w') as f:
                json.dump(result,f,indent=2)

            print(f" -> N={m['n']} WR={m['wr']:.1%} PF={m['pf']:.2f} Score={study.best_value:.4f}")

print("\nDone.")
