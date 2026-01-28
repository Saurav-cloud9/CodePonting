import pandas as pd
import numpy as np
import yfinance as yf
from gss_core_option_A_validation import *
import warnings

warnings.filterwarnings('ignore')

RANK1_PARAMS = {
    'use_long_term_anchor': True, 'use_ma_slope': True, 'use_adx_strength': True,
    'use_adx_acceleration': True, 'use_rsi_equilibrium': True, 'use_rsi_rising': True,
    'use_rsi_ignition': False, 'use_rsi_exhaustion': True, 'use_price_proximity': True,
    'use_volume_confirmation': False, 'ma_period': 38, 'ema_period': 220,
    'adx_period': 14, 'rsi_period': 14, 'atr_multiplier': 1.00, 'ma_slope_threshold': 0.070,
    'adx_strength_threshold': 23, 'rsi_exhaustion_threshold': 70, 'price_proximity_max': 4.0,
    'vol_standard': 1.0, 'vol_momentum': 1.0, 'require_fresh_momentum': False, 'bear_threshold': 20
}


def prepare_data(df, params):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df['MA'] = df['Close'].rolling(params['ma_period']).mean()
    df['EMA'] = df['Close'].ewm(span=params['ema_period']).mean()
    df['MA_5d_ago'] = df['MA'].shift(5)
    df['ADX'], df['Plus_DI'], df['Minus_DI'] = calculate_adx(df, params['adx_period'])
    df['ADX_prev'] = df['ADX'].shift(1)
    df['ADX_slope'] = df['ADX'].diff().rolling(3).mean()
    df['ATR'] = calculate_atr(df, 14)
    df['RSI'] = calculate_rsi(df['Close'], params['rsi_period'])
    df['RSI_prev'] = df['RSI'].shift(1)
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    df['Price_Proximity'] = (df['Close'] - df['MA']).abs() / df['MA'] * 100
    return df.dropna()


def run_sweep():
    print("STEP 1: THRESHOLD SWEEP (NIFTY)")
    df_raw = yf.download('^NSEI', start='2015-01-01', end='2025-12-31', progress=False)
    df = prepare_data(df_raw, RANK1_PARAMS)

    # Ground Truth Labeling
    actuals = [calculate_actual_regime_lookahead(df, i, 5, 1.0) for i in range(len(df))]
    df['Actual_Regime'] = actuals

    results = []
    for thresh in range(45, 61):
        params = RANK1_PARAMS.copy()
        params['bull_threshold'] = thresh
        correct, total = 0, 0

        for i in range(1, len(df)):
            row, prev = df.iloc[i], df.iloc[i - 1]
            score = calculate_gss(row['Close'], row['MA'], row['EMA'], row['MA_5d_ago'], row['ADX'], row['ADX_prev'],
                                  row['ADX_slope'], row['RSI'], row['RSI_prev'], row['Price_Proximity'], params)
            pred = map_score_to_regime(score, row['Volume'], row['Volume_MA'], row['RSI'], row['Plus_DI'],
                                       row['Minus_DI'], prev['Plus_DI'], prev['Minus_DI'], row['ADX_slope'], params)

            if pred == "BULL":
                total += 1
                if row['Actual_Regime'] == "BULL": correct += 1

        prec = (correct / total * 100) if total > 0 else 0
        results.append({'threshold': thresh, 'test_precision': prec})
        print(f"Thresh {thresh}: {prec:.2f}%")

    pd.DataFrame(results).to_csv('threshold_sweep_results.csv', index=False)


if __name__ == "__main__": run_sweep()