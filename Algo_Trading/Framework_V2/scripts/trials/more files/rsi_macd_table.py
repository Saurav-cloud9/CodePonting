import pandas as pd, numpy as np, os, glob

DATA_DIR = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
DS3_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3'
BASE_SL=2.5; BASE_TP=4.5; MAX_TB_GAP=3; EOD_HOUR=15; WARMUP=40

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    return 100 - (100 / (1 + gain / loss))

def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    return macd_line - macd_line.ewm(span=signal, adjust=False).mean()

def run_backtest(csv_path):
    fv2 = pd.read_csv(csv_path, low_memory=False)
    fv2.columns = fv2.columns.str.strip()
    fv2['datetime'] = pd.to_datetime(fv2['datetime']).dt.tz_localize(None)
    for col in ['open','high','low','close','ma20','atr14']:
        fv2[col] = pd.to_numeric(fv2[col], errors='coerce')
    symbol = os.path.basename(csv_path).replace('_5min.csv','')
    ds3_path = os.path.join(DS3_DIR, f'{symbol}.parquet')
    if os.path.exists(ds3_path):
        ds3 = pd.read_parquet(ds3_path)
        if 'datetime' not in ds3.columns:
            ds3 = ds3.reset_index()
        ds3['datetime'] = pd.to_datetime(ds3['datetime']).dt.tz_localize(None)
        warmup = ds3[ds3['datetime'] < fv2['datetime'].iloc[0]].tail(WARMUP)[['datetime','open','high','low','close']]
        combined = pd.concat([warmup, fv2[['datetime','open','high','low','close']]], ignore_index=True)
    else:
        combined = fv2[['datetime','open','high','low','close']].copy()
        warmup = pd.DataFrame()
    rsi_all = compute_rsi(combined['close'])
    macd_hist_all = compute_macd(combined['close'])
    n_warm = len(warmup)
    fv2['rsi'] = rsi_all.iloc[n_warm:].values
    fv2['macd_hist'] = macd_hist_all.iloc[n_warm:].values
    df = fv2.copy()
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    trades = []; i = 0
    while i < len(df):
        row = df.iloc[i]
        if pd.isna(row['ma20']) or pd.isna(row['atr14']):
            i += 1; continue
        if row['low'] <= row['ma20']:
            if row['hour'] >= EOD_HOUR:
                i += 1; continue
            touch_date = row['date']; atr = row['atr14']; bounce_bar = None
            for j in range(i, i + MAX_TB_GAP + 1):
                b = df.iloc[j]
                if b['date'] != touch_date or b['hour'] >= EOD_HOUR:
                    break
                if b['close'] > b['ma20']:
                    bounce_bar = b; break
            if bounce_bar is None:
                i += 1; continue
            rsi_val = bounce_bar['rsi']
            macd_val = bounce_bar['macd_hist']
            entry_idx = j + 1
            if entry_idx >= len(df):
                i += 1; continue
            entry_bar = df.iloc[entry_idx]
            if entry_bar['date'] != touch_date:
                i += 1; continue
            entry = entry_bar['open']
            pnl_atr = 0.0; outcome = None; k = entry_idx
            while k < len(df):
                kb = df.iloc[k]
                if kb['hour'] >= EOD_HOUR:
                    pnl_atr = (kb['open'] - entry) / atr
                    outcome = 'EOD+' if pnl_atr > 0 else 'EOD-'
                    k += 1; break
                if kb['high'] >= entry + BASE_TP * atr:
                    pnl_atr = BASE_TP; outcome = 'W'; k += 1; break
                if kb['low'] <= entry - BASE_SL * atr:
                    pnl_atr = -BASE_SL; outcome = 'L'; k += 1; break
                k += 1
            trades.append({'rsi': rsi_val, 'macd_hist': macd_val, 'outcome': outcome, 'pnl': pnl_atr})
            i = k
        else:
            i += 1
    return trades

csv_files = sorted(glob.glob(os.path.join(DATA_DIR, '*_5min.csv')))
all_trades = []
for f in csv_files:
    all_trades.extend(run_backtest(f))
df = pd.DataFrame(all_trades).dropna(subset=['rsi', 'macd_hist'])

def calc_pf(sub):
    gp = sub[sub['pnl'] > 0]['pnl'].sum()
    gl = abs(sub[sub['pnl'] < 0]['pnl'].sum())
    return round(gp / gl, 3) if gl > 0 else 999

BASELINE_PF = 0.922

overall_pf = calc_pf(df)
overall_wr = (df['pnl'] > 0).sum() / len(df) * 100
print(f'BASELINE : N=49,039 | PF=0.922 | Prof_WR=41.5%')
print(f'THIS RUN : N={len(df):,} | PF={overall_pf:.3f} | Prof_WR={overall_wr:.1f}%')

print()
print('-- RSI BUCKETS ---------------------------------------')
print(f'{"RSI Zone":<14} {"N":>7} {"N%":>5} {"PF":>6} {"WR%":>6}  vs BL')
print('-' * 55)
rsi_bins = [0, 20, 30, 40, 50, 60, 70, 80, 100]
rsi_labels = ['<20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '>80']
df['rsi_bucket'] = pd.cut(df['rsi'], bins=rsi_bins, labels=rsi_labels)
for b in rsi_labels:
    sub = df[df['rsi_bucket'] == b]
    if len(sub) < 10:
        continue
    pf = calc_pf(sub)
    wr = (sub['pnl'] > 0).sum() / len(sub) * 100
    pct = len(sub) / len(df) * 100
    flag = ' ^' if pf > BASELINE_PF else ' v'
    print(f'{b:<14} {len(sub):>7,} {pct:>4.1f}% {pf:>6.3f} {wr:>5.1f}%{flag}')

print()
print('-- MACD HISTOGRAM ZONES ------------------------------')
print(f'{"MACD Zone":<18} {"N":>7} {"N%":>5} {"PF":>6} {"WR%":>6}  vs BL')
print('-' * 55)
macd_bins = [-np.inf, -0.5, -0.1, 0, 0.1, 0.5, np.inf]
macd_labels = ['< -0.5', '-0.5 to -0.1', '-0.1 to 0', '0 to 0.1', '0.1 to 0.5', '> 0.5']
df['macd_zone'] = pd.cut(df['macd_hist'], bins=macd_bins, labels=macd_labels)
for b in macd_labels:
    sub = df[df['macd_zone'] == b]
    if len(sub) < 10:
        continue
    pf = calc_pf(sub)
    wr = (sub['pnl'] > 0).sum() / len(sub) * 100
    pct = len(sub) / len(df) * 100
    flag = ' ^' if pf > BASELINE_PF else ' v'
    print(f'{b:<18} {len(sub):>7,} {pct:>4.1f}% {pf:>6.3f} {wr:>5.1f}%{flag}')

# ── 2D GRID: RSI bucket x MACD zone ──────────────────────
print()
print('-- RSI x MACD 2D GRID (PF | N) ----------------------')
print('   (baseline PF=0.922 | * = PF>1.0 | ^ = beats baseline)')
print()

rsi_bins2   = [0, 30, 40, 50, 60, 70, 100]
rsi_labels2 = ['<30', '30-40', '40-50', '50-60', '60-70', '>70']
macd_bins2  = [-np.inf, -0.1, 0, 0.1, np.inf]
macd_labels2 = ['MACD<-0.1', '-0.1 to 0', '0 to 0.1', 'MACD>0.1']

df['rb'] = pd.cut(df['rsi'],       bins=rsi_bins2,  labels=rsi_labels2)
df['mb'] = pd.cut(df['macd_hist'], bins=macd_bins2, labels=macd_labels2)

header = f'{"RSI \\ MACD":<10}' + ''.join(f'{m:>16}' for m in macd_labels2)
print(header)
print('-' * (10 + 16 * len(macd_labels2)))

MIN_N = 30
for r in rsi_labels2:
    row_str = f'{r:<10}'
    for m in macd_labels2:
        sub = df[(df['rb'] == r) & (df['mb'] == m)]
        n = len(sub)
        if n < MIN_N:
            cell = f'  -- ({n:,})'
        else:
            pf = calc_pf(sub)
            flag = '*' if pf >= 1.0 else ('^' if pf > BASELINE_PF else ' ')
            cell = f'{flag}{pf:.3f} ({n:,})'
        row_str += f'{cell:>16}'
    print(row_str)

print()
print('-- TOP COMBOS (PF>baseline, N>=100) -----------------')
print(f'{"RSI":<8} {"MACD":<16} {"N":>6} {"PF":>6} {"WR%":>6}')
print('-' * 48)
results = []
for r in rsi_labels2:
    for m in macd_labels2:
        sub = df[(df['rb'] == r) & (df['mb'] == m)]
        if len(sub) < 100:
            continue
        pf = calc_pf(sub)
        wr = (sub['pnl'] > 0).sum() / len(sub) * 100
        results.append((pf, r, m, len(sub), wr))
results.sort(reverse=True)
for pf, r, m, n, wr in results[:10]:
    flag = '*' if pf >= 1.0 else ' '
    print(f'{flag}{r:<7} {m:<16} {n:>6,} {pf:>6.3f} {wr:>5.1f}%')
