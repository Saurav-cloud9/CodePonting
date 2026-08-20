"""
Convert temp JSONL files → validated parquets.
Run after all MCP fetching is complete.
"""
import json, csv
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PYTHON = None  # not needed here
BASE_DIR   = Path(__file__).parent
TMP_DIR    = BASE_DIR / 'Framework_V1/data/historical/intraday_5min_DS3/.tmp'
OUTPUT_DIR = BASE_DIR / 'Framework_V1/data/historical/intraday_5min_DS3'
LOG_FILE   = BASE_DIR / 'DS3_fetch_log.csv'
REPORT_FILE= BASE_DIR / 'DS3_validation_report.txt'

IST = pytz.FixedOffset(330)

def candles_to_df(jsonl_path: Path) -> pd.DataFrame:
    rows = []
    with open(jsonl_path) as f:
        for line in f:
            c = json.loads(line.strip())
            # Kite format: [date_str, open, high, low, close, volume, oi]
            if isinstance(c, list) and len(c) >= 6:
                dt = pd.to_datetime(c[0])
                if dt.tzinfo is None:
                    dt = IST.localize(dt)
                else:
                    dt = dt.astimezone(IST)
                rows.append({
                    'datetime': dt,
                    'open':     float(c[1]),
                    'high':     float(c[2]),
                    'low':      float(c[3]),
                    'close':    float(c[4]),
                    'volume':   int(c[5]),
                    'oi':       int(c[6]) if len(c) > 6 else 0,
                })
    if not rows:
        return pd.DataFrame(columns=['datetime','open','high','low','close','volume','oi'])

    df = pd.DataFrame(rows)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert(IST)
    for col in ['open','high','low','close']:
        df[col] = df[col].astype('float64')
    for col in ['volume','oi']:
        df[col] = df[col].astype('int64')
    df = df.sort_values('datetime').drop_duplicates(subset='datetime').reset_index(drop=True)
    return df


def validate(stock: str, df: pd.DataFrame) -> dict:
    stats = {'post_mkt': 0, 'ohlc': 0}

    # P2: remove post 15:30 candles
    mask_post = df['datetime'].dt.time > pd.Timestamp('15:30').time()
    stats['post_mkt'] = int(mask_post.sum())
    if stats['post_mkt']:
        print(f"  ⚠  {stock}: removing {stats['post_mkt']} post-market candles")
        df = df[~mask_post].reset_index(drop=True)

    # P3a: OHLC violations
    mask_ohlc = (
        (df['high'] < df['low'])   |
        (df['high'] < df['open'])  |
        (df['high'] < df['close']) |
        (df['low']  > df['open'])  |
        (df['low']  > df['close'])
    )
    stats['ohlc'] = int(mask_ohlc.sum())
    if stats['ohlc']:
        print(f"  ⚠  {stock}: removing {stats['ohlc']} OHLC-violation rows")
        df = df[~mask_ohlc].reset_index(drop=True)

    return df, stats


def main():
    jsonl_files = sorted(TMP_DIR.glob('*.jsonl'))
    print(f"Found {len(jsonl_files)} temp JSONL files to finalize.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_rows     = []
    report_rows  = []
    total_candles = 0

    for jf in jsonl_files:
        stock = jf.stem
        print(f"\nProcessing {stock}...")
        df = candles_to_df(jf)

        if df.empty:
            print(f"  ✗ No data for {stock}")
            log_rows.append({'stock': stock, 'status': 'EMPTY', 'candles_fetched': 0,
                             'date_from': '', 'date_to': '', 'error': 'no candles'})
            continue

        df, stats = validate(stock, df)
        out_path  = OUTPUT_DIR / f'{stock}.parquet'
        df.to_parquet(out_path, index=False)

        trading_days = df['datetime'].dt.date.nunique()
        flag = ' ⚠️  LOW COVERAGE' if trading_days < 2000 else ''
        date_from = str(df['datetime'].iloc[0])[:10]
        date_to   = str(df['datetime'].iloc[-1])[:10]
        candles   = len(df)
        total_candles += candles

        print(f"  ✅ {stock}: {candles} candles | {date_from} → {date_to} | {trading_days} trading days{flag}")
        print(f"     Saved → {out_path}")

        log_rows.append({'stock': stock, 'status': 'OK', 'candles_fetched': candles,
                         'date_from': date_from, 'date_to': date_to, 'error': ''})
        report_rows.append({'stock': stock, 'candles': candles, 'date_from': date_from,
                             'date_to': date_to, 'post_mkt': stats['post_mkt'], 'ohlc': stats['ohlc']})

    # Write log
    with open(LOG_FILE, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['stock','status','candles_fetched','date_from','date_to','error'])
        w.writeheader(); w.writerows(log_rows)

    # Write report
    hdr = f"{'Stock':<14} {'Candles':>8} {'Date From':>12} {'Date To':>12} {'PostMkt':>9} {'OHLC':>6}"
    sep = '-' * len(hdr)
    lines = ['DS3 VALIDATION REPORT', f'Generated: {datetime.now():%Y-%m-%d %H:%M:%S}', sep, hdr, sep]
    for r in report_rows:
        lines.append(f"{r['stock']:<14} {r['candles']:>8} {r['date_from']:>12} {r['date_to']:>12} "
                     f"{r['post_mkt']:>9} {r['ohlc']:>6}")
    lines += [sep, f"Total stocks : {len(report_rows)}", f"Total candles: {total_candles:,}"]
    REPORT_FILE.write_text('\n'.join(lines))

    print(f"\n{'='*60}")
    print(f"DS3 BUILD COMPLETE — {len(report_rows)} stocks, {total_candles:,} candles")
    print(f"Validation report → {REPORT_FILE}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
