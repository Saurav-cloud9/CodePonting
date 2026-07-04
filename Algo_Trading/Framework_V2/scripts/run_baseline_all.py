import sys, io, glob
from pathlib import Path
from collections import defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ma_baseline      import MABaseline
from core.ma_baseline_v1_1 import MABaselineV1_1
from core.ma_baseline_v2   import MABaselineV2
from core.ma_baseline_v3   import MABaselineV3

CSV_DIR = Path(__file__).parent.parent / 'data/historical/csv/intraday_5min'


def compute_indicators(df):
    df = df.copy()
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low']  - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    df['atr14'] = tr.ewm(alpha=1/14, adjust=False).mean()
    df['ma20']  = df['close'].rolling(20).mean()
    df['date']  = pd.to_datetime(df['datetime']).dt.date
    df['hour']  = pd.to_datetime(df['datetime']).dt.hour
    return df


def aggregate(trades):
    total  = len(trades)
    wins   = sum(1 for t in trades if t['outcome'] == 'W')
    losses = sum(1 for t in trades if t['outcome'] == 'L')
    eods   = sum(1 for t in trades if t['outcome'].startswith('EOD'))
    wr     = wins / total * 100 if total else 0
    gross_win  = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_loss = sum(t['pnl'] for t in trades if t['pnl'] < 0)
    pf = gross_win / abs(gross_loss) if gross_loss else float('inf')
    total_pnl = sum(t['pnl'] for t in trades)
    return dict(total=total, wins=wins, losses=losses, eods=eods,
                wr=wr, pf=pf, total_pnl=total_pnl)


def run_class(label, model, files, use_prepare=False):
    print(f'\n{"="*50}')
    print(f'Running {label} ...')
    print('='*50)
    all_trades = []
    for f in files:
        ticker = Path(f).stem.replace('_5min', '')
        df = pd.read_csv(f)
        df = compute_indicators(df)
        if use_prepare:
            df = MABaselineV1_1.prepare(df)
        trades = model.run(df)
        for t in trades:
            t['ticker'] = ticker
        all_trades.extend(trades)
        print(f'  {ticker}: {len(trades)} trades')

    stats = aggregate(all_trades)
    print(f'\n  Trades : {stats["total"]}  (W={stats["wins"]}, L={stats["losses"]}, EOD={stats["eods"]})')
    print(f'  WR     : {stats["wr"]:.1f}%')
    print(f'  PnL    : {stats["total_pnl"]:,.2f}')
    print(f'  PF     : {stats["pf"]:.4f}')

    # Yearwise
    year_trades = defaultdict(list)
    for t in all_trades:
        if 'exit_dt' in t and t['exit_dt'] is not None:
            try:
                yr = pd.to_datetime(t['exit_dt']).year
                year_trades[yr].append(t)
            except Exception:
                pass
    if year_trades:
        print('\n  Yearwise PF:')
        for yr in sorted(year_trades):
            yt = year_trades[yr]
            gw = sum(t['pnl'] for t in yt if t['pnl'] > 0)
            gl = sum(t['pnl'] for t in yt if t['pnl'] < 0)
            ypf = gw / abs(gl) if gl else float('inf')
            print(f'    {yr}: {len(yt):5d} trades  PF={ypf:.4f}')

    return stats


def run():
    files = sorted(glob.glob(str(CSV_DIR / '*_5min.csv')))
    print(f'Loaded {len(files)} CSVs from {CSV_DIR}')

    results = {}
    results['v0']    = run_class('v0  LONG bare bounce',        MABaseline(),     files)
    results['v1.1']  = run_class('v1.1 LONG wick+VWAP+EMA',    MABaselineV1_1(), files, use_prepare=True)
    results['v2']    = run_class('v2  SHORT bare (mirror v0)',  MABaselineV2(),   files)
    results['v3']    = run_class('v3  SHORT wick (mirror v1)',  MABaselineV3(),   files)

    # Comparison table
    print('\n\n' + '='*60)
    print('COMPARISON TABLE')
    print('='*60)
    print(f'{"":10s} {"Trades":>8s} {"WR%":>7s} {"PF":>8s} {"Total PnL":>14s}')
    print('-'*60)
    for lbl, s in results.items():
        print(f'{lbl:10s} {s["total"]:>8d} {s["wr"]:>6.1f}% {s["pf"]:>8.4f} {s["total_pnl"]:>14,.2f}')
    print('='*60)


if __name__ == '__main__':
    run()
