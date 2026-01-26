"""
GSS Validation Script
─────────────────────
Validates Gemini's Scoring System against Nifty historical data (Jan 2022 - Dec 2025)
Uses Day N-1 data to predict Day N regime, compares with actual regime
"""

import pandas as pd
import yfinance as yf


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


def calculate_gss(price, ma20, ema200, ma20_5d_ago, adx, prev_adx, rsi, prev_rsi, plus_di, minus_di):
    """
    GSS v3.1: Alpha-Generating Predictive System with Directional Filtering
    Returns: score (0-100)
    
    Changes from v3.0:
    - Added directional filter: ADX points only if +DI > -DI (prevents scoring bearish crashes)
    - RSI exhaustion penalty: -10 pts if RSI > 70 (avoids buying peaks)
    - Maintains v3.0 leading indicators and relaxed thresholds
    """
    # Convert all inputs to float to avoid Series comparison errors
    price = price.iloc[0] if hasattr(price, 'iloc') else float(price)
    ma20 = ma20.iloc[0] if hasattr(ma20, 'iloc') else float(ma20)
    ema200 = ema200.iloc[0] if hasattr(ema200, 'iloc') else float(ema200)
    ma20_5d_ago = ma20_5d_ago.iloc[0] if hasattr(ma20_5d_ago, 'iloc') else float(ma20_5d_ago)
    adx = adx.iloc[0] if hasattr(adx, 'iloc') else float(adx)
    prev_adx = prev_adx.iloc[0] if hasattr(prev_adx, 'iloc') else float(prev_adx)
    rsi = rsi.iloc[0] if hasattr(rsi, 'iloc') else float(rsi)
    prev_rsi = prev_rsi.iloc[0] if hasattr(prev_rsi, 'iloc') else float(prev_rsi)
    plus_di = plus_di.iloc[0] if hasattr(plus_di, 'iloc') else float(plus_di)
    minus_di = minus_di.iloc[0] if hasattr(minus_di, 'iloc') else float(minus_di)

    score = 0

    # Factor 1: Long-term Anchor (15 pts)
    if price > ema200:
        score += 15

    # Factor 2: MA20 Slope (20 pts)
    ma_slope_pct = ((ma20 - ma20_5d_ago) / ma20_5d_ago) * 100
    if ma_slope_pct > 0.05:
        score += 20

    # Factor 3A: ADX Strength (15 pts) - ONLY IF BULLISH DIRECTION
    # Critical: Only award points if +DI > -DI (upward directional movement)
    if adx > 20 and plus_di > minus_di:
        score += 15
    
    # Factor 3B: ADX Acceleration (15 pts) - ONLY IF BULLISH DIRECTION
    if adx > prev_adx and adx > 15 and plus_di > minus_di:
        score += 15

    # Factor 4A: RSI Above Equilibrium (10 pts)
    if rsi > 50:
        score += 10
    
    # Factor 4B: RSI Rising (10 pts)
    if rsi > prev_rsi:
        score += 10
    
    # Factor 4C: RSI Exhaustion Penalty (-10 pts)
    # Prevents buying overbought peaks that are about to reverse
    if rsi > 70:
        score -= 10

    # Factor 5: Price Proximity (15 pts)
    dist_pct = (price - ma20) / ma20 * 100
    if 0 < dist_pct <= 3:
        score += 15

    return score


def map_score_to_regime(score, volume, volume_ma20, adx_slope, rsi):
    """
    Convert GSS score to regime label with relaxed volume confirmation
    v3.1: Significantly reduced volume requirements to stop over-filtering
    """
    # Convert inputs to float
    volume = volume.iloc[0] if hasattr(volume, 'iloc') else float(volume)
    volume_ma20 = volume_ma20.iloc[0] if hasattr(volume_ma20, 'iloc') else float(volume_ma20)
    adx_slope = adx_slope.iloc[0] if hasattr(adx_slope, 'iloc') else float(adx_slope)
    rsi = rsi.iloc[0] if hasattr(rsi, 'iloc') else float(rsi)
    
    # Dynamic volume threshold - MUCH more lenient than v3.0
    if adx_slope > 0 and rsi > 50:  # Confirmed momentum
        volume_threshold = 1.0  # Average volume is enough
    else:
        volume_threshold = 1.05  # Only 5% above average (was 1.2x in v3.0)
    
    volume_confirmed = volume > (volume_ma20 * volume_threshold)
    
    # Regime mapping
    if score >= 70 and volume_confirmed:
        return "BULL"
    elif score >= 30:
        return "SIDEWAYS"
    else:
        return "BEAR"


# ═══════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_gss():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                        GSS VALIDATION SCRIPT                                 ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")

    # Step 1: Download Nifty data
    print("📥 Downloading Nifty data (Jan 2022 - Dec 2025)...")
    start_date = "2021-01-01"  # Larger buffer so long MAs/ADX have data before 2022
    end_date = "2026-01-10"  # Extra buffer for 5-day future-truth

    nifty = yf.download("^NSEI", start=start_date, end=end_date, progress=False)

    # Flatten columns if MultiIndex
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)

    if nifty.empty:
        print("❌ Failed to download Nifty data. Check internet connection.")
        return

    print(f"✅ Downloaded {len(nifty)} days of data\n")

    # Step 2: Calculate indicators
    print("🔧 Calculating indicators...")
    nifty['MA20'] = nifty['Close'].rolling(20).mean()
    nifty['MA50'] = nifty['Close'].rolling(50).mean()
    nifty['EMA200'] = nifty['Close'].ewm(span=200).mean()
    nifty['MA20_5d_ago'] = nifty['MA20'].shift(5)  # Pre-calculate for safety
    nifty['Volume_MA20'] = nifty['Volume'].rolling(20).mean()  # Volume average
    nifty['ADX'], nifty['Plus_DI'], nifty['Minus_DI'] = calculate_adx(nifty, period=14)  # Unpack all 3 values
    nifty['ATR'] = calculate_atr(nifty, period=14)  # For volatility-adjusted regime detection
    nifty['RSI'] = calculate_rsi(nifty['Close'], period=14)  # Leading momentum indicator
    nifty['ADX_slope'] = nifty['ADX'].diff()  # ADX acceleration
    
    print(f"📊 ADX Stats: Min={nifty['ADX'].min():.2f}, Max={nifty['ADX'].max():.2f}, Mean={nifty['ADX'].mean():.2f}")
    print(f"📊 +DI/-DI: Mean +DI={nifty['Plus_DI'].mean():.2f}, Mean -DI={nifty['Minus_DI'].mean():.2f}")
    print(f"📊 ATR Stats: Min={nifty['ATR'].min():.2f}, Max={nifty['ATR'].max():.2f}, Mean={nifty['ATR'].mean():.2f}")
    print(f"📊 RSI Stats: Min={nifty['RSI'].min():.2f}, Max={nifty['RSI'].max():.2f}, Mean={nifty['RSI'].mean():.2f}")

    # Filter to validation period (Jan 2022 onwards) BEFORE dropna
    nifty = nifty[nifty.index >= '2022-01-01']

    # Drop rows with NaN values before calculating actual regime
    nifty = nifty.dropna()

    # Calculate actual regime using Future-Truth logic
    actual_regimes = []
    for i in range(len(nifty)):
        regime = calculate_actual_regime_lookahead(nifty, i, lookahead=5)
        actual_regimes.append(regime)
    nifty['Actual_Regime'] = actual_regimes

    print(f"✅ Indicators calculated for {len(nifty)} trading days\n")

    # Step 3: Calculate GSS predictions (using N-1 data)
    print("🤖 Running GSS predictions...")

    gss_scores = []
    gss_predictions = []

    for i in range(1, len(nifty)):
        # Use previous day's data (N-1)
        prev_idx = i - 1
        prev_row = nifty.iloc[prev_idx]

        # Get MA20_5d_ago from pre-calculated column (safe, vectorized)
        ma20_5d_ago = prev_row['MA20_5d_ago']

        # Get prev_adx and prev_rsi (from day before N-1)
        if i >= 2:
            prev_adx = nifty.iloc[i - 2]['ADX']
            prev_rsi = nifty.iloc[i - 2]['RSI']
        else:
            prev_adx = prev_row['ADX']  # Fallback for early days
            prev_rsi = prev_row['RSI']

        # Calculate GSS score using N-1 data with directional indicators
        score = calculate_gss(
            price=prev_row['Close'],
            ma20=prev_row['MA20'],
            ema200=prev_row['EMA200'],
            ma20_5d_ago=ma20_5d_ago,
            adx=prev_row['ADX'],
            prev_adx=prev_adx,
            rsi=prev_row['RSI'],
            prev_rsi=prev_rsi,
            plus_di=prev_row['Plus_DI'],
            minus_di=prev_row['Minus_DI']
        )

        # Apply volume-aware regime mapping with relaxed volume filter
        prediction = map_score_to_regime(
            score=score,
            volume=prev_row['Volume'],
            volume_ma20=prev_row['Volume_MA20'],
            adx_slope=prev_row['ADX_slope'],
            rsi=prev_row['RSI']
        )

        gss_scores.append(score)
        gss_predictions.append(prediction)

    # Add to dataframe (skip first row since we need N-1)
    nifty = nifty.iloc[1:].copy()
    nifty['GSS_Score'] = gss_scores
    nifty['GSS_Prediction'] = gss_predictions

    # Step 4: Compare predictions with actual
    nifty['Match'] = nifty['GSS_Prediction'] == nifty['Actual_Regime']

    # Calculate accuracy
    total_days = len(nifty)
    matches = nifty['Match'].sum()
    accuracy = (matches / total_days) * 100

    print(f"✅ GSS predictions completed\n")

    # Step 5: Results
    print("═══════════════════════════════════════════════════════════════════════════════")
    print("                              VALIDATION RESULTS")
    print("═══════════════════════════════════════════════════════════════════════════════")
    print(f"\nTotal Trading Days:  {total_days}")
    print(f"Correct Predictions: {matches}")
    print(f"Wrong Predictions:   {total_days - matches}")
    print(f"\n🎯 ACCURACY: {accuracy:.2f}%\n")

    # Regime-wise accuracy
    print("─────────────────────────────────────────────────────────────────────────────")
    print("REGIME-WISE BREAKDOWN:")
    print("─────────────────────────────────────────────────────────────────────────────")

    for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
        regime_data = nifty[nifty['Actual_Regime'] == regime]
        if len(regime_data) > 0:
            regime_matches = regime_data['Match'].sum()
            regime_total = len(regime_data)
            regime_accuracy = (regime_matches / regime_total) * 100
            print(
                f"{regime:10} Days: {regime_total:4} | Correct: {regime_matches:4} | Accuracy: {regime_accuracy:5.1f}%")

    print("─────────────────────────────────────────────────────────────────────────────")
    print("GSS PREDICTION COUNTS:")
    print("─────────────────────────────────────────────────────────────────────────────")
    
    # Show what GSS predicted
    gss_pred_counts = nifty['GSS_Prediction'].value_counts()
    for regime in ['BULL', 'BEAR', 'SIDEWAYS']:
        if regime in gss_pred_counts.index:
            count = gss_pred_counts[regime]
            pct = (count / total_days) * 100
            
            # Calculate precision for each prediction
            regime_predictions = nifty[nifty['GSS_Prediction'] == regime]
            correct_preds = (regime_predictions['GSS_Prediction'] == regime_predictions['Actual_Regime']).sum()
            precision = (correct_preds / count * 100) if count > 0 else 0
            
            print(f"{regime:10} GSS called: {count:4} times ({pct:5.1f}%) | Precision: {precision:5.1f}%")
        else:
            print(f"{regime:10} GSS called:    0 times (  0.0%) | Precision:   0.0%")

    print("─────────────────────────────────────────────────────────────────────────────\n")

    # Step 6: Show mismatches
    mismatches = nifty[~nifty['Match']].copy()

    if len(mismatches) > 0:
        print("❌ MISMATCH EXAMPLES (First 10):")
        print("─────────────────────────────────────────────────────────────────────────────")
        display_cols = ['Close', 'MA20', 'ADX', 'Plus_DI', 'Minus_DI', 'RSI', 'GSS_Score', 'Actual_Regime', 'GSS_Prediction']
        print(mismatches[display_cols].head(10).to_string())
        print("\n")

    import os
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gss_results.csv")
    nifty.to_csv(output_file)
    print(f"💾 Results saved to: {output_file}\n")

    # Step 8: Decision
    print("═══════════════════════════════════════════════════════════════════════════════")
    print("VALIDATION METHOD: GSS v3.1 with Directional Filtering + ATR-based Future-Truth")
    print("Regime labels: BULL/BEAR if 5-day move > 1.5×ATR, else SIDEWAYS")
    print("GSS v3.1 Changes:")
    print("  • Directional filter: ADX points ONLY if +DI > -DI (prevents scoring bearish crashes)")
    print("  • RSI exhaustion penalty: -10 pts if RSI > 70 (avoids buying overbought peaks)")
    print("  • Relaxed volume filter: 1.05x standard, 1.0x for confirmed momentum")
    print("  • Maintains v3.0 leading indicators (RSI momentum, ADX acceleration)")
    print("BULL requires: Score ≥70 AND Volume confirmation")
    print("─────────────────────────────────────────────────────────────────────────────")
    if accuracy >= 70:
        print("✅ GSS HAS PREDICTIVE EDGE! Accuracy >= 70% - Strategy has alpha.")
    elif accuracy >= 60:
        print("⚠️  GSS ACCEPTABLE. Accuracy 60-70% - Better than random, review edge cases.")
    elif accuracy >= 50:
        print("⚠️  GSS MARGINAL. Accuracy 50-60% - Slight edge, needs weight tuning.")
    else:
        print("❌ GSS NO EDGE. Accuracy < 50% - Worse than coin flip, major revision needed.")
    print("═══════════════════════════════════════════════════════════════════════════════")


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    validate_gss()