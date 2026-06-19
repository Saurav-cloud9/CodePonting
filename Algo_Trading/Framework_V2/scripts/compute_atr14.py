import pandas as pd
import numpy as np
import os

DS3_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V1\data\historical\intraday_5min_DS3'
FV2_DIR  = r'C:\Users\Saurav\CodePonting\Algo_Trading\Framework_V2\data\historical\csv\intraday_5min'
WARMUP   = 30  # bars before 2022 to prepend for ATR warm-up

STOCKS = [
    'ADANIPORTS','ASHOKLEY','AXISBANK','BAJFINANCE','BANDHANBNK',
    'BHARTIARTL','CIPLA','COALINDIA','DABUR','DIVISLAB',
    'HDFCBANK','HINDALCO','ICICIBANK','INDUSINDBK','INFY',
    'ITC','JSWSTEEL','NATIONALUM','NTPC','ONGC',
    'PNB','POWERGRID','RELIANCE','SBIN','SUNPHARMA',
    'TATAMOTORS','TATASTEEL','TECHM','VEDL','WIPRO',
]

def compute_atr14(symbols):
    for stock in symbols:
        fv2_path = os.path.join(FV2_DIR, f'{stock}_5min.csv')
        ds3_path = os.path.join(DS3_DIR, f'{stock}.parquet')

        if not os.path.exists(fv2_path):
            print(f'SKIP {stock} — fv2 CSV not found'); continue
        if not os.path.exists(ds3_path):
            print(f'SKIP {stock} — DS3 parquet not found'); continue

        fv2 = pd.read_csv(fv2_path)
        fv2.columns = fv2.columns.str.strip()
        fv2['datetime'] = pd.to_datetime(fv2['datetime']).dt.tz_localize(None)

        ds3 = pd.read_parquet(ds3_path)
        ds3.columns = ds3.columns.str.strip()
        if ds3.index.name == 'datetime' or 'datetime' not in ds3.columns:
            ds3 = ds3.reset_index()
        ds3['datetime'] = pd.to_datetime(ds3['datetime']).dt.tz_localize(None)

        # last WARMUP bars before 2022
        warmup = ds3[ds3['datetime'] < fv2['datetime'].iloc[0]].tail(WARMUP)[['datetime','open','high','low','close']]

        # combine warmup + fv2
        combined = pd.concat([warmup, fv2[['datetime','open','high','low','close']]], ignore_index=True)

        pc = combined['close'].shift(1)
        tr = np.maximum(combined['high'] - combined['low'],
             np.maximum((combined['high'] - pc).abs(), (combined['low'] - pc).abs()))
        atr14 = tr.rolling(14, min_periods=14).mean()

        # drop warmup rows, align with fv2
        fv2['atr14'] = atr14.iloc[len(warmup):].values
        fv2.to_csv(fv2_path, index=False)
        print(f'OK  {stock} — atr14 added ({fv2["atr14"].notna().sum()} valid rows)')

if __name__ == '__main__':
    import sys
    symbols = sys.argv[1:] if len(sys.argv) > 1 else STOCKS
    compute_atr14(symbols)
