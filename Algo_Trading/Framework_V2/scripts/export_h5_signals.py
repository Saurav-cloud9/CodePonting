"""
Export raw MA20 bounce signals with all 11 fv2 params for H5 Lite testing.
Stock: POWERGRID, Period: 2022, Cap: 100 signals (chronological), No position guard.
same_candle_tb is an observation column only — not a gate param.
"""
import pandas as pd
import numpy as np
import os

STOCK = "POWERGRID"
CSV_PATH = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min\POWERGRID_5min.csv"
OUTPUT_DIR = r"C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\outputs\h5"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "powergrid_2022_h5_signals.csv")
MAX_SIGNALS = 100
YEAR = 2022

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = df['datetime'].dt.date
df = df[df['datetime'].dt.year == YEAR].copy().reset_index(drop=True)

# Compute ATR14 (SMA) and vol_ma20
prev_close = df['close'].shift(1)
df['tr'] = np.maximum(df['high'] - df['low'],
           np.maximum(abs(df['high'] - prev_close), abs(df['low'] - prev_close)))
df['atr14'] = df['tr'].rolling(14, min_periods=14).mean()
df['vol_ma20'] = df['volume'].rolling(20, min_periods=20).mean()
df['vr'] = df['volume'] / df['vol_ma20']

# Day-relative index for p01/p02 N/A detection
df['day_idx'] = df.groupby('date').cumcount()

signals = []
i = 20

while i < len(df) - 2 and len(signals) < MAX_SIGNALS:
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    if pd.isna(row['ma20']) or pd.isna(row['atr14']) or pd.isna(row['vol_ma20']):
        i += 1
        continue

    # Touch: low[T0] <= ma20[T0]  
    if row['low'] <= row['ma20']: # removed -> and pd.notna(prev['ma20']) and prev['close'] > prev['ma20']:
        T0 = i
        t0_date = row['date']
        t0r = df.iloc[T0]

        # Bounce bar: first bar from T0 where close > ma20, same day
        bounce_bar = None
        for j in range(T0, min(T0 + 10, len(df) - 1)):
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

        bounce_bar_index = bounce_bar - T0  # relative to T0 (0 if same candle)
        entry_bar_index  = bounce_bar_index + 1

        br = df.iloc[bounce_bar]
        er = df.iloc[entry_bar]

        # --- p01: slope_threshold ---
        if t0r['day_idx'] >= 5 and df.iloc[T0 - 5]['date'] == t0_date:
            p01 = ((t0r['ma20'] - df.iloc[T0 - 5]['ma20']) / t0r['ma20']) * 100
        else:
            p01 = np.nan

        # --- p02: slope_offset ---
        if t0r['day_idx'] >= 8 and df.iloc[T0 - 8]['date'] == t0_date:
            ma_t3 = df.iloc[T0 - 3]['ma20']
            ma_t8 = df.iloc[T0 - 8]['ma20']
            p02 = ((ma_t3 - ma_t8) / ma_t3) * 100 if pd.notna(ma_t3) and ma_t3 != 0 else np.nan
        else:
            p02 = np.nan

        # --- p03: candles_above (consecutive bars before T0 where low > ma20) ---
        p03 = 0
        for k in range(T0 - 1, -1, -1):
            bk = df.iloc[k]
            if bk['date'] != t0_date:
                break
            if pd.notna(bk['ma20']) and bk['low'] > bk['ma20']:
                p03 += 1
            else:
                break

        # --- p04: pullback_bars (bars from swing high to T0) ---
        # Window: T0-1 back to (not including) first bar where low <= ma20
        # Swing high = highest high within that window
        swing_idx = None
        best_high = -np.inf
        for k in range(T0 - 1, -1, -1):
            bk = df.iloc[k]
            if bk['date'] != t0_date:
                break
            if bk['low'] <= bk['ma20']:  # hit a prior touch — stop
                break
            if bk['high'] >= best_high:  # >= picks earliest bar with peak high
                best_high = bk['high']
                swing_idx = k
        p04 = (T0 - swing_idx) if swing_idx is not None else np.nan

        # --- p05: shoot_depth ---
        atr = t0r['atr14']
        p05 = (t0r['ma20'] - t0r['low']) / atr if atr > 0 else np.nan

        # --- p06: touch_body_pct ---
        candle_range = t0r['high'] - t0r['low']
        p06 = (abs(t0r['close'] - t0r['open']) / candle_range * 100) if candle_range > 0 else 100.0

        # --- p07: wick_defence_ratio ---
        ma20 = t0r['ma20']
        body_low = min(t0r['open'], t0r['close'])
        denom = ma20 - t0r['low']
        numer = body_low - ma20
        if denom == 0: # the condition denom < 0 is excluded as its never going to happen since it would imply no touch happened at the first place
            p07, p07_na = np.nan, 1
        else:
            p07, p07_na = round(numer / denom, 4), 0

        # --- p08: bounce_vr_abs ---
        p08 = br['vr'] if pd.notna(br['vr']) else np.nan

        # --- p09: bounce_vr_rel (N/A if same candle) ---
        same_candle = 1 if bounce_bar == T0 else 0
        if same_candle or pd.isna(br['vr']) or pd.isna(t0r['vr']):
            p09 = np.nan
        else:
            p09 = 1 if br['vr'] > t0r['vr'] else 0

        # --- p10: max_tb_gap (touch-to-bounce bar gap) ---
        p10 = bounce_bar_index  # raw gap; H5 applies ceiling threshold

        # --- p11: G3a (entry_close_above_bounce) ---
        p11 = 1 if er['close'] > br['close'] else 0

        # --- p12: G3b (entry_vr_holds) ---
        if pd.notna(er['vr']) and pd.notna(br['vr']):
            p12 = 1 if er['vr'] >= br['vr'] else 0
        else:
            p12 = np.nan

        # --- PnL + Outcome simulation ---
        entry_price = er['open']
        atr = t0r['atr14']
        sl     = entry_price - (2.5 * atr)
        target = entry_price + (4.5 * atr)
        outcome = None
        pnl = None
        for j in range(entry_bar, len(df)):
            bar = df.iloc[j]
            if bar['date'] != t0_date:
                # EOD exit on last bar of the day
                last = df.iloc[j - 1]
                pnl = round(last['close'] - entry_price, 2)
                outcome = 'EOD+' if last['close'] > entry_price else 'EOD-'
                exit_bar = j - 1
                break
            if bar['low'] <= sl and bar['high'] >= target:
                # Both hit same bar — whichever is closer to open wins
                if abs(bar['open'] - sl) <= abs(bar['open'] - target):
                    outcome, pnl = 'L', round(-2.5 * atr, 4)
                else:
                    outcome, pnl = 'W', round(4.5 * atr, 4)
                exit_bar = j
                break
            if bar['low'] <= sl:
                outcome, pnl = 'L', round(-2.5 * atr, 4)
                exit_bar = j
                break
            if bar['high'] >= target:
                outcome, pnl = 'W', round(4.5 * atr, 4)
                exit_bar = j
                break
        else:
            last = df.iloc[-1]
            pnl = round(last['close'] - entry_price, 4)
            outcome = 'EOD+' if last['close'] > entry_price else 'EOD-'
            exit_bar = len(df) - 1

        signals.append({
            'signal_id': f"S{len(signals)+1:03d}",
            'stock': STOCK,
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
            'entry_bar_index':  entry_bar_index,
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
out.columns = out.columns.str.strip()
out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', lineterminator='\n')
print(f"Exported {len(out)} signals -> {OUTPUT_FILE}")
print(out[['signal_id', 'datetime', 'p01', 'p02', 'p03', 'p04', 'p05', 'p07', 'p07_na', 'p08', 'p09', 'p10', 'p11', 'p12', 'same_candle_tb']].to_string(index=False))
