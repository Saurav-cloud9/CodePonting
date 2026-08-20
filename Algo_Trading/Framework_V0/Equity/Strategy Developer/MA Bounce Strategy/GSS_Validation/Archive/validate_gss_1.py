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
    """Calculate ADX (Average Directional Index)"""
    high = df['High']
    low = df['Low']
    close = df['Close']

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    # Directional Movement
    up = high - high.shift(1)
    down = low.shift(1) - low

    plus_dm = up.copy()
    plus_dm[up <= down] = 0
    plus_dm[plus_dm < 0] = 0

    minus_dm = down.copy()
    minus_dm[down <= up] = 0
    minus_dm[minus_dm < 0] = 0

    plus_di = 100 * (plus_dm.rolling(period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period, min_periods=period).mean() / atr)

    # ADX calculation - fixed zero-division handling
    di_sum = plus_di + minus_di
    dx = pd.Series(index=df.index, dtype=float)
    mask = di_sum > 0
    dx[mask] = 100 * ((plus_di[mask] - minus_di[mask]).abs() / di_sum[mask])
    dx[~mask] = 0
    adx = dx.rolling(period, min_periods=period).mean()

    # Ensure we return a Series, not a DataFrame
    if isinstance(adx, pd.DataFrame):
        adx = adx.iloc[:, 0]

    return adx


def calculate_actual_regime(row):
    """Simple regime classification based on price vs MAs"""
    price = row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else float(row['Close'])
    ma20 = row['MA20'].iloc[0] if hasattr(row['MA20'], 'iloc') else float(row['MA20'])
    ma50 = row['MA50'].iloc[0] if hasattr(row['MA50'], 'iloc') else float(row['MA50'])

    if price > ma20 > ma50:
        return "BULL"
    elif price < ma20 < ma50:
        return "BEAR"
    else:
        return "SIDEWAYS"


def calculate_gss(price, ma20, ema200, ma20_5d_ago, adx):
    """
    Gemini's Scoring System (Corrected Version)
    Returns: score (0-100)
    """
    # Convert all inputs to float to avoid Series comparison errors
    # Use .iloc[0] for Series, direct conversion for scalars
    price = price.iloc[0] if hasattr(price, 'iloc') else float(price)
    ma20 = ma20.iloc[0] if hasattr(ma20, 'iloc') else float(ma20)
    ema200 = ema200.iloc[0] if hasattr(ema200, 'iloc') else float(ema200)
    ma20_5d_ago = ma20_5d_ago.iloc[0] if hasattr(ma20_5d_ago, 'iloc') else float(ma20_5d_ago)
    adx = adx.iloc[0] if hasattr(adx, 'iloc') else float(adx)

    score = 0

    # Factor 1: 200EMA Anchor (20%)
    if price > ema200:
        score += 20

    # Factor 2: MA20 Slope (30%) - CORRECTED to 0.1%
    ma_slope_pct = ((ma20 - ma20_5d_ago) / ma20_5d_ago) * 100
    if ma_slope_pct > 0.1:
        score += 30

    # Factor 3: ADX Strength (30%)
    if adx > 25:
        score += 30
    elif adx < 20:
        score -= 10

    # Factor 4: Price Proximity (20%) - CORRECTED directional
    dist_pct = (price - ma20) / ma20 * 100  # No abs()
    if 0 < dist_pct <= 2:  # Must be ABOVE MA20
        score += 20

    return score


def map_score_to_regime(score):
    """Convert GSS score to regime label"""
    if score >= 70:
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
    end_date = "2025-12-31"

    nifty = yf.download("^NSEI", start=start_date, end=end_date, progress=False)

    if nifty.empty:
        print("❌ Failed to download Nifty data. Check internet connection.")
        return

    print(f"✅ Downloaded {len(nifty)} days of data\n")

    # Step 2: Calculate indicators
    print("🔧 Calculating indicators...")
    nifty['MA20'] = nifty['Close'].rolling(20).mean()
    nifty['MA50'] = nifty['Close'].rolling(50).mean()
    nifty['EMA200'] = nifty['Close'].ewm(span=200).mean()
    nifty['ADX'] = calculate_adx(nifty, period=14)
    print(f"📊 ADX Stats: Min={nifty['ADX'].min():.2f}, Max={nifty['ADX'].max():.2f}, Mean={nifty['ADX'].mean():.2f}")

    # Filter to validation period (Jan 2022 onwards) BEFORE dropna
    nifty = nifty[nifty.index >= '2022-01-01']

    # Calculate actual regime
    nifty['Actual_Regime'] = nifty.apply(calculate_actual_regime, axis=1)

    # Fill forward ADX NaN values from the initial rolling period
    nifty['ADX'] = nifty['ADX'].bfill()

    # Drop rows with any remaining NaN values
    nifty = nifty.dropna()


    print(f"✅ Indicators calculated for {len(nifty)} trading days\n")

    # Step 3: Calculate GSS predictions (using N-1 data)
    print("🤖 Running GSS predictions...")

    gss_scores = []
    gss_predictions = []

    for i in range(1, len(nifty)):
        # Use previous day's data (N-1)
        prev_idx = i - 1
        prev_row = nifty.iloc[prev_idx]

        # Get MA20 from 5 days before N-1 (i.e., index i-6)
        if i >= 6:
            ma20_5d_ago = nifty.iloc[i - 6]['MA20']
        else:
            ma20_5d_ago = prev_row['MA20']  # Fallback for early days

        # Calculate GSS score using N-1 data
        score = calculate_gss(
            price=prev_row['Close'],
            ma20=prev_row['MA20'],
            ema200=prev_row['EMA200'],
            ma20_5d_ago=ma20_5d_ago,
            adx=prev_row['ADX']
        )

        prediction = map_score_to_regime(score)

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

    print("─────────────────────────────────────────────────────────────────────────────\n")

    # Step 6: Show mismatches
    mismatches = nifty[~nifty['Match']].copy()

    if len(mismatches) > 0:
        print("❌ MISMATCH EXAMPLES (First 10):")
        print("─────────────────────────────────────────────────────────────────────────────")
        display_cols = ['Close', 'MA20', 'EMA200', 'ADX', 'GSS_Score', 'Actual_Regime', 'GSS_Prediction']
        print(mismatches[display_cols].head(10).to_string())
        print("\n")

    import os
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gss_results.csv")
    nifty.to_csv(output_file)
    print(f"💾 Results saved to: {output_file}\n")

    # Step 8: Decision
    print("═══════════════════════════════════════════════════════════════════════════════")
    if accuracy >= 90:
        print("✅ GSS VALIDATED! Accuracy >= 90% - Safe to use for playbook classification.")
    elif accuracy >= 80:
        print("⚠️  GSS ACCEPTABLE. Accuracy 80-90% - Review mismatches, may need tuning.")
    else:
        print("❌ GSS NEEDS IMPROVEMENT. Accuracy < 80% - Must adjust weights/thresholds.")
    print("═══════════════════════════════════════════════════════════════════════════════")


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    validate_gss()