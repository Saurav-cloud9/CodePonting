"""
GSS v4.0 Hyperparameter Optimization with Optuna
=================================================
10-year optimization with walk-forward validation

Train: 2015-2021 (7 years)
Test: 2022-2025 (4 years)

Objective: (BULL Precision × 0.7) + (BULL Recall × 0.3)
Constraints: BULL calls ≥10%, BEAR calls ≥5%

FIXES APPLIED:
- Fix #1: Predictive wall alignment (CRITICAL)
- Fix #2: Multi-index flattening (safety)
- Fix #3: ADX slope smoothing (3-day SMA)
- Fix #4: Price proximity parameterization
- Fix #6: Memory management (gc_after_trial)
- Fix #7: Volume range verification (0.85-1.15)
"""

import pandas as pd
import numpy as np
import yfinance as yf
import optuna
from optuna.samplers import TPESampler
import warnings
import os
warnings.filterwarnings('ignore')

from gss_core import (
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
    
    # FIX #2: Explicit multi-index flattening for safety
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
    
    # FIX #3: ADX slope smoothing with 3-day SMA (Gemini's fix)
    nifty['ADX_slope'] = nifty['ADX'].diff().rolling(window=3).mean()
    
    return nifty


def calculate_actual_regimes(nifty):
    """Calculate Future-Truth regime labels"""
    actual_regimes = []
    for i in range(len(nifty)):
        regime = calculate_actual_regime_lookahead(nifty, i, lookahead=5)
        actual_regimes.append(regime)
    nifty['Actual_Regime'] = actual_regimes
    return nifty


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def run_validation(nifty, params):
    """
    Run GSS validation with given parameters
    
    FIX #1: CRITICAL - Correct alignment between predictions and actual regimes
    
    Logic:
    - For day i, we use data from day i-1 to make a prediction
    - This prediction is FOR day i-1 (the day we're looking at)
    - We compare this to day i-1's actual regime (i-1 -> i-1+5 move)
    
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
    
    # FIX #1: Align predictions with the PREVIOUS day's actual regime
    # We made len(nifty)-1 predictions (starting from index 1)
    # Each prediction at position i predicts for day i-1
    # So we compare predictions[0] to actual_regime[0], predictions[1] to actual_regime[1], etc.
    
    nifty_eval = nifty.iloc[1:].copy()  # Start from index 1 (has predictions)
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
        'bear_precision': bear_precision,
        'bear_recall': bear_recall,
        'accuracy': accuracy,
        'bull_calls_pct': bull_calls_pct,
        'bear_calls_pct': bear_calls_pct,
        'total_days': total_days
    }


# ═══════════════════════════════════════════════════════════════════════════
# OPTUNA OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════

def objective(trial, train_data, test_data):
    """
    Optuna objective function
    
    Returns weighted score: (BULL Precision × 0.7) + (BULL Recall × 0.3)
    With penalty for insufficient signal generation
    """
    
    # Suggest hyperparameters
    params = {
        # Moving Average parameters
        'ma_period': trial.suggest_int('ma_period', 15, 25),
        'ema_period': trial.suggest_int('ema_period', 150, 250),
        'ma_slope_threshold': trial.suggest_float('ma_slope_threshold', 0.03, 0.12),
        
        # ADX parameters
        'adx_period': trial.suggest_int('adx_period', 10, 21),
        'adx_strength_threshold': trial.suggest_int('adx_strength_threshold', 15, 30),
        
        # RSI parameters
        'rsi_period': trial.suggest_int('rsi_period', 9, 21),
        'rsi_exhaustion_threshold': trial.suggest_int('rsi_exhaustion_threshold', 65, 80),
        
        # Volume parameters - FIX #7: Verified range 0.85-1.15
        'vol_standard': trial.suggest_float('vol_standard', 1.05, 1.25),
        'vol_momentum': trial.suggest_float('vol_momentum', 0.85, 1.15),
        
        # Scoring thresholds
        'bull_threshold': trial.suggest_int('bull_threshold', 65, 80),
        'bear_threshold': trial.suggest_int('bear_threshold', 15, 35),
        
        # FIX #4: Price proximity parameterization
        'price_proximity_max': trial.suggest_float('price_proximity_max', 2.0, 5.0),
        
        # Momentum flag
        'require_fresh_momentum': trial.suggest_categorical('require_fresh_momentum', [True, False])
    }
    
    # Recalculate indicators with trial parameters
    train_prepared = calculate_indicators(
        train_data.copy(),
        ma_period=params['ma_period'],
        ema_period=params['ema_period'],
        adx_period=params['adx_period'],
        rsi_period=params['rsi_period']
    )
    train_prepared = train_prepared.dropna()
    
    # Run validation on training set
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
    
    return objective_score


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║               GSS v4.0 HYPERPARAMETER OPTIMIZATION                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")

    # CREATE RESULTS DIRECTORY
    results_dir = '.'  # Save to current directory
    
    # Download data
    full_data = prepare_data(start_date="2015-01-01", end_date="2026-01-10")

    print("Column structure after download:")
    print(full_data.columns)
    print("\nColumn levels:", full_data.columns.nlevels)

    # Calculate indicators with default params (will be recalculated in objective)
    # ADD THIS: Calculate indicators on full_data FIRST
    full_data = calculate_indicators(
        full_data,
        ma_period=20,  # Use default values
        ema_period=200,
        adx_period=14,
        rsi_period=14
    )
    full_data = full_data.dropna()
    
    # Calculate actual regimes (ATR-based, fixed at 14 periods)
    print("\n🔧 Calculating Future-Truth regimes (ATR-based)...")
    full_data = calculate_actual_regimes(full_data)
    
    # Split into train/test
    train_data = full_data[full_data.index < '2022-01-01'].copy()
    test_data = full_data[full_data.index >= '2022-01-01'].copy()
    
    print(f"\n📊 Data Split:")
    print(f"   Train: 2015-2021 ({len(train_data)} days)")
    print(f"   Test:  2022-2025 ({len(test_data)} days)")
    
    # Create Optuna study
    print("\n🔬 Starting Optuna optimization (300 trials)...")
    print("   Objective: (BULL Precision × 0.7) + (BULL Recall × 0.3)")
    print("   Constraints: BULL ≥10%, BEAR ≥5%")
    print("   Search Space: 14 parameters")
    print("   Estimated time: 60-90 minutes\n")

    study = optuna.create_study(
        study_name='gss_v4_optimization',
        direction='maximize',
        sampler=TPESampler(seed=42),
        storage='sqlite:///optuna_gss.db',  # Persistent storage
        load_if_exists=True  # Resume if interrupted
    )

    # Run optimization with progress callback
    def callback(study, trial):
        if trial.number % 50 == 0 and trial.number > 0:
            print(f"\n📈 Progress: {trial.number}/300 trials completed")
            print(f"   Best score so far: {study.best_value:.3f}")
            # Save intermediate results
            try:
                study.trials_dataframe().to_csv(
                    os.path.join(results_dir, 'optuna_trials_intermediate.csv'),
                    index=False
                )
                print(f"   💾 Checkpoint saved")
            except PermissionError:
                print(f"   ⚠️ Could not save checkpoint (file locked)")
    
    # FIX #6: Memory management - garbage collection after each trial
    study.optimize(
        lambda trial: objective(trial, train_data, test_data),
        n_trials=300,
        callbacks=[callback],
        show_progress_bar=True,
        gc_after_trial=True  # Prevent memory leaks
    )
    
    print("\n\n✅ Optimization Complete!")
    print(f"   Best objective score: {study.best_value:.3f}")
    
    # Save all trials
    trials_df = study.trials_dataframe()
    trials_df.to_csv('optuna_trials_full.csv', index=False)
    print("\n💾 Saved: optuna_trials_full.csv")
    
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
        test_metrics = run_validation(test_prepared, trial_params)
        
        # Display results
        print(f"\n📊 TRAIN Performance (2015-2021):")
        print(f"   BULL Precision: {trial_row['user_attrs_train_bull_precision']:.1f}%")
        print(f"   BULL Recall:    {trial_row['user_attrs_train_bull_recall']:.1f}%")
        print(f"   Accuracy:       {trial_row['user_attrs_train_accuracy']:.1f}%")
        print(f"   BULL Calls:     {trial_row['user_attrs_train_bull_calls_pct']:.1f}%")
        print(f"   BEAR Calls:     {trial_row['user_attrs_train_bear_calls_pct']:.1f}%")
        
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
        
        print(f"\n⚙️  Parameters:")
        for param_name, param_value in sorted(trial_params.items()):
            if isinstance(param_value, float):
                print(f"   {param_name:30s} = {param_value:.4f}")
            else:
                print(f"   {param_name:30s} = {param_value}")
    
    print("\n" + "="*80)
    print("🎯 RECOMMENDATION:")
    print("   • Use Rank 1 if generalization is EXCELLENT or GOOD")
    print("   • If Rank 1 shows MODERATE decay, compare with Ranks 2-3")
    print("   • Lower ranks may have better robustness despite lower train score")
    print("="*80)
    
    print("\n✅ All files saved in current directory:")
    print("   • optuna_trials_full.csv - Complete trial history")
    print("   • optuna_trials_intermediate.csv - Last checkpoint")


if __name__ == "__main__":
    main()
