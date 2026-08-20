"""
Batch export H5 signals — 5 stocks × 2022 × 2 tb variants.
tb3 : bounce search window = 3 bars (tight, structurally cleaner)
tb9 : bounce search window = 9 bars (wide, captures late bounces)
No signal cap — all 2022 signals exported.
"""
import pandas as pd
import numpy as np
import os

STOCKS      = ['POWERGRID','NTPC','RELIANCE','HDFCBANK','INFY','ADANIPORTS','ASHOKLEY',
               'AXISBANK','BAJFINANCE','BANDHANBNK','BHARTIARTL','CIPLA','COALINDIA',
               'DABUR','DIVISLAB','HINDALCO','ICICIBANK','INDUSINDBK','ITC','JSWSTEEL',
               'NATIONALUM','ONGC','PNB','SBIN','SUNPHARMA','TATAMOTORS','TATASTEEL',
               'TECHM','VEDL','WIPRO']
YEAR        = 2022
TB_VARIANTS = [3, 9]
DATA_DIR    = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min"
OUT_DIR     = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5\signals"

os.makedirs(OUT_DIR, exist_ok=True)

# ─── Core export function ─────────────────────────────────────────────────────
def export_signals(stock, year, max_tb_gap):
    csv_path = os.path.join(DATA_DIR, f"{stock}_5min.csv")
    out_file = os.path.join(OUT_DIR, f"{stock.lower()}_{year}_h5_signals_tb{max_tb_gap}.csv")

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df = df[df['datetime'].dt.year == year].copy().reset_index(drop=True)

    # Indicators
    prev_close   = df['close'].shift(1)
    df['tr']     = np.maximum(df['high'] - df['low'],
                   np.maximum(abs(df['high'] - prev_close), abs(df['low'] - prev_close)))
    df['atr14']  = df['tr'].rolling(14, min_periods=14).mean()
    df['vol_ma20'] = df['volume'].rolling(20, min_periods=20).mean()
    df['vr']     = df['volume'] / df['vol_ma20']
    df['day_idx'] = df.groupby('date').cumcount()

    signals = []
    i = 20

    while i < len(df) - 2:
        row  = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
            i += 1
            continue

        if row['low'] <= row['ma20']:
            T0       = i
            t0_date  = row['date']
            t0r      = df.iloc[T0]

            # Bounce: first bar from T0 where close > ma20, within max_tb_gap bars, same day
            bounce_bar = None
            for j in range(T0, min(T0 + max_tb_gap + 1, len(df) - 1)):
                brow = df.iloc[j]
                if brow['date'] != t0_date:
                    break
                if brow['close'] > brow['ma20']:
                    bounce_bar = j
                    break

            if bounce_bar is None:
                i += 1
                continue

            entry_bar = bounce_bar + 1
            if entry_bar >= len(df) or df.iloc[entry_bar]['date'] != t0_date:
                i += 1
                continue

            bounce_bar_index = bounce_bar - T0
            entry_bar_index  = bounce_bar_index + 1

            br = df.iloc[bounce_bar]
            er = df.iloc[entry_bar]

            if er['datetime'].time() >= pd.Timestamp('14:40').time():
                i += 1
                continue

            # ── Params ──────────────────────────────────────────────────────
            p01 = ((t0r['ma20'] - df.iloc[T0-5]['ma20']) / t0r['ma20']) * 100 \
                  if t0r['day_idx'] >= 5 and df.iloc[T0-5]['date'] == t0_date else np.nan
            p02 = ((df.iloc[T0-3]['ma20'] - df.iloc[T0-8]['ma20']) / df.iloc[T0-3]['ma20']) * 100 \
                  if t0r['day_idx'] >= 8 and df.iloc[T0-8]['date'] == t0_date and pd.notna(df.iloc[T0-3]['ma20']) and df.iloc[T0-3]['ma20'] != 0 else np.nan

            p03 = 0
            for k in range(T0 - 1, -1, -1):
                bk = df.iloc[k]
                if bk['date'] != t0_date: break
                if pd.notna(bk['ma20']) and bk['low'] > bk['ma20']: p03 += 1
                else: break

            swing_idx, best_high = None, -np.inf
            for k in range(T0 - 1, -1, -1):
                bk = df.iloc[k]
                if bk['date'] != t0_date: break
                if bk['low'] <= bk['ma20']: break
                if bk['high'] >= best_high:
                    best_high = bk['high']; swing_idx = k
            p04 = (T0 - swing_idx) if swing_idx is not None else np.nan

            atr = t0r['atr14']
            p05 = (t0r['ma20'] - t0r['low']) / atr if atr > 0 else np.nan
            cr  = t0r['high'] - t0r['low']
            p06 = (abs(t0r['close'] - t0r['open']) / cr * 100) if cr > 0 else 100.0

            ma20     = t0r['ma20']
            body_low = min(t0r['open'], t0r['close'])
            denom    = ma20 - t0r['low']
            if denom == 0:
                p07, p07_na = np.nan, 1
            else:
                p07, p07_na = round((body_low - ma20) / denom, 4), 0

            p08 = br['vr'] if pd.notna(br['vr']) else np.nan
            same_candle = 1 if bounce_bar == T0 else 0
            p09 = np.nan if (same_candle or pd.isna(br['vr']) or pd.isna(t0r['vr'])) \
                  else (1 if br['vr'] > t0r['vr'] else 0)
            p10  = bounce_bar_index
            p11 = 1 if er['open']  > br['close'] else 0
            p12      = (1 if er['vr'] >= br['vr'] else 0) \
                       if (pd.notna(er['vr']) and pd.notna(br['vr'])) else np.nan

            # ── PnL simulation ───────────────────────────────────────────────
            entry_price = er['open']
            sl     = entry_price - (2.5 * atr)
            target = entry_price + (4.5 * atr)
            outcome, pnl, exit_bar = None, None, None

            for j in range(entry_bar, len(df)):
                bar = df.iloc[j]
                if bar['low'] <= sl and bar['high'] >= target:
                    if abs(bar['open'] - sl) <= abs(bar['open'] - target):
                        outcome, pnl = 'L', round(-2.5 * atr, 4)
                    else:
                        outcome, pnl = 'W', round(4.5 * atr, 4)
                    exit_bar = j; break
                if bar['low'] <= sl:
                    outcome, pnl = 'L', round(-2.5 * atr, 4); exit_bar = j; break
                if bar['high'] >= target:
                    outcome, pnl = 'W', round(4.5 * atr, 4); exit_bar = j; break
                if bar['datetime'].time() >= pd.Timestamp('15:00').time():
                    pnl = round(bar['open'] - entry_price, 2)
                    outcome = 'EOD+' if bar['open'] > entry_price else 'EOD-'
                    exit_bar = j; break
                if bar['date'] != t0_date:
                    last = df.iloc[j - 1]
                    pnl = round(last['close'] - entry_price, 2)
                    outcome = 'EOD+' if last['close'] > entry_price else 'EOD-'
                    exit_bar = j - 1; break
            else:
                last = df.iloc[-1]
                pnl = round(last['close'] - entry_price, 4)
                outcome = 'EOD+' if last['close'] > entry_price else 'EOD-'
                exit_bar = len(df) - 1

            signals.append({
                'signal_id': f"S{len(signals)+1:03d}",
                'stock': stock,
                'datetime': t0r['datetime'],
                'p01': round(p01, 4) if pd.notna(p01) else np.nan,
                'p02': round(p02, 4) if pd.notna(p02) else np.nan,
                'p03': int(p03),
                'p04': int(p04) if pd.notna(p04) else np.nan,
                'p05': round(float(p05), 4) if pd.notna(p05) else np.nan,
                'p06': round(float(p06), 2) if pd.notna(p06) else np.nan,
                'p07': p07 if pd.notna(p07) else np.nan,
                'p07_na': p07_na,
                'p08': round(float(p08), 4) if pd.notna(p08) else np.nan,
                'p09': p09,
                'p10': p10,
                'p11': p11,
                'p12': p12,
                'same_candle_tb': same_candle,
                'bounce_bar_index': bounce_bar_index,
                'entry_bar_index': entry_bar_index,
                'bounce_datetime': df.iloc[bounce_bar]['datetime'],
                'entry_datetime': df.iloc[entry_bar]['datetime'],
                'exit_datetime': df.iloc[exit_bar]['datetime'],
                'entry_price': entry_price,
                'sl': sl,
                'target': target,
                'pnl': pnl,
                'outcome': outcome,
            })
            i = entry_bar + 1
        else:
            i += 1

    out = pd.DataFrame(signals)
    out.to_csv(out_file, index=False, encoding='utf-8', lineterminator='\n')
    print(f"  {stock} tb{max_tb_gap}: {len(out)} signals -> {out_file}")
    return len(out)

# ─── Run ─────────────────────────────────────────────────────────────────────
print(f"Exporting {len(STOCKS)} stocks × {len(TB_VARIANTS)} variants ({YEAR})...\n")
for stock in STOCKS:
    for tb in TB_VARIANTS:
        export_signals(stock, YEAR, tb)
print("\nDone.")
