"""
WFA — Walk-Forward Analysis
Train: 2022 (params locked in Optuna JSONs)
Test : 2023, 2024, 2025 — frozen params, no re-optimization
Stocks: 5 both-clear stocks (tb3 + tb9)
Output: PF / WR / R/R / N per stock × year × variant
"""
import pandas as pd
import numpy as np
import os
import json

STOCKS      = ['POWERGRID', 'HDFCBANK', 'ITC', 'NATIONALUM', 'PNB']
TRAIN_YEAR  = 2022
TEST_YEARS  = [2023, 2024, 2025]
TB_VARIANTS = [3, 9]

DATA_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
OPT_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\2022"

# ─── Gate eval (same as batch — p11_open, p12 dropped) ────────────────────────
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
    p05v=fval('p05'); p07v=fval('p07'); p07na=int(fval('p07_na') or 0); p08v=fval('p08')
    p09raw=sig.get('p09','')
    p09v=None if str(p09raw).strip() in ('','NaN','nan') else int(float(p09raw))
    bounce_idx=fval('bounce_bar_index')
    p11v=int(float(sig.get('p11_open', 0)))
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

def metrics(passing):
    n = len(passing)
    if n == 0: return dict(n=0, wr=0, pf=0, rr=0, net=0)
    pnls = [s['pnl'] for s in passing]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp = sum(wins); gl = abs(sum(losses))
    pf = round(gp/gl, 2) if gl else 9999
    wr = round(len(wins)/n*100, 1)
    avg_w = np.mean(wins) if wins else 0
    avg_l = abs(np.mean(losses)) if losses else 0
    rr = round(avg_w/avg_l, 2) if avg_l else 9999
    net = round(sum(pnls), 2)
    return dict(n=n, wr=wr, pf=pf, rr=rr, net=net)

# ─── Signal export (inline — no file write) ───────────────────────────────────
def export_signals_inmem(stock, year, max_tb_gap):
    csv_path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df = df[df['datetime'].dt.year == year].copy().reset_index(drop=True)
    if len(df) == 0: return []

    prev_close  = df['close'].shift(1)
    df['tr']    = np.maximum(df['high']-df['low'],
                  np.maximum(abs(df['high']-prev_close), abs(df['low']-prev_close)))
    df['atr14'] = df['tr'].rolling(14, min_periods=14).mean()
    df['vol_ma20'] = df['volume'].rolling(20, min_periods=20).mean()
    df['vr']    = df['volume'] / df['vol_ma20']
    df['day_idx'] = df.groupby('date').cumcount()

    signals = []
    i = 20
    while i < len(df) - 2:
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1; continue
        if row['low'] <= row['ma20']:
            T0 = i; t0_date = row['date']; t0r = df.iloc[T0]
            bounce_bar = None
            for j in range(T0, min(T0+max_tb_gap+1, len(df)-1)):
                brow = df.iloc[j]
                if brow['date'] != t0_date: break
                if brow['close'] > brow['ma20']:
                    bounce_bar = j; break
            if bounce_bar is None: i += 1; continue
            entry_bar = bounce_bar + 1
            if entry_bar >= len(df) or df.iloc[entry_bar]['date'] != t0_date:
                i += 1; continue
            bounce_bar_index = bounce_bar - T0
            br = df.iloc[bounce_bar]; er = df.iloc[entry_bar]
            if er['datetime'].time() >= pd.Timestamp('14:40').time():
                i += 1; continue

            p01 = ((t0r['ma20']-df.iloc[T0-5]['ma20'])/t0r['ma20'])*100 \
                  if t0r['day_idx']>=5 and df.iloc[T0-5]['date']==t0_date else np.nan
            p02 = ((df.iloc[T0-3]['ma20']-df.iloc[T0-8]['ma20'])/df.iloc[T0-3]['ma20'])*100 \
                  if t0r['day_idx']>=8 and df.iloc[T0-8]['date']==t0_date \
                  and pd.notna(df.iloc[T0-3]['ma20']) and df.iloc[T0-3]['ma20']!=0 else np.nan
            p03 = 0
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
            p11_open=1 if er['open']>br['close'] else 0

            entry_price=er['open']; sl=entry_price-(2.5*atr); target=entry_price+(4.5*atr)
            outcome,pnl,exit_bar=None,None,None
            for j in range(entry_bar,len(df)):
                bar=df.iloc[j]
                if bar['low']<=sl and bar['high']>=target:
                    if abs(bar['open']-sl)<=abs(bar['open']-target):
                        outcome,pnl='L',round(-2.5*atr,4)
                    else:
                        outcome,pnl='W',round(4.5*atr,4)
                    exit_bar=j; break
                if bar['low']<=sl:
                    outcome,pnl='L',round(-2.5*atr,4); exit_bar=j; break
                if bar['high']>=target:
                    outcome,pnl='W',round(4.5*atr,4); exit_bar=j; break
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
                'p01':round(p01,4) if pd.notna(p01) else np.nan,
                'p02':round(p02,4) if pd.notna(p02) else np.nan,
                'p03':int(p03),
                'p04':int(p04) if pd.notna(p04) else np.nan,
                'p05':round(float(p05),4) if pd.notna(p05) else np.nan,
                'p06':round(float(p06),2) if pd.notna(p06) else np.nan,
                'p07':p07 if pd.notna(p07) else np.nan, 'p07_na':p07_na,
                'p08':round(float(p08),4) if pd.notna(p08) else np.nan,
                'p09':p09, 'p10':bounce_bar_index,
                'p11_open':p11_open,
                'bounce_bar_index':bounce_bar_index,
                'pnl':pnl, 'outcome':outcome,
            })
            i = entry_bar + 1
        else:
            i += 1
    return signals

# ─── Run WFA ──────────────────────────────────────────────────────────────────
print(f"WFA — Train: {TRAIN_YEAR} | Test: {TEST_YEARS}")
print(f"Stocks: {STOCKS}\n")

# Print header
hdr = f"{'Stock':12s}  {'TB':>3}  {'Metric':>6}"
for y in [TRAIN_YEAR] + TEST_YEARS:
    hdr += f"  {str(y):>10}"
print(hdr)
print('-' * (len(hdr) + 10))

for stock in STOCKS:
    for tb in TB_VARIANTS:
        # Load frozen 2022 params
        with open(f'{OPT_DIR}/{stock.lower()}_2022_optuna_tb{tb}.json') as f:
            j = json.load(f)
        bp = j['best_params']
        p04mxf = max(bp['p04_min'], bp['p04_max'])
        p05mxf = max(bp['p05_min'], bp['p05_max'])
        af = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
              'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
              'p09':bp['p09'],'p10':bp['p10_on'],'p11':bp['p11'],'p12':False}
        p = {'p01':bp['p01'],'p02':bp['p02'],'p03':bp['p03'],
             'p04min':bp['p04_min'],'p04max':p04mxf,
             'p05min':bp['p05_min'],'p05max':p05mxf,
             'p06':bp['p06'],'p07':bp['p07'],'p08':bp['p08'],'p10':bp['p10']}

        row_n=''; row_wr=''; row_pf=''; row_rr=''
        for year in [TRAIN_YEAR] + TEST_YEARS:
            sigs = export_signals_inmem(stock, year, tb)
            passing = [s for s in sigs if eval_signal(s, p, af)]
            m = metrics(passing)
            row_n  += f"  {m['n']:>10}"
            row_wr += f"  {str(m['wr'])+'%':>10}"
            row_pf += f"  {m['pf']:>10}"
            row_rr += f"  {m['rr']:>10}"

        tag = f"{stock:12s}  tb{tb}"
        print(f"{tag}  {'N':>6}{row_n}")
        print(f"{'':12s}  {'':3}  {'WR':>6}{row_wr}")
        print(f"{'':12s}  {'':3}  {'PF':>6}{row_pf}")
        print(f"{'':12s}  {'':3}  {'R/R':>6}{row_rr}")
        print()
