import os
import upstox_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

from gss_core_option_A_validation import *
from step1_threshold_sweep import prepare_data, RANK1_PARAMS

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION & INSTRUMENT KEYS (From mega_backtest)
# ═══════════════════════════════════════════════════════════════
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTdhMTExM2Q2NTkxMDUyZGMwM2Y4OWMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTYwNzQ0MywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5NjM3NjAwfQ.x2fmxmrIhLgoY4-Iv6hpm0VmkwoMaTmzsb0F_c2v07g"

STOCKS = {
    'TATASTEEL': 'NSE_EQ|INE081A01020', 'HINDALCO': 'NSE_EQ|INE038A01020',
    'JSWSTEEL': 'NSE_EQ|INE019A01038', 'NATIONALUM': 'NSE_EQ|INE139A01034',
    'SBIN': 'NSE_EQ|INE062A01020', 'HDFCBANK': 'NSE_EQ|INE040A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021', 'AXISBANK': 'NSE_EQ|INE238A01034',
    'PNB': 'NSE_EQ|INE160A01022', 'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'INFY': 'NSE_EQ|INE009A01021', 'WIPRO': 'NSE_EQ|INE075A01022',
    'TECHM': 'NSE_EQ|INE669C01036', 'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029', 'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DIVISLAB': 'NSE_EQ|INE361B01024', 'CIPLA': 'NSE_EQ|INE059A01026',
    'RELIANCE': 'NSE_EQ|INE002A01018', 'ONGC': 'NSE_EQ|INE213A01029',
    'COALINDIA': 'NSE_EQ|INE522F01014', 'ITC': 'NSE_EQ|INE154A01025',
    'DABUR': 'NSE_EQ|INE016A01026', 'BHARTIARTL': 'NSE_EQ|INE397D01024',
    'IDEA': 'NSE_EQ|INE669E01016', 'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010', 'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'VEDL': 'NSE_EQ|INE205A01025', 'BANDHANBNK': 'NSE_EQ|INE545U01014'
}

conf = upstox_client.Configuration()
conf.access_token = ACCESS_TOKEN
api_client = upstox_client.ApiClient(conf)


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING (Following mega_backtest lines 145-189)
# ═══════════════════════════════════════════════════════════════

def fetch_5m_data(key, start, end):
    try:
        api = upstox_client.HistoryV3Api(api_client)

        # FIX 1: Use named parameters in correct order
        res = api.get_historical_candle_data1(
            instrument_key=key,
            unit="minutes",
            interval="5",
            to_date=end.strftime('%Y-%m-%d'),
            from_date=start.strftime('%Y-%m-%d')
        )

        # FIX 2: Add data validation
        if not hasattr(res, 'data') or not res.data:
            return None
        candles = res.data.candles
        if len(candles) == 0:
            return None

        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)

        # FIX 3: Calculate MA20 & avg_volume before renaming
        #debug_29 df['ma20'] = df['close'].rolling(20).mean()
        #debug_29 df['avg_volume'] = df['volume'].rolling(20).mean()

        # Then rename columns to Title Case
        df = df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume'
        })

        return df

    except Exception as e:
        print(f"Error fetching 5m data: {e}")
        return None


def fetch_daily_mas(key, end_date):
    """PROBLEM 2 FIXED: Fetch MA50/100/200 exactly like mega_backtest logic"""
    try:
        api = upstox_client.HistoryV3Api(api_client)
        start_date = end_date - timedelta(days=400)
        res = api.get_historical_candle_data1(
            instrument_key=key,
            unit="days",
            interval="1",
            to_date=end_date.strftime('%Y-%m-%d'),
            from_date=start_date.strftime('%Y-%m-%d')
        )
        # ADD: Validation check here too
        if not hasattr(res, 'data') or not res.data:
            return None
        df = pd.DataFrame(res.data.candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['datetime'] = pd.to_datetime(df['datetime']).dt.date
        df = df.sort_values('datetime').reset_index(drop=True)

        # Calculate Daily MAs
        df['ma50'] = df['close'].rolling(50).mean()
        df['ma100'] = df['close'].rolling(100).mean()
        df['ma200'] = df['close'].rolling(200).mean()
        return df[['datetime', 'ma50', 'ma100', 'ma200']]
    except Exception as e:
        print(f"Error fetching Daily: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# INTRADAY VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════

def run_intraday_validation(symbol, key, bull_threshold):
    # 1. Generate Month Tuples (2022-2025)
    months = []
    curr = datetime(2022, 1, 1)
    while curr <= datetime(2025, 12, 31):
        first = curr
        last = (datetime(curr.year + 1, 1, 1) if curr.month == 12 else datetime(curr.year, curr.month + 1,
                                                                                1)) - timedelta(days=1)
        months.append((first, last))
        curr = datetime(curr.year + (1 if curr.month == 12 else 0), (curr.month % 12) + 1, 1)

    master_trades = []
    params = RANK1_PARAMS.copy()
    params['bull_threshold'] = bull_threshold

    # 2. Iterate month-by-month to prevent data overflow
    for start_m, end_m in months:
        df_5m = fetch_5m_data(key, start_m, end_m)
        df_daily = fetch_daily_mas(key, end_m)
        if df_5m is None or df_daily is None: continue

        # Process 5-min indicators & merge Daily MA50 filter
        df_5m['datetime'] = pd.to_datetime(df_5m['datetime'])
        df = prepare_data(df_5m, params)
        df['MA20'] = df['Close'].rolling(20).mean()
        df['date'] = df['datetime'].dt.date
        df_daily = df_daily.rename(columns={'datetime': 'date'})  # Rename daily datetime to 'date'
        df = df.merge(df_daily, on='date', how='left')  # FIX: Merge on common column to preserve 'datetime'

        # 3. Daily Intraday Loop
        for date, day_df in df.groupby('date'):
            in_pos, trades_today = False, 0
            sl, target, qty, entry_p = 0, 0, 0, 0

            for i in range(1, len(day_df)):
                curr_row, prev_row = day_df.iloc[i], day_df.iloc[i - 1]
                time = curr_row['datetime'].time()

                # Entry: Only if above Daily MA50 + MA20 Bounce + GSS
                if not in_pos and trades_today < 1 and time < datetime.strptime('15:00', '%H:%M').time():
                    if curr_row['Close'] <= curr_row['ma50']: continue  # MA50 Filter Check

                    ma20_touch = prev_row['Low'] <= prev_row['MA20'] <= prev_row['High']
                    price_above = curr_row['Close'] > curr_row['MA20']

                    score = calculate_gss(curr_row['Close'], curr_row['MA'], curr_row['EMA'], curr_row['MA_5d_ago'],
                                          curr_row['ADX'], curr_row['ADX_prev'], curr_row['ADX_slope'],
                                          curr_row['RSI'], curr_row['RSI_prev'], curr_row['Price_Proximity'], params)
                    regime = map_score_to_regime(score, curr_row['Volume'], curr_row['Volume_MA'], curr_row['RSI'],
                                                 curr_row['Plus_DI'], curr_row['Minus_DI'], prev_row['Plus_DI'],
                                                 prev_row['Minus_DI'], curr_row['ADX_slope'], params)

                    if ma20_touch and price_above and regime == "BULL":
                        in_pos, entry_p = True, curr_row['Close']
                        qty, trades_today = (50000 // entry_p), 1
                        sl, target = entry_p - (curr_row['ATR'] * 1.5), entry_p + (curr_row['ATR'] * 3.0)

                elif in_pos:  # Exit: SL / Target / EOD
                    if curr_row['Close'] > (entry_p + curr_row['ATR']): sl = max(sl, entry_p)  # Trailing SL
                    exit_trigger = (curr_row['Low'] <= sl) or (curr_row['High'] >= target) or (
                                time >= datetime.strptime('15:15', '%H:%M').time())
                    if exit_trigger:
                        exit_p = sl if curr_row['Low'] <= sl else (
                            target if curr_row['High'] >= target else curr_row['Close'])
                        master_trades.append((exit_p - entry_p) * qty)
                        in_pos = False

    trades = np.array(master_trades)
    return {
        'stock': symbol, 'total_trades': len(trades), 'net_pnl': np.sum(trades),
        'win_rate': (len(trades[trades > 0]) / len(trades) * 100) if len(trades) > 0 else 0,
        'wl_ratio': (np.mean(trades[trades > 0]) / abs(np.mean(trades[trades <= 0]))) if (trades > 0).any() and (
                    trades <= 0).any() else 0
    }


if __name__ == "__main__":
    sweep = pd.read_csv('threshold_sweep_results.csv')
    best_threshold = int(sweep.loc[sweep['test_precision'].idxmax()]['threshold'])

    results = []
    print(f"Starting Validation for {len(STOCKS)} stocks (2022-2025)...")
    for name, key in STOCKS.items():
        res = run_intraday_validation(name, key, best_threshold)
        if res:
            results.append(res)
            print(f"✅ {name}: PNL ₹{res['net_pnl']:.0f} | Win%: {res['win_rate']:.1f}%")

    pd.DataFrame(results).to_csv('multistock_trading_results.csv', index=False)