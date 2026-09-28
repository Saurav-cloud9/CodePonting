"""
Step 54b — Table 3 SL-sweep for FLAGSHIP_6BCEH_SHORT_VWAP_RSI60.

Table 2 (healthy subset, EOD% <= 30) put the best ZPF at SL=1.5 / TP=4.5-5.0 (0.899) —
but SL sat at the grid floor and the whole SL=1.5 row still climbed as SL tightened.
This sweep extends SL well below 1.5 (fine 0.25 steps) at three fixed TPs and tracks
ZPF + net_zpnl + CAPM alpha (basket primary, NIFTY cross-check) together, to find where —
or whether — they genuinely co-peak vs. keep drifting to the edge.

Reuses the exact engine from strategies/flagship/11_6bceh_short_vwap_rsi.py
(load_stocks / run_combo / add_vwap / add_rsi_wilder / zerodha_charge), RSI threshold
fixed at 60 (the Step A winner). No changes to signal/filter/exit logic.

Output: 54b_table3_sl_sweep_results.csv (one row per SL x TP), plus printed per-TP tables.
"""
import sys, io, types, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
import numpy as np
from scipy import stats

ENGINE = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/strategies/flagship/11_6bceh_short_vwap_rsi.py'
NIFTY_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet'
DS3_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RSI_THRESH = 60
# SL capped at 1.0 (practical floor — a sub-1.0xATR stop is noise-width and degenerate,
# not a real strategy). Table 2's healthy peak was SL=1.5 at the grid floor; this checks
# whether 1.5 is a genuine edge or still climbing toward 1.0.
SL_VALS = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
TP_VALS = [3.0, 4.5, 5.0]

# ── load the engine's functions (strip stdout re-wrap + MAIN) ──────────────────
with open(ENGINE) as f:
    src = f.read().split('# ── MAIN')[0]
src = src.replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n", '')
eng = types.ModuleType('eng')
eng.__dict__['__file__'] = ENGINE
exec(compile(src, ENGINE, 'exec'), eng.__dict__)

# ── market factors ────────────────────────────────────────────────────────────
nifty = pd.read_parquet(NIFTY_PATH)
nifty['date'] = pd.to_datetime(nifty['datetime']).dt.date
nifty = nifty.sort_values('date').reset_index(drop=True)
nifty['ret_pct'] = nifty['close'].pct_change() * 100
nifty_daily = nifty[['date', 'ret_pct']].dropna()

basket_rows = []
for f in sorted(glob.glob(os.path.join(DS3_DIR, '*.parquet'))):
    d = pd.read_parquet(f, columns=['datetime', 'close'])
    d['datetime'] = pd.to_datetime(d['datetime'])
    if d['datetime'].dt.tz is not None:
        d['datetime'] = d['datetime'].dt.tz_localize(None)
    d['date'] = d['datetime'].dt.date
    basket_rows.append(d.groupby('date')['close'].last())
basket_df = pd.concat(basket_rows, axis=1).mask(lambda x: x <= 0)
basket_daily = (basket_df.pct_change().mean(axis=1, skipna=True).dropna() * 100).reset_index()
basket_daily.columns = ['date', 'ret_pct']


def capm(y, x):
    n = len(y)
    xm, ym = x.mean(), y.mean()
    sxx = ((x - xm) ** 2).sum()
    beta = ((x - xm) * (y - ym)).sum() / sxx
    alpha = ym - beta * xm
    resid = y - (alpha + beta * x)
    dof = n - 2
    s2 = (resid ** 2).sum() / dof
    se = np.sqrt(s2 * (1 / n + xm ** 2 / sxx))
    tc = stats.t.ppf(0.975, dof)
    return dict(alpha=alpha, beta=beta, se=se, t=alpha / se,
                p=2 * stats.t.sf(abs(alpha / se), dof),
                ci_lo=alpha - tc * se, ci_hi=alpha + tc * se, n=n)


def alpha_row(zpnl_arr, dates_arr, market_daily):
    dd = pd.to_datetime(pd.Series(dates_arr)).dt.date
    daily = pd.DataFrame({'zpnl': zpnl_arr, 'date': dd}).groupby('date')['zpnl'].sum().reset_index()
    m = daily.merge(market_daily, on='date', how='inner')
    c = capm(m['zpnl'].values, m['ret_pct'].values)
    c['alpha_cum'] = c['alpha'] * c['n']
    return c


print('Loading stocks (+ VWAP + RSI)...')
stocks = eng.load_stocks()
print(f'Loaded {len(stocks)} stocks. Sweeping {len(SL_VALS)} SL x {len(TP_VALS)} TP = '
      f'{len(SL_VALS) * len(TP_VALS)} combos at RSI>{RSI_THRESH}...\n')

rows = []
for tp in TP_VALS:
    print(f'{"="*118}\nTP = {tp}   (fixed)   |   SL sweep {SL_VALS[0]} -> {SL_VALS[-1]}')
    print(f'{"="*118}')
    print(f'  {"SL":>5} {"N":>8} {"PF":>7} {"ZPF":>7} {"net_zpnl":>12} {"aB":>8} {"aB_CI":>18} '
          f'{"pB":>6} {"aN":>8} {"SL%":>6} {"TP%":>6} {"EOD%":>6} {"ZSh(D)":>8}')
    for sl in SL_VALS:
        pnl, zpnl, dates, types_ = eng.run_combo(stocks, sl, tp, RSI_THRESH)
        pnl = np.asarray(pnl, float); zpnl = np.asarray(zpnl, float)
        types_ = np.asarray(types_); dates_ = np.asarray(dates)
        fin = np.isfinite(pnl) & np.isfinite(zpnl)
        pnl, zpnl, types_, dates_ = pnl[fin], zpnl[fin], types_[fin], dates_[fin]
        n = len(pnl)
        gp = pnl[pnl > 0].sum(); gl = abs(pnl[pnl < 0].sum())
        zgp = zpnl[zpnl > 0].sum(); zgl = abs(zpnl[zpnl < 0].sum())
        pf = gp / gl if gl > 0 else 0.0
        zpf = zgp / zgl if zgl > 0 else 0.0
        net_zpnl = zpnl.sum()
        sl_pct = (types_ == 'SL').sum() / n * 100
        tp_pct = (types_ == 'TP').sum() / n * 100
        eod = types_ == 'EOD'
        eod_pct = eod.sum() / n * 100
        dd = pd.to_datetime(pd.Series(dates_)).dt.date
        dsum = pd.DataFrame({'zpnl': zpnl, 'date': dd}).groupby('date')['zpnl'].sum()
        zshd = (dsum.mean() / dsum.std()) * np.sqrt(252) if dsum.std() > 0 else 0.0
        cb = alpha_row(zpnl, dates_, basket_daily)
        cn = alpha_row(zpnl, dates_, nifty_daily)
        rows.append(dict(sl=sl, tp=tp, n=n, pf=round(pf, 3), zpf=round(zpf, 4),
                         net_zpnl=round(net_zpnl, 2),
                         alpha_basket=round(cb['alpha'], 4), ci_lo_basket=round(cb['ci_lo'], 3),
                         ci_hi_basket=round(cb['ci_hi'], 3), p_basket=round(cb['p'], 4),
                         beta_basket=round(cb['beta'], 3), alpha_cum_basket=round(cb['alpha_cum'], 1),
                         alpha_nifty=round(cn['alpha'], 4), ci_lo_nifty=round(cn['ci_lo'], 3),
                         ci_hi_nifty=round(cn['ci_hi'], 3), p_nifty=round(cn['p'], 4),
                         beta_nifty=round(cn['beta'], 3),
                         sl_pct=round(sl_pct, 1), tp_pct=round(tp_pct, 1),
                         eod_pct=round(eod_pct, 1), zshd=round(zshd, 3)))
        print(f'  {sl:>5.2f} {n:>8,} {pf:>7.3f} {zpf:>7.4f} {net_zpnl:>12,.0f} '
              f'{cb["alpha"]:>8.3f} [{cb["ci_lo"]:>7.2f},{cb["ci_hi"]:>7.2f}] {cb["p"]:>6.3f} '
              f'{cn["alpha"]:>8.3f} {sl_pct:>6.1f} {tp_pct:>6.1f} {eod_pct:>6.1f} {zshd:>8.3f}')
    print()

df = pd.DataFrame(rows)
out = os.path.join(SCRIPT_DIR, '54b_table3_sl_sweep_results.csv')
df.to_csv(out, index=False)
print(f'Results saved: {out}\n')

# ── co-peak check per TP ──────────────────────────────────────────────────────
print(f'{"="*70}\nCO-PEAK CHECK (ZPF / net_zpnl / basket alpha) per fixed TP\n{"="*70}')
for tp in TP_VALS:
    g = df[df.tp == tp].reset_index(drop=True)
    zpf_pk = g.loc[g.zpf.idxmax()]
    nz_pk = g.loc[g.net_zpnl.idxmax()]
    aB_pk = g.loc[g.alpha_basket.idxmax()]
    print(f'\nTP={tp}:')
    print(f'  ZPF peak         SL={zpf_pk.sl}  (ZPF={zpf_pk.zpf:.4f}, net_zpnl={zpf_pk.net_zpnl:,.0f}, '
          f'aB={zpf_pk.alpha_basket:.3f}, EOD%={zpf_pk.eod_pct})')
    print(f'  net_zpnl peak    SL={nz_pk.sl}  (ZPF={nz_pk.zpf:.4f}, net_zpnl={nz_pk.net_zpnl:,.0f}, '
          f'aB={nz_pk.alpha_basket:.3f}, EOD%={nz_pk.eod_pct})')
    print(f'  basket-a peak    SL={aB_pk.sl}  (ZPF={aB_pk.zpf:.4f}, net_zpnl={aB_pk.net_zpnl:,.0f}, '
          f'aB={aB_pk.alpha_basket:.3f}, EOD%={aB_pk.eod_pct})')
    edge = zpf_pk.sl == SL_VALS[0] or nz_pk.sl == SL_VALS[0] or aB_pk.sl == SL_VALS[0]
    print(f'  -> {"EDGE-OF-GRID (a peak sits at SL floor 0.25 — extend further)" if edge else "interior peak(s)"}')

print('\nDone.')
