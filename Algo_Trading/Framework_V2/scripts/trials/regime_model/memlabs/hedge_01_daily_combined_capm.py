"""
Hedge side-thread (file 1) — passive NIFTY hedge overlay on FLAGSHIP_6BCEH_SHORT_VWAP_RSI60.
Delegated by fv2 to cpgeneric, 2026-09-19. Separate from the #54 regime-filter thread
(54_/54b_/54c_/54d_/54e_) — does not touch any of those files or their conclusions,
just reuses 54c_trade_log.csv (now with exit_dt added) as input.

QUESTION: FLAGSHIP_6BCEH_SHORT_VWAP_RSI60's basket-regressed CAPM shows net_zpnl=-2436.26,
alpha_cumulative=-1042.49 (p=0.201, near-zero, not confidently negative), beta=-4.355.
Decomposition: net_zpnl = alpha_cumulative + beta*Sigma_x, so beta_drag = -2436.26 -
(-1042.49) = -1393.77 - beta drag is the dominant loss driver, not skill.
A theoretical perfect hedge (hedge_beta = +4.355, hedge_alpha = 0 by construction, passive
index-tracking) would drive combined_beta -> 0 and leave combined net_zpnl -> alpha_cumulative
(~-1042.49) unchanged - NOT positive, just drag-removed. This simulates that at DAILY
resolution (no intraday NIFTY data exists in this project - flagged as a next step if this
looks promising) and checks how close a realistic implementation actually gets.

capm()/alpha_row() reused verbatim from 54b_table3_sl_sweep.py (same formula/units the
master_basket.csv row was computed with) - not re-derived, so results are directly comparable.

Method:
  1. Aggregate strategy trades to daily zpnl by exit_dt (same key run_combo() uses).
  2. hedge_daily_zpnl = +beta_orig * nifty_daily_ret_pct (sign-flipped vs the strategy's own
     beta, same "rupees of daily zpnl per 1 percentage-point of NIFTY move" units the
     existing beta_capm is already in - no unit conversion needed, hedge_beta is just
     -beta_orig by construction).
  3. combined_daily_zpnl = strategy_daily_zpnl + hedge_daily_zpnl.
  4. Re-run capm() on combined vs NIFTY daily returns -> new alpha/beta/p/net_zpnl.
  5. Compare combined beta to 0 and combined net_zpnl to the -1042.49 ceiling.

Output: hedge_01_results.md (this run's numbers + comparison table).
"""
import glob
import os

import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_LOG = os.path.join(SCRIPT_DIR, '54c_trade_log.csv')
NIFTY_PATH = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/daily/NIFTY50.parquet'
DS3_DIR = '/home/ubuntu/CodePonting/Algo_Trading/Framework_V2/data/historical/intraday_5min_DS3'

# Reference numbers from strategies/flagship/master_basket.csv,
# row source==FLAGSHIP_6BCEH_SHORT_VWAP_RSI60 (2026-09-19)
REF_NET_ZPNL = -2436.26
REF_ALPHA_CUM = -1042.49
REF_BETA = -4.355
REF_ALPHA_DAILY = -0.408
REF_P = 0.201


def capm(y, x):
    """Verbatim from 54b_table3_sl_sweep.py - do not modify, must match master CSV exactly."""
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
    """Verbatim from 54b_table3_sl_sweep.py."""
    dd = pd.to_datetime(pd.Series(dates_arr)).dt.date
    daily = pd.DataFrame({'zpnl': zpnl_arr, 'date': dd}).groupby('date')['zpnl'].sum().reset_index()
    m = daily.merge(market_daily, on='date', how='inner')
    c = capm(m['zpnl'].values, m['ret_pct'].values)
    c['alpha_cum'] = c['alpha'] * c['n']
    return c, daily, m


# ── load ─────────────────────────────────────────────────────────────────
print('Loading trade log + NIFTY daily...')
trades = pd.read_csv(TRADE_LOG)
trades['exit_dt'] = pd.to_datetime(trades['exit_dt']).dt.date

nifty = pd.read_parquet(NIFTY_PATH)
nifty['date'] = pd.to_datetime(nifty['datetime']).dt.date
nifty = nifty.sort_values('date').reset_index(drop=True)
nifty['ret_pct'] = nifty['close'].pct_change() * 100
nifty_daily = nifty[['date', 'ret_pct']].dropna()

# Basket factor - verbatim construction from 54b_table3_sl_sweep.py (30-stock equal-weighted
# daily return). REF_* numbers are basket-regressed (master_basket.csv), not NIFTY-regressed -
# using NIFTY here was a bug caught on first run (alpha/beta didn't match reference at all,
# even though net_zpnl did - net_zpnl doesn't depend on which market factor is used, only the
# regression stats do).
basket_rows = []
for f in sorted(glob.glob(os.path.join(DS3_DIR, '*.parquet'))):
    d = pd.read_parquet(f, columns=['datetime', 'close'])
    d['datetime'] = pd.to_datetime(d['datetime'])
    if d['datetime'].dt.tz is not None:
        d['datetime'] = d['datetime'].dt.tz_localize(None)
    d['date'] = d['datetime'].dt.date
    basket_rows.append(d.groupby('date')['close'].last())
basket_df = pd.concat(basket_rows, axis=1).mask(lambda x: x <= 0)
# backtesting_rules.md fix (2026-09-xx): pd.concat's date index is object-dtype and NOT
# guaranteed sorted - pct_change() on an unsorted index silently compares against the
# wrong "previous" row. 54b_table3_sl_sweep.py (where this construction was copied from)
# still has the old bug - sort_index() on a real DatetimeIndex is the documented fix.
basket_df.index = pd.to_datetime(basket_df.index)
basket_df = basket_df.sort_index()
basket_daily = (basket_df.pct_change().mean(axis=1, skipna=True).dropna() * 100).reset_index()
basket_daily.columns = ['date', 'ret_pct']
basket_daily['date'] = basket_daily['date'].dt.date

# ── step 1: reproduce the original (unhedged) result as a sanity check ────
orig, orig_daily, orig_m = alpha_row(trades['zpnl'].values, trades['exit_dt'].values, basket_daily)
net_zpnl_all_trades = trades['zpnl'].sum()  # over ALL trades, not just merged-with-market days
print(f'\nSanity check vs master_basket.csv row (should match REF_* above):')
print(f'  net_zpnl (all trades)   = {net_zpnl_all_trades:.2f}  (ref {REF_NET_ZPNL})')
print(f'  alpha (daily)           = {orig["alpha"]:.3f}  (ref {REF_ALPHA_DAILY})')
print(f'  alpha_cumulative        = {orig["alpha_cum"]:.2f}  (ref {REF_ALPHA_CUM})')
print(f'  beta                    = {orig["beta"]:.3f}  (ref {REF_BETA})')
print(f'  p                       = {orig["p"]:.3f}  (ref {REF_P})')

# ── step 2: build the hedge leg ────────────────────────────────────────────
# Per fv2's spec: hedge is sized by the BASKET-regressed beta (-4.355, the reference
# metric), but the hedge INSTRUMENT itself is NIFTY (the actual tradeable, liquid index -
# "the basket" isn't a single tradeable thing). hedge_beta = -orig['beta'] (offsets the
# strategy's basket-beta exactly, by construction); hedge_daily_zpnl = hedge_beta *
# nifty_daily_ret_pct - same "rupees of daily zpnl per 1pp of market move" units the
# existing beta_capm is already in, no separate scaling needed.
hedge_beta = -orig['beta']
hedge = nifty_daily.copy()
hedge['hedge_zpnl'] = hedge_beta * hedge['ret_pct']

# ── step 3: combine ─────────────────────────────────────────────────────
combined_daily = orig_daily.merge(hedge[['date', 'hedge_zpnl']], on='date', how='left')
combined_daily['hedge_zpnl'] = combined_daily['hedge_zpnl'].fillna(0.0)  # no NIFTY row -> no hedge applied that day
combined_daily['combined_zpnl'] = combined_daily['zpnl'] + combined_daily['hedge_zpnl']

# ── step 4: re-run CAPM on the combined series - against BOTH factors ──────
# Primary: basket (apples-to-apples with the reference beta this hedge was sized to cancel).
# Secondary: NIFTY (the hedge's own instrument) - informative even though the hedge wasn't
# sized against it directly, since basket and NIFTY are highly overlapping large-cap universes.
comb, _, comb_m = alpha_row(combined_daily['combined_zpnl'].values, combined_daily['date'].values, basket_daily)
comb_nifty, _, _ = alpha_row(combined_daily['combined_zpnl'].values, combined_daily['date'].values, nifty_daily)
combined_net_zpnl = combined_daily['combined_zpnl'].sum()
hedge_total_pnl = combined_daily['hedge_zpnl'].sum()

# ── step 5: compare ──────────────────────────────────────────────────────
gap_to_ceiling = combined_net_zpnl - REF_ALPHA_CUM  # how far short of the theoretical best case
recovered_pct = (REF_NET_ZPNL - combined_net_zpnl) / (REF_NET_ZPNL - REF_ALPHA_CUM) * 100 \
    if (REF_NET_ZPNL - REF_ALPHA_CUM) != 0 else float('nan')

print(f'\n{"="*70}')
print('HEDGE RESULTS (daily-level MVP)')
print(f'{"="*70}')
print(f'  hedge_beta applied       = {hedge_beta:.3f}  (NIFTY-instrument, sized off basket-beta)')
print(f'  hedge total P&L          = {hedge_total_pnl:.2f}')
print(f'  combined net_zpnl        = {combined_net_zpnl:.2f}  (unhedged {REF_NET_ZPNL}, ceiling {REF_ALPHA_CUM})')
print(f'  --- vs basket (primary, apples-to-apples with reference) ---')
print(f'  combined alpha (daily)   = {comb["alpha"]:.3f}')
print(f'  combined alpha_cum       = {comb["alpha_cum"]:.2f}')
print(f'  combined beta            = {comb["beta"]:.3f}  (target ~0, was {orig["beta"]:.3f})')
print(f'  combined p               = {comb["p"]:.3f}')
print(f'  --- vs NIFTY (secondary, the hedge\'s own instrument) ---')
print(f'  combined alpha (daily)   = {comb_nifty["alpha"]:.3f}')
print(f'  combined beta            = {comb_nifty["beta"]:.3f}')
print(f'  combined p               = {comb_nifty["p"]:.3f}')
print(f'  gap to theoretical ceiling = {gap_to_ceiling:.2f}')
print(f'  % of beta-drag recovered  = {recovered_pct:.1f}%')

# ── write report ─────────────────────────────────────────────────────────
out_md = os.path.join(SCRIPT_DIR, 'hedge_01_results.md')
with open(out_md, 'w') as f:
    f.write('# Hedge 01 — Passive NIFTY hedge overlay, daily-level MVP\n\n')
    f.write('FLAGSHIP_6BCEH_SHORT_VWAP_RSI60, delegated by fv2, 2026-09-19.\n\n')
    f.write('## Reference (unhedged, from master_basket.csv)\n\n')
    f.write(f'| Metric | Value |\n|---|---|\n')
    f.write(f'| net_zpnl | {REF_NET_ZPNL} |\n| alpha (daily) | {REF_ALPHA_DAILY} |\n')
    f.write(f'| alpha_cumulative (theoretical ceiling) | {REF_ALPHA_CUM} |\n')
    f.write(f'| beta | {REF_BETA} |\n| p | {REF_P} |\n\n')
    f.write('## Sanity check (reproduced from 54c_trade_log.csv, should match reference)\n\n')
    f.write(f'| Metric | Value |\n|---|---|\n')
    f.write(f'| net_zpnl (all trades) | {net_zpnl_all_trades:.2f} |\n')
    f.write(f'| alpha (daily) | {orig["alpha"]:.3f} |\n| alpha_cumulative | {orig["alpha_cum"]:.2f} |\n')
    f.write(f'| beta | {orig["beta"]:.3f} |\n| p | {orig["p"]:.3f} |\n\n')
    f.write('## Hedged result\n\n')
    f.write('Hedge instrument: NIFTY (passive, tradeable). Sizing: hedge_beta = '
            '-basket_beta (offsets the reference basket-regressed beta by construction).\n\n')
    f.write(f'| Metric | Value |\n|---|---|\n')
    f.write(f'| hedge_beta applied | {hedge_beta:.3f} |\n')
    f.write(f'| hedge total P&L | {hedge_total_pnl:.2f} |\n')
    f.write(f'| combined net_zpnl | {combined_net_zpnl:.2f} |\n\n')
    f.write('### vs basket (primary — apples-to-apples with reference)\n\n')
    f.write(f'| Metric | Value |\n|---|---|\n')
    f.write(f'| combined alpha (daily) | {comb["alpha"]:.3f} |\n')
    f.write(f'| combined alpha_cumulative | {comb["alpha_cum"]:.2f} |\n')
    f.write(f'| combined beta | {comb["beta"]:.3f} |\n')
    f.write(f'| combined p | {comb["p"]:.3f} |\n\n')
    f.write('### vs NIFTY (secondary — the hedge\'s own instrument)\n\n')
    f.write(f'| Metric | Value |\n|---|---|\n')
    f.write(f'| combined alpha (daily) | {comb_nifty["alpha"]:.3f} |\n')
    f.write(f'| combined beta | {comb_nifty["beta"]:.3f} |\n')
    f.write(f'| combined p | {comb_nifty["p"]:.3f} |\n\n')
    f.write('## Comparison\n\n')
    f.write(f'- Theoretical ceiling (perfect hedge): net_zpnl -> {REF_ALPHA_CUM}\n')
    f.write(f'- Realized: net_zpnl -> {combined_net_zpnl:.2f}\n')
    f.write(f'- Gap to ceiling: {gap_to_ceiling:.2f}\n')
    f.write(f'- % of beta drag actually recovered: {recovered_pct:.1f}%\n')
    f.write(f'- Beta reduction: {REF_BETA} -> {comb["beta"]:.3f}\n')

print(f'\nReport written: {out_md}')
