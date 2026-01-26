"""
GSS Core Engine - Reusable Components (v4.0)
=============================================
All indicator calculations and regime mapping logic.
All parameters are exposed as arguments (no hardcoding).

FIXES APPLIED:
- Fix #4: Price proximity parameterization (2.0-5.0 range)
- Fix #5: RSI ignition bonus (+5 pts for crossing 50)

Usage:
    from gss_core import calculate_gss, map_score_to_regime
    score = calculate_gss(price, ma, ema, ..., params)
    regime = map_score_to_regime(score, volume, ..., params)
"""

import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# INDICATOR CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

def calculate_adx(df, period=14):
    """
    Calculate ADX with Wilder's smoothing
    Returns: (adx, plus_di, minus_di) for directional filtering
    """
    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)

    high = df['High']
    low = df['Low']
    close = df['Close']

    # True Range components
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    # Directional Movement
    up = high - high.shift(1)
    down = low.shift(1) - low

    plus_dm = up.where((up > down) & (up > 0), 0)
    minus_dm = down.where((down > up) & (down > 0), 0)

    # Smooth DM and calculate DI
    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)

    # Calculate DX
    di_sum = plus_di + minus_di
    di_diff = (plus_di - minus_di).abs()
    dx = 100 * (di_diff / di_sum.replace(0, float('nan')))
    dx = dx.fillna(0)

    # Smooth to get ADX
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx, plus_di, minus_di


def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR) with Wilder's smoothing
    Used for volatility-adjusted regime detection
    """
    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # True Range components
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's smoothing (same as ADX)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return atr


def calculate_rsi(series, period=14):
    """
    Calculate Relative Strength Index (RSI) with Wilder's smoothing
    Leading momentum indicator for early trend detection
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Wilder's smoothing (same as ADX/ATR)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_actual_regime_lookahead(df, current_idx, lookahead=5):
    """
    Future-Truth Logic: What actually happened to the price?
    Uses ATR-based dynamic threshold to filter out market noise (beta)
    Only labels BULL/BEAR for moves that exceed 1.5×ATR (statistically significant)
    
    IMPORTANT: Returns regime label for current_idx (the day the move STARTS from)
    """
    if current_idx + lookahead >= len(df):
        return "SIDEWAYS"
    
    start_price = df.iloc[current_idx]['Close']
    future_price = df.iloc[current_idx + lookahead]['Close']
    
    # Calculate 5-day return as decimal (not percentage)
    change_decimal = (future_price - start_price) / start_price
    
    # Get 14-day ATR at current index
    atr_value = df.iloc[current_idx]['ATR']
    
    # Convert ATR to decimal threshold (volatility-adjusted)
    atr_threshold = (1.5 * atr_value) / start_price
    
    # Label regimes: only significant moves (>1.5×ATR) are BULL/BEAR
    if change_decimal > atr_threshold:
        return "BULL"
    elif change_decimal < -atr_threshold:
        return "BEAR"
    else:
        return "SIDEWAYS"  # Move within normal volatility = noise


# ═══════════════════════════════════════════════════════════════════════════
# GSS SCORING & REGIME MAPPING (Parameterized)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_gss(price, ma, ema, ma_prev, adx, prev_adx, rsi, prev_rsi, 
                  plus_di, minus_di, prev_plus_di, params):
    """
    GSS v4.0 Scoring Engine (Fully Parameterized)
    
    Args:
        price: Current price
        ma: Short-term MA value
        ema: Long-term EMA value
        ma_prev: MA value from N days ago
        adx: Current ADX
        prev_adx: Previous ADX
        rsi: Current RSI
        prev_rsi: Previous RSI
        plus_di: Current +DI
        minus_di: Current -DI
        prev_plus_di: Previous +DI
        params: Dictionary with:
            - ma_slope_threshold: Minimum MA slope % for points
            - adx_strength_threshold: Minimum ADX for strength points
            - rsi_exhaustion_threshold: RSI level for penalty
            - price_proximity_max: Maximum distance from MA for points
            - require_fresh_momentum: Boolean for +DI rising requirement
    
    Returns:
        score (0-100+, can exceed 100 with RSI ignition bonus)
    """
    # Convert all inputs to float
    price = price.iloc[0] if hasattr(price, 'iloc') else float(price)
    ma = ma.iloc[0] if hasattr(ma, 'iloc') else float(ma)
    ema = ema.iloc[0] if hasattr(ema, 'iloc') else float(ema)
    ma_prev = ma_prev.iloc[0] if hasattr(ma_prev, 'iloc') else float(ma_prev)
    adx = adx.iloc[0] if hasattr(adx, 'iloc') else float(adx)
    prev_adx = prev_adx.iloc[0] if hasattr(prev_adx, 'iloc') else float(prev_adx)
    rsi = rsi.iloc[0] if hasattr(rsi, 'iloc') else float(rsi)
    prev_rsi = prev_rsi.iloc[0] if hasattr(prev_rsi, 'iloc') else float(prev_rsi)
    plus_di = plus_di.iloc[0] if hasattr(plus_di, 'iloc') else float(plus_di)
    minus_di = minus_di.iloc[0] if hasattr(minus_di, 'iloc') else float(minus_di)
    prev_plus_di = prev_plus_di.iloc[0] if hasattr(prev_plus_di, 'iloc') else float(prev_plus_di)
    
    score = 0
    
    # Factor 1: Long-term Anchor (15 pts)
    if price > ema:
        score += 15
    
    # Factor 2: MA Slope (20 pts) - Parameterized threshold
    ma_slope_pct = ((ma - ma_prev) / ma_prev) * 100
    if ma_slope_pct > params['ma_slope_threshold']:
        score += 20
    
    # Factor 3A: ADX Strength (15 pts) - With directional filter
    # Optionally require fresh momentum
    if params['require_fresh_momentum']:
        # Strict: +DI must be rising
        if adx > params['adx_strength_threshold'] and plus_di > minus_di and plus_di > prev_plus_di:
            score += 15
    else:
        # Relaxed: Just need bullish direction
        if adx > params['adx_strength_threshold'] and plus_di > minus_di:
            score += 15
    
    # Factor 3B: ADX Acceleration (15 pts) - With directional filter
    if params['require_fresh_momentum']:
        if adx > prev_adx and adx > 15 and plus_di > minus_di and plus_di > prev_plus_di:
            score += 15
    else:
        if adx > prev_adx and adx > 15 and plus_di > minus_di:
            score += 15
    
    # Factor 4A: RSI Above Equilibrium (10 pts)
    if rsi > 50:
        score += 10
    
    # Factor 4B: RSI Rising (10 pts)
    if rsi > prev_rsi:
        score += 10
    
    # Factor 4C: RSI Ignition Bonus (5 pts) - FIX #5
    # Bonus for RSI crossing above 50 centerline (predictive of regime shift)
    if rsi > 50 and prev_rsi <= 50:
        score += 5
    
    # Factor 4D: RSI Exhaustion Penalty (-10 pts) - Parameterized threshold
    if rsi > params['rsi_exhaustion_threshold']:
        score -= 10
    
    # Factor 5: Price Proximity (15 pts) - FIX #4: Parameterized range
    dist_pct = (price - ma) / ma * 100
    if 0 < dist_pct <= params['price_proximity_max']:
        score += 15
    
    return score


def map_score_to_regime(score, volume, volume_ma, adx_slope, rsi, 
                        plus_di, minus_di, prev_plus_di, prev_minus_di, params):
    """
    Regime Mapping Engine (Fully Parameterized)
    
    Args:
        score: GSS score
        volume: Current volume
        volume_ma: Volume moving average
        adx_slope: ADX change (smoothed, for momentum detection)
        rsi: Current RSI
        plus_di: Current +DI
        minus_di: Current -DI
        prev_plus_di: Previous +DI
        prev_minus_di: Previous -DI
        params: Dictionary with:
            - bull_threshold: Minimum score for BULL
            - bear_threshold: Maximum score for BEAR
            - vol_standard: Standard volume multiplier
            - vol_momentum: High-momentum volume multiplier
            - require_fresh_momentum: Boolean for DI rising requirement
    
    Returns:
        regime: "BULL", "BEAR", or "SIDEWAYS"
    """
    # Convert inputs to float
    volume = volume.iloc[0] if hasattr(volume, 'iloc') else float(volume)
    volume_ma = volume_ma.iloc[0] if hasattr(volume_ma, 'iloc') else float(volume_ma)
    adx_slope = adx_slope.iloc[0] if hasattr(adx_slope, 'iloc') else float(adx_slope)
    rsi = rsi.iloc[0] if hasattr(rsi, 'iloc') else float(rsi)
    plus_di = plus_di.iloc[0] if hasattr(plus_di, 'iloc') else float(plus_di)
    minus_di = minus_di.iloc[0] if hasattr(minus_di, 'iloc') else float(minus_di)
    prev_plus_di = prev_plus_di.iloc[0] if hasattr(prev_plus_di, 'iloc') else float(prev_plus_di)
    prev_minus_di = prev_minus_di.iloc[0] if hasattr(prev_minus_di, 'iloc') else float(prev_minus_di)
    
    # Dynamic volume threshold (uses smoothed ADX slope)
    if adx_slope > 0 and rsi > 50:  # Confirmed momentum
        volume_threshold = params['vol_momentum']
    else:
        volume_threshold = params['vol_standard']
    
    volume_confirmed = volume > (volume_ma * volume_threshold)
    
    # BULL: Fresh bullish momentum + volume
    bull_directional = plus_di > minus_di
    if params['require_fresh_momentum']:
        bull_directional = bull_directional and (plus_di > prev_plus_di)
    
    if score >= params['bull_threshold'] and bull_directional and volume_confirmed:
        return "BULL"
    
    # BEAR: Fresh bearish momentum + volume
    bear_directional = minus_di > plus_di
    if params['require_fresh_momentum']:
        bear_directional = bear_directional and (minus_di > prev_minus_di)
    
    if score <= params['bear_threshold'] and bear_directional and volume_confirmed:
        return "BEAR"
    
    # SIDEWAYS: Everything else
    return "SIDEWAYS"
