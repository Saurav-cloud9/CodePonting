import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# INDICATOR CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

def calculate_adx(df, period=14):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)

    high, low, close = df['High'], df['Low'], df['Close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    up = high - high.shift(1)
    down = low.shift(1) - low

    plus_dm = up.where((up > down) & (up > 0), 0)
    minus_dm = down.where((down > up) & (down > 0), 0)

    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)

    di_sum = plus_di + minus_di
    di_diff = (plus_di - minus_di).abs()
    dx = 100 * (di_diff / di_sum.replace(0, float('nan'))).fillna(0)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx, plus_di, minus_di


def calculate_atr(df, period=14):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    tr = pd.concat([(df['High'] - df['Low']),
                    (df['High'] - df['Close'].shift(1)).abs(),
                    (df['Low'] - df['Close'].shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1 / period, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - (100 / (1 + (gain / loss)))


def calculate_actual_regime_lookahead(df, current_idx, lookahead=5, atr_multiplier=1.5):
    if current_idx + lookahead >= len(df): return "SIDEWAYS"

    start_p = df.iloc[current_idx]['Close']
    future_p = df.iloc[current_idx + lookahead]['Close']
    atr_val = df.iloc[current_idx]['ATR']

    diff = (future_p - start_p) / start_p
    thresh = (atr_multiplier * atr_val) / start_p

    if diff > thresh:
        return "BULL"
    elif diff < -thresh:
        return "BEAR"
    return "SIDEWAYS"


# ═══════════════════════════════════════════════════════════════════════════
# GSS SCORING & REGIME MAPPING (Aligned for Option A Validation)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_gss(price, ma, ema, ma_prev, adx, prev_adx, adx_slope, rsi, prev_rsi, price_proximity, params):
    """
    Scoring engine modified for 11-argument 'Option A' signature.
    Directional DI checks moved to map_score_to_regime.
    """
    score = 0

    # Factor 1: Anchor
    if params.get('use_long_term_anchor', True) and price > ema:
        score += 15

    # Factor 2: MA Slope
    if params.get('use_ma_slope', True):
        if ((ma - ma_prev) / ma_prev) * 100 > params['ma_slope_threshold']:
            score += 20

    # Factor 3: ADX Logic (Pure Strength/Acceleration)
    if params.get('use_adx_strength', True):
        if adx > params['adx_strength_threshold']:
            score += 15

    if params.get('use_adx_acceleration', True):
        if adx > prev_adx and adx > 15:
            score += 15

    # Factor 4: RSI Logic
    if params.get('use_rsi_equilibrium', True) and rsi > 50: score += 10
    if params.get('use_rsi_rising', True) and rsi > prev_rsi: score += 10
    if params.get('use_rsi_ignition', True) and rsi > 50 and prev_rsi <= 50: score += 5
    if params.get('use_rsi_exhaustion', True) and rsi > params['rsi_exhaustion_threshold']: score -= 10

    # Factor 5: Price Proximity (Uses pre-calculated value from Step 1/2)
    if params.get('use_price_proximity', True):
        if 0 < price_proximity <= params['price_proximity_max']:
            score += 15

    return score


def map_score_to_regime(score, volume, volume_ma, rsi, plus_di, minus_di, prev_plus_di, prev_minus_di, adx_slope,
                        params):
    """
    Corrected signature to match validation script call.
    Handles all directional and volume filters.
    """
    # Volume Confirmation
    vol_confirmed = True
    if params.get('use_volume_confirmation', True):
        v_thresh = params['vol_momentum'] if (adx_slope > 0 and rsi > 50) else params['vol_standard']
        vol_confirmed = volume > (volume_ma * v_thresh)

    # BULL Logic
    is_bull_dir = plus_di > minus_di
    if params.get('require_fresh_momentum', False):
        is_bull_dir = is_bull_dir and (plus_di > prev_plus_di)

    if score >= params['bull_threshold'] and is_bull_dir and vol_confirmed:
        return "BULL"

    # BEAR Logic
    is_bear_dir = minus_di > plus_di
    if params.get('require_fresh_momentum', False):
        is_bear_dir = is_bear_dir and (minus_di > prev_minus_di)

    if score <= params['bear_threshold'] and is_bear_dir and vol_confirmed:
        return "BEAR"

    return "SIDEWAYS"