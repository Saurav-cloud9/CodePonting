import sys, io, glob
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ma_baseline import MABaseline

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


def run():
    files = sorted(glob.glob(str(CSV_DIR / '*_5min.csv')))
    model = MABaseline()
    all_trades = []

    for f in files:
        ticker = Path(f).stem.replace('_5min', '')
        df = pd.read_csv(f)
        df = compute_indicators(df)
        trades = model.run(df)
        for t in trades:
            t['ticker'] = ticker
        all_trades.extend(trades)
        print(f'  {ticker}: {len(trades)} trades')

    # Aggregate
    total  = len(all_trades)
    wins   = sum(1 for t in all_trades if t['outcome'] == 'W')
    losses = sum(1 for t in all_trades if t['outcome'] == 'L')
    eods   = sum(1 for t in all_trades if t['outcome'].startswith('EOD'))
    wr     = wins / total * 100 if total else 0
    gross_win  = sum(t['pnl'] for t in all_trades if t['pnl'] > 0)
    gross_loss = sum(t['pnl'] for t in all_trades if t['pnl'] < 0)
    pf = gross_win / abs(gross_loss) if gross_loss else float('inf')
    total_pnl  = sum(t['pnl'] for t in all_trades)

    print('\n' + '='*50)
    print('MABaseline v1 — Aggregate')
    print('='*50)
    print(f'  Stocks     : {len(files)}')
    print(f'  Trades     : {total}  (W={wins}, L={losses}, EOD={eods})')
    print(f'  Win Rate   : {wr:.1f}%')
    print(f'  Total PnL  : {total_pnl:,.2f}')
    print(f'  Profit Factor: {pf:.4f}')

    # Yearwise PF
    print('\nYearwise PF:')
    from collections import defaultdict
    year_trades = defaultdict(list)
    for t in all_trades:
        if 'exit_dt' in t and t['exit_dt'] is not None:
            try:
                yr = pd.to_datetime(t['exit_dt']).year
                year_trades[yr].append(t)
            except Exception:
                pass
    if year_trades:
        for yr in sorted(year_trades):
            yt = year_trades[yr]
            gw = sum(t['pnl'] for t in yt if t['pnl'] > 0)
            gl = sum(t['pnl'] for t in yt if t['pnl'] < 0)
            ypf = gw / abs(gl) if gl else float('inf')
            print(f'  {yr}: {len(yt):5d} trades  PF={ypf:.4f}')
    else:
        print('  (exit_dt not available — yearwise skipped)')


if __name__ == '__main__':
    run()
