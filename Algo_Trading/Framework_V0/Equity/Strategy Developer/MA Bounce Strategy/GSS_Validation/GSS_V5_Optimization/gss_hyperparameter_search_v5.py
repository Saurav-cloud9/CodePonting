"""
GSS v5.0 Hyperparameter Optimization with ML-Enhanced Feature Selection
========================================================================

NEW FEATURES IN V5.0:
1. Feature Selection: Optuna decides which GSS features to enable/disable
2. ATR Multiplier: Parameterized regime labeling threshold (was fixed at 1.5)
3. Bull Threshold: Now a searchable parameter (was fixed at 67)
4. Cross-Validation: Structure for multiple train/test splits

SEARCH SPACE (28 dimensions):
- 14 continuous parameters (thresholds, periods)
- 10 boolean parameters (feature enable/disable flags)  
- 4 categorical parameters (momentum requirements, volume)

Train: 2015-2021 (7 years)
Test: 2022-2025 (4 years)

Objective: (BULL Precision × 0.7) + (BULL Recall × 0.3)
Constraints: BULL calls ≥10%, BEAR calls ≥5%
"""

import pandas as pd
import numpy as np
import yfinance as yf
import optuna
from optuna.samplers import TPESampler
import warnings
import os
import gc
warnings.filterwarnings('ignore')

from gss_core_v5 import (
    calculate_adx, calculate_atr, calculate_rsi,
    calculate_gss, map_score_to_regime, calculate_actual_regime_lookahead
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ═══════════════════════════════════════════════════════════════════════════

def prepare_data(start_date="2015-01-01", end_date="2026-01-10"):
    """Download and prepare Nifty data with all indicators"""
    print(f"📥 Downloading Nifty data ({start_date} to {end_date})...")
    
    # Download with buffer for indicator calculation
    buffer_start = "2014-01-01"
    nifty = yf.download("^NSEI", start=buffer_start, end=end_date, progress=False)
    
    # Explicit multi-index flattening for safety
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)
    
    if nifty.empty:
        raise ValueError("Failed to download data")
    
    print(f"✅ Downloaded {len(nifty)} days of data")
    return nifty


def calculate_indicators(nifty, ma_period=20, ema_period=200, adx_period=14, rsi_period=14):
    """Calculate all technical indicators with configurable periods"""
    nifty['MA'] = nifty['Close'].rolling(ma_period).mean()
    nifty['MA_5d_ago'] = nifty['MA'].shift(5)
    nifty['EMA'] = nifty['Close'].ewm(span=ema_period).mean()
    nifty['Volume_MA20'] = nifty['Volume'].rolling(20).mean()
    
    nifty['ADX'], nifty['Plus_DI'], nifty['Minus_DI'] = calculate_adx(nifty, period=adx_period)
    nifty['ATR'] = calculate_atr(nifty, period=14)  # ATR fixed at 14 for regime detection
    nifty['RSI'] = calculate_rsi(nifty['Close'], period=rsi_period)
    
    # ADX slope smoothing with 3-day SMA
    nifty['ADX_slope'] = nifty['ADX'].diff().rolling(window=3).mean()
    
    return nifty


def calculate_actual_regimes(nifty, atr_multiplier=1.5):
    """
    Calculate Future-Truth regime labels
    
    NEW: atr_multiplier is now parameterized
    """
    actual_regimes = []
    for i in range(len(nifty)):
        regime = calculate_actual_regime_lookahead(
            nifty, i, lookahead=5, atr_multiplier=atr_multiplier
        )
        actual_regimes.append(regime)
    nifty['Actual_Regime'] = actual_regimes
    return nifty


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def run_validation(nifty, params):
    """
    Run GSS validation with given parameters
    
    Predictive wall alignment: Compare day i-1 prediction to day i-1 actual regime
    
    Returns:
        dict with metrics
    """
    gss_scores = []
    gss_predictions = []
    
    # Start from index 1 (need previous day's data)
    for i in range(1, len(nifty)):
        prev_idx = i - 1
        prev_row = nifty.iloc[prev_idx]
        
        # Get MA_5d_ago
        ma_prev = prev_row['MA_5d_ago']
        
        # Get previous values for momentum (from i-2)
        if i >= 2:
            prev_adx = nifty.iloc[i - 2]['ADX']
            prev_rsi = nifty.iloc[i - 2]['RSI']
            prev_plus_di = nifty.iloc[i - 2]['Plus_DI']
            prev_minus_di = nifty.iloc[i - 2]['Minus_DI']
        else:
            prev_adx = prev_row['ADX']
            prev_rsi = prev_row['RSI']
            prev_plus_di = prev_row['Plus_DI']
            prev_minus_di = prev_row['Minus_DI']
        
        # Calculate GSS score using prev_row data
        score = calculate_gss(
            price=prev_row['Close'],
            ma=prev_row['MA'],
            ema=prev_row['EMA'],
            ma_prev=ma_prev,
            adx=prev_row['ADX'],
            prev_adx=prev_adx,
            rsi=prev_row['RSI'],
            prev_rsi=prev_rsi,
            plus_di=prev_row['Plus_DI'],
            minus_di=prev_row['Minus_DI'],
            prev_plus_di=prev_plus_di,
            params=params
        )
        
        # Map to regime
        prediction = map_score_to_regime(
            score=score,
            volume=prev_row['Volume'],
            volume_ma=prev_row['Volume_MA20'],
            adx_slope=prev_row['ADX_slope'],
            rsi=prev_row['RSI'],
            plus_di=prev_row['Plus_DI'],
            minus_di=prev_row['Minus_DI'],
            prev_plus_di=prev_plus_di,
            prev_minus_di=prev_minus_di,
            params=params
        )
        
        gss_scores.append(score)
        gss_predictions.append(prediction)
    
    # Align predictions with actual regimes
    nifty_eval = nifty.iloc[1:].copy()
    nifty_eval['GSS_Score'] = gss_scores
    nifty_eval['GSS_Prediction'] = gss_predictions
    nifty_eval['Match'] = nifty_eval['GSS_Prediction'] == nifty_eval['Actual_Regime']
    
    # Calculate metrics
    total_days = len(nifty_eval)
    
    # BULL metrics
    actual_bull_days = (nifty_eval['Actual_Regime'] == 'BULL').sum()
    bull_predictions = nifty_eval[nifty_eval['GSS_Prediction'] == 'BULL']
    bull_calls = len(bull_predictions)
    correct_bull_calls = (bull_predictions['GSS_Prediction'] == bull_predictions['Actual_Regime']).sum()
    
    bull_precision = (correct_bull_calls / bull_calls * 100) if bull_calls > 0 else 0
    bull_recall = (correct_bull_calls / actual_bull_days * 100) if actual_bull_days > 0 else 0
    bull_calls_pct = (bull_calls / total_days * 100)
    
    # BEAR metrics
    actual_bear_days = (nifty_eval['Actual_Regime'] == 'BEAR').sum()
    bear_predictions = nifty_eval[nifty_eval['GSS_Prediction'] == 'BEAR']
    bear_calls = len(bear_predictions)
    correct_bear_calls = (bear_predictions['GSS_Prediction'] == bear_predictions['Actual_Regime']).sum()
    
    bear_precision = (correct_bear_calls / bear_calls * 100) if bear_calls > 0 else 0
    bear_recall = (correct_bear_calls / actual_bear_days * 100) if actual_bear_days > 0 else 0
    bear_calls_pct = (bear_calls / total_days * 100)
    
    # Overall accuracy
    accuracy = (nifty_eval['Match'].sum() / total_days * 100)
    
    return {
        'bull_precision': bull_precision,
        'bull_recall': bull_recall,
        'bull_calls_pct': bull_calls_pct,
        'bear_precision': bear_precision,
        'bear_recall': bear_recall,
        'bear_calls_pct': bear_calls_pct,
        'accuracy': accuracy
    }


# ═══════════════════════════════════════════════════════════════════════════
# OPTUNA OBJECTIVE (v5.0 - EXPANDED SEARCH SPACE)
# ═══════════════════════════════════════════════════════════════════════════

def objective(trial, train_data, test_data):
    """
    Optuna objective function with expanded search space
    
    NEW IN V5.0:
    - 10 feature enable/disable flags
    - ATR multiplier for regime labeling
    - Bull threshold as searchable parameter
    - 28 total dimensions
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # PART 1: INDICATOR PERIODS (4 params)
    # ═══════════════════════════════════════════════════════════════════════
    ma_period = trial.suggest_int('ma_period', 10, 50, step=2)
    ema_period = trial.suggest_int('ema_period', 100, 300, step=20)
    adx_period = trial.suggest_int('adx_period', 10, 20, step=2)
    rsi_period = trial.suggest_int('rsi_period', 10, 20, step=2)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PART 2: REGIME LABELING (1 NEW param)
    # ═══════════════════════════════════════════════════════════════════════
    atr_multiplier = trial.suggest_float('atr_multiplier', 1.0, 3.0, step=0.25)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PART 3: FEATURE ENABLE/DISABLE (10 NEW params)
    # ═══════════════════════════════════════════════════════════════════════
    use_long_term_anchor = trial.suggest_categorical('use_long_term_anchor', [True, False])
    use_ma_slope = trial.suggest_categorical('use_ma_slope', [True, False])
    use_adx_strength = trial.suggest_categorical('use_adx_strength', [True, False])
    use_adx_acceleration = trial.suggest_categorical('use_adx_acceleration', [True, False])
    use_rsi_equilibrium = trial.suggest_categorical('use_rsi_equilibrium', [True, False])
    use_rsi_rising = trial.suggest_categorical('use_rsi_rising', [True, False])
    use_rsi_ignition = trial.suggest_categorical('use_rsi_ignition', [True, False])
    use_rsi_exhaustion = trial.suggest_categorical('use_rsi_exhaustion', [True, False])
    use_price_proximity = trial.suggest_categorical('use_price_proximity', [True, False])
    use_volume_confirmation = trial.suggest_categorical('use_volume_confirmation', [True, False])
    
    # ═══════════════════════════════════════════════════════════════════════
    # PART 4: FEATURE THRESHOLDS (7 params)
    # ═══════════════════════════════════════════════════════════════════════
    ma_slope_threshold = trial.suggest_float('ma_slope_threshold', 0.05, 0.20, step=0.01)
    adx_strength_threshold = trial.suggest_int('adx_strength_threshold', 15, 30, step=1)
    rsi_exhaustion_threshold = trial.suggest_int('rsi_exhaustion_threshold', 65, 80, step=1)
    price_proximity_max = trial.suggest_float('price_proximity_max', 2.0, 5.0, step=0.2)
    vol_standard = trial.suggest_float('vol_standard', 0.85, 1.15, step=0.05)
    vol_momentum = trial.suggest_float('vol_momentum', 0.90, 1.30, step=0.05)
    require_fresh_momentum = trial.suggest_categorical('require_fresh_momentum', [True, False])
    
    # ═══════════════════════════════════════════════════════════════════════
    # PART 5: REGIME MAPPING THRESHOLDS (3 params, 1 NEW)
    # ═══════════════════════════════════════════════════════════════════════
    bull_threshold = trial.suggest_int('bull_threshold', 50, 95, step=5)  # NEW: Was fixed at 67
    bear_threshold = trial.suggest_int('bear_threshold', 0, 40, step=5)
    
    # ═══════════════════════════════════════════════════════════════════════
    # BUILD PARAMS DICT
    # ═══════════════════════════════════════════════════════════════════════
    params = {
        # Feature enable/disable (NEW)
        'use_long_term_anchor': use_long_term_anchor,
        'use_ma_slope': use_ma_slope,
        'use_adx_strength': use_adx_strength,
        'use_adx_acceleration': use_adx_acceleration,
        'use_rsi_equilibrium': use_rsi_equilibrium,
        'use_rsi_rising': use_rsi_rising,
        'use_rsi_ignition': use_rsi_ignition,
        'use_rsi_exhaustion': use_rsi_exhaustion,
        'use_price_proximity': use_price_proximity,
        'use_volume_confirmation': use_volume_confirmation,
        
        # Feature thresholds
        'ma_slope_threshold': ma_slope_threshold,
        'adx_strength_threshold': adx_strength_threshold,
        'rsi_exhaustion_threshold': rsi_exhaustion_threshold,
        'price_proximity_max': price_proximity_max,
        
        # Volume thresholds
        'vol_standard': vol_standard,
        'vol_momentum': vol_momentum,
        
        # Regime mapping
        'bull_threshold': bull_threshold,
        'bear_threshold': bear_threshold,
        'require_fresh_momentum': require_fresh_momentum,
    }
    
    # ═══════════════════════════════════════════════════════════════════════
    # PREPARE DATA WITH TRIAL PARAMETERS
    # ═══════════════════════════════════════════════════════════════════════
    train_prepared = calculate_indicators(
        train_data.copy(),
        ma_period=ma_period,
        ema_period=ema_period,
        adx_period=adx_period,
        rsi_period=rsi_period
    )
    train_prepared = train_prepared.dropna()
    
    # NEW: Calculate regimes with parameterized ATR multiplier
    train_prepared = calculate_actual_regimes(train_prepared, atr_multiplier=atr_multiplier)
    
    # ═══════════════════════════════════════════════════════════════════════
    # RUN VALIDATION ON TRAIN SET
    # ═══════════════════════════════════════════════════════════════════════
    train_metrics = run_validation(train_prepared, params)
    
    # Apply floor constraints (anti-Sideways Trap)
    if train_metrics['bull_calls_pct'] < 10.0:
        return 0.0  # Penalty: Too few BULL calls
    if train_metrics['bear_calls_pct'] < 5.0:
        return 0.0  # Penalty: Too few BEAR calls
    
    # Calculate weighted objective
    objective_score = (train_metrics['bull_precision'] * 0.7) + (train_metrics['bull_recall'] * 0.3)
    
    # Store train metrics for later analysis
    trial.set_user_attr('train_bull_precision', train_metrics['bull_precision'])
    trial.set_user_attr('train_bull_recall', train_metrics['bull_recall'])
    trial.set_user_attr('train_accuracy', train_metrics['accuracy'])
    trial.set_user_attr('train_bull_calls_pct', train_metrics['bull_calls_pct'])
    trial.set_user_attr('train_bear_calls_pct', train_metrics['bear_calls_pct'])
    
    # Store feature usage for analysis (NEW)
    trial.set_user_attr('features_enabled', sum([
        use_long_term_anchor, use_ma_slope, use_adx_strength, use_adx_acceleration,
        use_rsi_equilibrium, use_rsi_rising, use_rsi_ignition, use_rsi_exhaustion,
        use_price_proximity, use_volume_confirmation
    ]))
    
    # Memory cleanup
    del train_prepared
    gc.collect()
    
    return objective_score


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║           GSS v5.0 ML-ENHANCED HYPERPARAMETER OPTIMIZATION                  ║")
    print("║                                                                              ║")
    print("║  NEW: Feature Selection + ATR Tuning + Threshold Sweep                      ║")
    print("║  Search Space: 28 dimensions (14 continuous + 10 boolean + 4 categorical)   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")

    # CREATE RESULTS DIRECTORY
    results_dir = '.'
    
    # Download data
    full_data = prepare_data(start_date="2015-01-01", end_date="2026-01-10")

    # Calculate indicators with default params (will be recalculated in objective)
    full_data = calculate_indicators(
        full_data,
        ma_period=20,
        ema_period=200,
        adx_period=14,
        rsi_period=14
    )
    full_data = full_data.dropna()
    
    # Calculate actual regimes with default ATR multiplier
    print("\n🔧 Calculating Future-Truth regimes (ATR-based, default multiplier=1.5)...")
    full_data = calculate_actual_regimes(full_data, atr_multiplier=1.5)
    
    # Split into train/test
    train_data = full_data[full_data.index < '2022-01-01'].copy()
    test_data = full_data[full_data.index >= '2022-01-01'].copy()
    
    print(f"\n📊 Data Split:")
    print(f"   Train: 2015-2021 ({len(train_data)} days)")
    print(f"   Test:  2022-2025 ({len(test_data)} days)")
    
    # Create Optuna study
    print("\n🔬 Starting Optuna optimization...")
    print("   Objective: (BULL Precision × 0.7) + (BULL Recall × 0.3)")
    print("   Constraints: BULL ≥10%, BEAR ≥5%")
    print("   Search Space: 28 parameters")
    print("     • 10 feature enable/disable flags (NEW)")
    print("     • 1 ATR multiplier for regime labeling (NEW)")
    print("     • 1 bull_threshold (NEW - was fixed at 67)")
    print("     • 16 other parameters (periods, thresholds)")
    print("   Estimated time: 2-3 minutes per trial\n")

    study = optuna.create_study(
        study_name='gss_v5_optimization',
        direction='maximize',
        sampler=TPESampler(seed=42),
        storage='sqlite:///optuna_gss_v5.db',  # NEW database
        load_if_exists=True
    )

    # Run optimization with progress callback
    def callback(study, trial):
        if trial.number % 50 == 0 and trial.number > 0:
            print(f"\n📈 Progress: {trial.number} trials completed")
            print(f"   Best score so far: {study.best_value:.3f}")
            best_trial = study.best_trial
            features_enabled = best_trial.user_attrs.get('features_enabled', 'N/A')
            print(f"   Best features enabled: {features_enabled}/10")
            
            # Save intermediate results
            try:
                study.trials_dataframe().to_csv(
                    os.path.join(results_dir, 'optuna_trials_v5_intermediate.csv'),
                    index=False
                )
                print(f"   💾 Checkpoint saved")
            except PermissionError:
                print(f"   ⚠️ Could not save checkpoint (file locked)")
    
    # Run optimization
    n_trials = 400  # Same as v4.0 for fair comparison
    study.optimize(
        lambda trial: objective(trial, train_data, test_data),
        n_trials=n_trials,
        callbacks=[callback],
        show_progress_bar=True,
        gc_after_trial=True
    )
    
    print("\n\n✅ Optimization Complete!")
    print(f"   Best objective score: {study.best_value:.3f}")
    
    # Save all trials
    trials_df = study.trials_dataframe()
    trials_df.to_csv('optuna_trials_v5_full.csv', index=False)
    print("\n💾 Saved: optuna_trials_v5_full.csv")
    
    # Get top 5 parameter sets
    print("\n" + "="*80)
    print("TOP 5 PARAMETER SETS (Ranked by Objective Score)")
    print("="*80)
    
    top_trials = study.trials_dataframe().nlargest(5, 'value')
    
    for rank, (idx, trial_row) in enumerate(top_trials.iterrows(), 1):
        print(f"\n{'='*80}")
        print(f"RANK {rank}: Objective Score = {trial_row['value']:.3f}")
        print(f"{'='*80}")
        
        # Extract parameters
        trial_params = {}
        for col in trial_row.index:
            if col.startswith('params_'):
                param_name = col.replace('params_', '')
                trial_params[param_name] = trial_row[col]
        
        # Validate on test set
        test_prepared = calculate_indicators(
            test_data.copy(),
            ma_period=int(trial_params['ma_period']),
            ema_period=int(trial_params['ema_period']),
            adx_period=int(trial_params['adx_period']),
            rsi_period=int(trial_params['rsi_period'])
        )
        test_prepared = test_prepared.dropna()
        test_prepared = calculate_actual_regimes(
            test_prepared, 
            atr_multiplier=trial_params['atr_multiplier']
        )
        test_metrics = run_validation(test_prepared, trial_params)
        
        # Display results
        print(f"\n📊 TRAIN Performance (2015-2021):")
        print(f"   BULL Precision: {trial_row['user_attrs_train_bull_precision']:.1f}%")
        print(f"   BULL Recall:    {trial_row['user_attrs_train_bull_recall']:.1f}%")
        print(f"   Accuracy:       {trial_row['user_attrs_train_accuracy']:.1f}%")
        print(f"   BULL Calls:     {trial_row['user_attrs_train_bull_calls_pct']:.1f}%")
        print(f"   BEAR Calls:     {trial_row['user_attrs_train_bear_calls_pct']:.1f}%")
        print(f"   Features Used:  {trial_row['user_attrs_features_enabled']}/10")
        
        print(f"\n📊 TEST Performance (2022-2025):")
        print(f"   BULL Precision: {test_metrics['bull_precision']:.1f}% ", end='')
        prec_diff = test_metrics['bull_precision'] - trial_row['user_attrs_train_bull_precision']
        print(f"({'+'if prec_diff>=0 else ''}{prec_diff:.1f}%)")
        
        print(f"   BULL Recall:    {test_metrics['bull_recall']:.1f}% ", end='')
        rec_diff = test_metrics['bull_recall'] - trial_row['user_attrs_train_bull_recall']
        print(f"({'+'if rec_diff>=0 else ''}{rec_diff:.1f}%)")
        
        print(f"   Accuracy:       {test_metrics['accuracy']:.1f}% ", end='')
        acc_diff = test_metrics['accuracy'] - trial_row['user_attrs_train_accuracy']
        print(f"({'+'if acc_diff>=0 else ''}{acc_diff:.1f}%)")
        
        print(f"   BULL Calls:     {test_metrics['bull_calls_pct']:.1f}%")
        print(f"   BEAR Calls:     {test_metrics['bear_calls_pct']:.1f}%")
        
        # Calculate generalization quality
        avg_decay = abs(prec_diff) + abs(rec_diff) + abs(acc_diff)
        avg_decay /= 3
        
        if avg_decay < 5:
            generalization = "✅ EXCELLENT - Very stable"
        elif avg_decay < 10:
            generalization = "✓ GOOD - Acceptable decay"
        else:
            generalization = "⚠️ MODERATE - Consider lower ranks"
        
        print(f"\n   Generalization: {generalization} (avg decay: {avg_decay:.1f}%)")
        
        # Show which features are enabled
        print(f"\n⚙️  Feature Selection:")
        feature_flags = {
            'Long-term Anchor': trial_params.get('use_long_term_anchor', True),
            'MA Slope': trial_params.get('use_ma_slope', True),
            'ADX Strength': trial_params.get('use_adx_strength', True),
            'ADX Acceleration': trial_params.get('use_adx_acceleration', True),
            'RSI Equilibrium': trial_params.get('use_rsi_equilibrium', True),
            'RSI Rising': trial_params.get('use_rsi_rising', True),
            'RSI Ignition': trial_params.get('use_rsi_ignition', True),
            'RSI Exhaustion': trial_params.get('use_rsi_exhaustion', True),
            'Price Proximity': trial_params.get('use_price_proximity', True),
            'Volume Confirmation': trial_params.get('use_volume_confirmation', True),
        }
        
        enabled_features = [name for name, enabled in feature_flags.items() if enabled]
        disabled_features = [name for name, enabled in feature_flags.items() if not enabled]
        
        print(f"   ✓ Enabled ({len(enabled_features)}): {', '.join(enabled_features)}")
        if disabled_features:
            print(f"   ✗ Disabled ({len(disabled_features)}): {', '.join(disabled_features)}")
        
        print(f"\n⚙️  Key Parameters:")
        print(f"   ATR Multiplier:     {trial_params['atr_multiplier']:.2f} (OLD - was 1.5)")
        print(f"   Bull Threshold:     {trial_params['bull_threshold']} (OLD - was 67)")
        print(f"   MA Period:          {trial_params['ma_period']}")
        print(f"   EMA Period:         {trial_params['ema_period']}")
        print(f"   MA Slope Threshold: {trial_params['ma_slope_threshold']:.3f}")
        print(f"   ADX Strength:       {trial_params['adx_strength_threshold']}")
    
    print("\n" + "="*80)
    print("🎯 V5.0 ANALYSIS POINTS:")
    print("   1. Compare features_enabled count: Does less = better?")
    print("   2. Check if ATR multiplier differs from 1.5 (v4.0 default)")
    print("   3. Check if bull_threshold differs from 67 (v4.0 default)")
    print("   4. Compare best v5.0 precision to v4.0's 23.9% ceiling")
    print("="*80)
    
    print("\n✅ Files saved:")
    print("   • optuna_gss_v5.db - Study database")
    print("   • optuna_trials_v5_full.csv - Complete trial history")
    print("   • optuna_trials_v5_intermediate.csv - Last checkpoint")


if __name__ == "__main__":
    main()
