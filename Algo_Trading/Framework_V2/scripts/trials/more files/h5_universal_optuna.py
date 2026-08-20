"""
H5 Universal Optuna — one parameter set across all 30 stocks × 2022-2025 (tb3)
Objective : maximize pooled PF
Floors    : per-stock N_pass >= 5% of stock total; pooled PF > 1.0
N_trials  : 2000
"""
import pandas as pd
import numpy as np
import optuna
import os
from datetime import datetime

optuna.logging.set_verbosity(optuna.logging.WARNING)

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]
YEARS    = [2022, 2023, 2024, 2025]
TB       = 3
N_TRIALS = 2000
SIG_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"
OUT_DIR  = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\optuna\universal"

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
    p11v = int(float(sig.get('p11', 0)))

    g1_01 = 'P' if not af['p01'] else ('NA' if np.isnan(p01v) else ('P' if p01v >= p['p01'] else 'F'))
    g1_02 = 'P' if not af['p02'] else ('NA' if np.isnan(p02v) else ('P' if p02v >= p['p02'] else 'F'))
    g1_03 = 'P' if not af['p03'] else ('P' if p03v >= p['p03'] else 'F')
    if not af['p04']:        g1_04 = 'P'
    elif g1_03 == 'F':       g1_04 = 'NA'
    elif np.isnan(p04v):     g1_04 = 'NA'
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
    g3 = _agg([g3_11])

    return g1 == 'P' and g2 == 'P' and g3 == 'P'

def compute_metrics(signals):
    n = len(signals)
    if n == 0:
        return dict(n=0, pf=0.0, wr=0.0, net_pnl=0.0, sharpe=0.0)
    pnls = [float(s['pnl']) for s in signals]
    gp = sum(x for x in pnls if x > 0)
    gl = abs(sum(x for x in pnls if x < 0))
    pf = gp / gl if gl > 0 else 9999.0
    wins = sum(1 for s in signals if str(s.get('outcome', '')).strip() in ('W', 'EOD+'))
    std_pnl = np.std(pnls, ddof=1) if n > 1 else 0.0
    sharpe = (np.mean(pnls) / std_pnl) if std_pnl > 0 else 0.0
    return dict(n=n, pf=pf, wr=wins / n, net_pnl=sum(pnls), sharpe=sharpe)

# ─── Load all signals ─────────────────────────────────────────────────────────
print("Loading signals...")
all_signals = []
stock_signals = {s: [] for s in STOCKS}
missing = []

for stock in STOCKS:
    for year in YEARS:
        fname = f"{stock.lower()}_{year}_h5_signals_tb{TB}.csv"
        fpath = os.path.join(SIG_DIR, fname)
        if not os.path.exists(fpath):
            missing.append(fname)
            continue
        df = pd.read_csv(fpath)
        df.columns = df.columns.str.strip()
        rows = df.to_dict('records')
        stock_signals[stock].extend(rows)
        all_signals.extend(rows)

stock_totals = {s: len(stock_signals[s]) for s in STOCKS}

if missing:
    print(f"  WARNING: {len(missing)} files not found — {missing[:5]}{'...' if len(missing)>5 else ''}")

print(f"  Loaded {len(all_signals):,} signals across {len(STOCKS)} stocks × {len(YEARS)} years")
for s in STOCKS:
    print(f"    {s:<14}: {stock_totals[s]:>4} signals  (floor >= {max(1, int(stock_totals[s]*0.05))})")

# ─── Optuna objective ─────────────────────────────────────────────────────────
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
    p10     = trial.suggest_int('p10', 0, 3)
    p11_on  = trial.suggest_categorical('p11', [True, False])

    af = {'p01':p01_on,'p02':p02_on,'p03':p03_on,'p04':p04_on,
          'p05':p05_on,'p06':p06_on,'p07':p07_on,'p08':p08_on,
          'p09':p09_on,'p10':p10_on,'p11':p11_on,'p12':False}
    p  = {'p01':p01,'p02':p02,'p03':p03,'p04min':p04_min,'p04max':p04_max,
          'p05min':p05_min,'p05max':p05_max,'p06':p06,'p07':p07,'p08':p08,'p10':p10}

    # Single pass: evaluate all signals, group by stock
    passing_by_stock = {s: [] for s in STOCKS}
    for sig in all_signals:
        if eval_signal(sig, p, af):
            passing_by_stock[sig['stock']].append(sig)

    # Soft coverage: fraction of stocks meeting 5% floor
    stocks_ok = sum(
        1 for stock in STOCKS
        if stock_totals[stock] > 0 and len(passing_by_stock[stock]) >= max(1, stock_totals[stock] * 0.05)
    )
    coverage = stocks_ok / len(STOCKS)  # 0.0 – 1.0

    # Pooled PF — no hard floor, let Optuna maximize naturally
    all_passing = [s for sigs in passing_by_stock.values() for s in sigs]
    if not all_passing:
        return -1e9
    m = compute_metrics(all_passing)

    # score = PF × coverage — both dimensions pulled upward simultaneously
    return m['pf'] * coverage

# ─── Run ──────────────────────────────────────────────────────────────────────
seed = {
    'p01_on':False,'p01':0.05,'p02_on':False,'p02':0.05,
    'p03_on':False,'p03':1,'p04_on':False,'p04_min':3,'p04_max':8,
    'p05_on':True,'p05_min':0.0,'p05_max':1.6,
    'p06_on':False,'p06':50,'p07_on':False,'p07':1.0,
    'p08_on':True,'p08':0.5,
    'p09':False,'p10_on':False,'p10':3,'p11':True,
}

print(f"\nRunning Optuna: {N_TRIALS} trials | universal | tb{TB} | objective: pooled PF × coverage(5% floor)")
print("Estimated runtime: 3–6 minutes\n")

study = optuna.create_study(direction='maximize')
study.enqueue_trial(seed)
study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

if study.best_value <= 0:
    print("\nNo valid trial found — all trials failed the 5% per-stock floor or PF > 1.0.")
    print("Consider loosening floors and re-running.")
    raise SystemExit(1)

# ─── Best params ──────────────────────────────────────────────────────────────
bp = study.best_trial.params
p04_max_f = max(bp['p04_min'], bp['p04_max'])
p05_max_f = max(bp['p05_min'], bp['p05_max'])

af_best = {'p01':bp['p01_on'],'p02':bp['p02_on'],'p03':bp['p03_on'],'p04':bp['p04_on'],
           'p05':bp['p05_on'],'p06':bp['p06_on'],'p07':bp['p07_on'],'p08':bp['p08_on'],
           'p09':bp['p09'],   'p10':bp['p10_on'],'p11':bp['p11'],   'p12':False}
p_best  = {'p01':round(bp['p01'],4),'p02':round(bp['p02'],4),'p03':bp['p03'],
           'p04min':bp['p04_min'],'p04max':p04_max_f,
           'p05min':round(bp['p05_min'],4),'p05max':round(p05_max_f,4),
           'p06':bp['p06'],'p07':round(bp['p07'],4),'p08':round(bp['p08'],4),'p10':bp['p10']}

# ─── Per-stock results with best params ───────────────────────────────────────
stock_rows = []
for stock in STOCKS:
    sigs = stock_signals[stock]
    passing = [s for s in sigs if eval_signal(s, p_best, af_best)]
    m = compute_metrics(passing)
    stock_rows.append({
        'stock': stock,
        'n_total': stock_totals[stock],
        'n_pass': m['n'],
        'pass_pct': round(m['n'] / max(stock_totals[stock], 1) * 100, 1),
        'wr_pct': round(m['wr'] * 100, 1),
        'pf': round(m['pf'], 3),
        'net_pnl': round(m['net_pnl'], 2),
        'sharpe': round(m['sharpe'], 3),
    })

all_passing = [s for s in all_signals if eval_signal(s, p_best, af_best)]
agg = compute_metrics(all_passing)

# ─── Terminal output ──────────────────────────────────────────────────────────
W = 80
print("\n" + "═"*W)
print("  UNIVERSAL OPTIMAL PARAMETER SET")
print("═"*W)
print(f"  Best score (PF): {study.best_value:.4f}  |  Trials: {N_TRIALS}  |  TB: tb{TB}")
print(f"  Stocks: {len(STOCKS)}  |  Years: {YEARS[0]}–{YEARS[-1]}  |  Total signals: {len(all_signals):,}")
print()
print(f"  {'PARAM':<10} {'ON':>6} {'VALUE':>12}")
print(f"  {'-'*30}")
print(f"  {'p01':<10} {str(bp['p01_on']):>6}  {bp['p01']:>12.4f}")
print(f"  {'p02':<10} {str(bp['p02_on']):>6}  {bp['p02']:>12.4f}")
print(f"  {'p03':<10} {str(bp['p03_on']):>6}  {bp['p03']:>12}")
print(f"  {'p04':<10} {str(bp['p04_on']):>6}  min={bp['p04_min']} max={p04_max_f}")
print(f"  {'p05':<10} {str(bp['p05_on']):>6}  min={bp['p05_min']:.4f} max={p05_max_f:.4f}")
print(f"  {'p06':<10} {str(bp['p06_on']):>6}  {bp['p06']:>12}")
print(f"  {'p07':<10} {str(bp['p07_on']):>6}  {bp['p07']:>12.4f}")
print(f"  {'p08':<10} {str(bp['p08_on']):>6}  {bp['p08']:>12.4f}")
print(f"  {'p09':<10} {str(bp['p09']):>6}  {'(toggle)':>12}")
print(f"  {'p10':<10} {str(bp['p10_on']):>6}  {bp['p10']:>12}")
print(f"  {'p11':<10} {str(bp['p11']):>6}  {'(toggle)':>12}")

print()
print(f"  {'STOCK':<14} {'N_TOT':>6} {'N_PASS':>7} {'PASS%':>6} {'WR%':>6} {'PF':>7} {'NET_PNL':>12} {'SHARPE':>8}")
print("  " + "─"*(W-2))
for r in stock_rows:
    print(f"  {r['stock']:<14} {r['n_total']:>6} {r['n_pass']:>7} {r['pass_pct']:>5.1f}% "
          f"{r['wr_pct']:>5.1f}% {r['pf']:>7.3f} {r['net_pnl']:>12,.0f} {r['sharpe']:>8.3f}")
print("  " + "─"*(W-2))
print(f"  {'AGGREGATE':<14} {len(all_signals):>6} {agg['n']:>7} "
      f"{agg['n']/len(all_signals)*100:>5.1f}% "
      f"{agg['wr']*100:>5.1f}% {agg['pf']:>7.3f} {agg['net_pnl']:>12,.0f} {agg['sharpe']:>8.3f}")
print("═"*W)

# ─── Save CSV ─────────────────────────────────────────────────────────────────
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out_csv = os.path.join(OUT_DIR, f"universal_optuna_{ts}.csv")

param_row = {
    'type':'params','stock':'','n_total':'','n_pass':'','pass_pct':'','wr_pct':'','pf':'','net_pnl':'','sharpe':'',
    'best_score':round(study.best_value,4),
    'p01_on':bp['p01_on'],'p01':round(bp['p01'],4),
    'p02_on':bp['p02_on'],'p02':round(bp['p02'],4),
    'p03_on':bp['p03_on'],'p03':bp['p03'],
    'p04_on':bp['p04_on'],'p04_min':bp['p04_min'],'p04_max':p04_max_f,
    'p05_on':bp['p05_on'],'p05_min':round(bp['p05_min'],4),'p05_max':round(p05_max_f,4),
    'p06_on':bp['p06_on'],'p06':bp['p06'],
    'p07_on':bp['p07_on'],'p07':round(bp['p07'],4),
    'p08_on':bp['p08_on'],'p08':round(bp['p08'],4),
    'p09_on':bp['p09'],'p10_on':bp['p10_on'],'p10':bp['p10'],'p11_on':bp['p11'],
}
stock_out = [{'type':'stock','best_score':'', **r,
              'p01_on':'','p01':'','p02_on':'','p02':'','p03_on':'','p03':'',
              'p04_on':'','p04_min':'','p04_max':'','p05_on':'','p05_min':'','p05_max':'',
              'p06_on':'','p06':'','p07_on':'','p07':'','p08_on':'','p08':'',
              'p09_on':'','p10_on':'','p10':'','p11_on':''} for r in stock_rows]
agg_out = {'type':'aggregate','stock':'ALL','n_total':len(all_signals),'n_pass':agg['n'],
           'pass_pct':round(agg['n']/len(all_signals)*100,1),
           'wr_pct':round(agg['wr']*100,1),'pf':round(agg['pf'],3),
           'net_pnl':round(agg['net_pnl'],2),'sharpe':round(agg['sharpe'],3),
           'best_score':'','p01_on':'','p01':'','p02_on':'','p02':'','p03_on':'','p03':'',
           'p04_on':'','p04_min':'','p04_max':'','p05_on':'','p05_min':'','p05_max':'',
           'p06_on':'','p06':'','p07_on':'','p07':'','p08_on':'','p08':'',
           'p09_on':'','p10_on':'','p10':'','p11_on':''}

pd.DataFrame([param_row] + stock_out + [agg_out]).to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")
