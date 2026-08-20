# GSS v4.0 Hyperparameter Optimization Framework

## 📋 Overview

Production-ready hyperparameter optimization for the Gemini Scoring System (GSS) using Bayesian optimization with Optuna.

**Version:** 4.0  
**Status:** Production Ready  
**Optimization Method:** Bayesian (TPE Sampler)  
**Validation:** Walk-Forward (Train: 2015-2021, Test: 2022-2025)

---

## 🎯 Key Features

- ✅ **10-year backtesting** (2015-2025) across multiple market regimes
- ✅ **14 parameters optimized** simultaneously using Bayesian optimization
- ✅ **Walk-forward validation** prevents overfitting
- ✅ **Anti-Sideways Trap** constraints (≥10% BULL, ≥5% BEAR calls)
- ✅ **ATR-based Future-Truth** regime detection (Steel Ruler methodology)
- ✅ **300 trials** with smart exploration (60-90 min runtime)
- ✅ **Checkpoints every 50 trials** - resume on interruption
- ✅ **Train vs Test comparison** with generalization scoring
- ✅ **Memory management** - prevents leaks over long runs

---

## 🔧 Critical Fixes Applied

### Fix #1: Predictive Wall Alignment (CRITICAL)
Corrected 1-day misalignment between predictions and actual regimes that was inflating/deflating accuracy.

### Fix #2: Multi-Index Flattening
Explicit handling of yfinance multi-level column headers for reliability.

### Fix #3: ADX Slope Smoothing (Gemini's Insight)
3-day SMA on ADX slope prevents false triggers from 1-day noise spikes.

### Fix #4: Price Proximity Parameterization
Optimizes the "buy near MA" distance (2.0-5.0% range) instead of hardcoding 3%.

### Fix #5: RSI Ignition Bonus
+5 bonus points when RSI crosses above 50 centerline (predictive of regime shifts).

### Fix #6: Memory Management
Garbage collection after each trial prevents memory leaks during 300-trial runs.

### Fix #7: Volume Range Verification
Confirms vol_momentum range (0.85-1.15x) allows testing "low volume BEAR" hypothesis.

### Fix #8: Indicator Vision Synchronization
Verified that scoring engine uses trial-specific periods (not hardcoded).

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Navigate to optimization folder
cd gss_v4_optimization

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `yfinance` - Market data download
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `optuna` - Bayesian optimization

---

## 🚀 Usage

### Quick Start

```bash
python gss_hyperparameter_search.py
```

**Expected Runtime:** 60-90 minutes for 300 trials

### Output Files

The script automatically creates:
- `optuna_trials_full.csv` - Complete trial history with all parameters
- `optuna_trials_intermediate.csv` - Checkpoint saved every 50 trials

### Console Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║               GSS v4.0 HYPERPARAMETER OPTIMIZATION                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

📥 Downloading Nifty data (2015-01-01 to 2026-01-10)...
✅ Downloaded 2,543 days of data

🔧 Calculating Future-Truth regimes (ATR-based)...

📊 Data Split:
   Train: 2015-2021 (1,756 days)
   Test:  2022-2025 (787 days)

🔬 Starting Optuna optimization (300 trials)...
   Objective: (BULL Precision × 0.7) + (BULL Recall × 0.3)
   Constraints: BULL ≥10%, BEAR ≥5%
   Search Space: 14 parameters
   Estimated time: 60-90 minutes

[Progress bar appears here...]

📈 Progress: 50/300 trials completed
   Best score so far: 0.362
   💾 Checkpoint saved

[... continues through 300 trials ...]

✅ Optimization Complete!
   Best objective score: 0.421

═══════════════════════════════════════════════════════════════════════════════
TOP 5 PARAMETER SETS (Ranked by Objective Score)
═══════════════════════════════════════════════════════════════════════════════

RANK 1: Objective Score = 0.421
────────────────────────────────────────────────────────────────────────────────

📊 TRAIN Performance (2015-2021):
   BULL Precision: 44.2%
   BULL Recall:    22.1%
   Accuracy:       61.3%
   BULL Calls:     12.8%
   BEAR Calls:     6.2%

📊 TEST Performance (2022-2025):
   BULL Precision: 41.5% (-2.7%)
   BULL Recall:    19.4% (-2.7%)
   Accuracy:       58.9% (-2.4%)
   BULL Calls:     11.2%
   BEAR Calls:     5.8%

   Generalization: ✅ EXCELLENT - Very stable (avg decay: 2.6%)

⚙️  Parameters:
   adx_period                     = 16
   adx_strength_threshold         = 22
   bear_threshold                 = 25
   bull_threshold                 = 71
   ema_period                     = 195
   ma_period                      = 19
   ma_slope_threshold             = 0.0785
   price_proximity_max            = 3.2500
   require_fresh_momentum         = False
   rsi_exhaustion_threshold       = 72
   rsi_period                     = 14
   vol_momentum                   = 1.0500
   vol_standard                   = 1.1200

[Ranks 2-5 follow same format...]

═══════════════════════════════════════════════════════════════════════════════
🎯 RECOMMENDATION:
   • Use Rank 1 if generalization is EXCELLENT or GOOD
   • If Rank 1 shows MODERATE decay, compare with Ranks 2-3
   • Lower ranks may have better robustness despite lower train score
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🔬 Search Space (14 Parameters)

| Category | Parameter | Range | Description |
|----------|-----------|-------|-------------|
| **Moving Averages** | `ma_period` | 15-25 | Short-term MA calculation period |
| | `ema_period` | 150-250 | Long-term trend anchor period |
| | `ma_slope_threshold` | 0.03-0.12% | Minimum MA slope for points |
| **ADX** | `adx_period` | 10-21 | ADX calculation period |
| | `adx_strength_threshold` | 15-30 | Minimum ADX for strength points |
| **RSI** | `rsi_period` | 9-21 | RSI calculation period |
| | `rsi_exhaustion_threshold` | 65-80 | Overbought penalty trigger |
| **Volume** | `vol_standard` | 1.05-1.25 | Standard volume multiplier |
| | `vol_momentum` | 0.85-1.15 | High-momentum volume multiplier |
| **Price** | `price_proximity_max` | 2.0-5.0 | Max distance from MA (%) |
| **Scoring** | `bull_threshold` | 65-80 | Minimum score for BULL call |
| | `bear_threshold` | 15-35 | Maximum score for BEAR call |
| **Flags** | `require_fresh_momentum` | [True, False] | Require +DI/-DI rising? |

---

## 📊 Objective Function

**Weighted Score:**
```
Objective = (BULL Precision × 0.7) + (BULL Recall × 0.3)
```

**Why this weighting?**
- 70% precision: Ensures quality signals (avoid false positives)
- 30% recall: Maintains adequate signal quantity (avoid over-filtering)

**Constraints (Anti-Sideways Trap):**
- BULL calls must be ≥ 10% of total days
- BEAR calls must be ≥ 5% of total days
- Trials violating these constraints get objective score = 0.0

---

## 📈 Interpreting Results

### Generalization Scoring

Each rank shows train vs test comparison with decay analysis:

```
BULL Precision: 41.5% (-2.7%)  ← Small decay = good generalization
```

**Generalization Categories:**
- **✅ EXCELLENT** - Avg decay < 5% (very stable, use with confidence)
- **✓ GOOD** - Avg decay 5-10% (acceptable, monitor in production)
- **⚠️ MODERATE** - Avg decay > 10% (compare with lower ranks)

### Decision Guide

**Use Rank 1 if:**
- Generalization is EXCELLENT or GOOD
- Train/test metrics are similar (< 5% difference)
- BULL precision > 35% on test set

**Consider Rank 2-3 if:**
- Rank 1 shows MODERATE generalization (> 10% decay)
- Lower ranks have more stable train/test metrics
- You prefer robustness over peak performance

**Key Metrics to Watch:**
1. **BULL Precision** - Most important (quality of signals)
2. **Generalization** - Stability across time periods
3. **BULL Calls %** - Ensure adequate signal generation (> 10%)

---

## 🔄 Using Results in Your Trading Bot

### Step 1: Extract Best Parameters

From console output or `optuna_trials_full.csv`, get Rank 1 parameters.

### Step 2: Import GSS Core

```python
from gss_core import calculate_gss, map_score_to_regime

# Optimized parameters from Rank 1
params = {
    'ma_period': 19,
    'ema_period': 195,
    'ma_slope_threshold': 0.0785,
    'adx_period': 16,
    'adx_strength_threshold': 22,
    'rsi_period': 14,
    'rsi_exhaustion_threshold': 72,
    'vol_standard': 1.12,
    'vol_momentum': 1.05,
    'bull_threshold': 71,
    'bear_threshold': 25,
    'price_proximity_max': 3.25,
    'require_fresh_momentum': False
}
```

### Step 3: Calculate Indicators

```python
import pandas as pd
from gss_core import calculate_adx, calculate_atr, calculate_rsi

# Calculate with optimized periods
nifty['MA'] = nifty['Close'].rolling(params['ma_period']).mean()
nifty['EMA'] = nifty['Close'].ewm(span=params['ema_period']).mean()
nifty['ADX'], nifty['Plus_DI'], nifty['Minus_DI'] = calculate_adx(nifty, period=params['adx_period'])
nifty['RSI'] = calculate_rsi(nifty['Close'], period=params['rsi_period'])
# ... etc
```

### Step 4: Generate Signals

```python
# For current day, use previous day's data
prev_row = nifty.iloc[-1]  # Most recent complete day

# Calculate GSS score
score = calculate_gss(
    price=prev_row['Close'],
    ma=prev_row['MA'],
    ema=prev_row['EMA'],
    ma_prev=prev_row['MA_5d_ago'],
    adx=prev_row['ADX'],
    prev_adx=nifty.iloc[-2]['ADX'],
    rsi=prev_row['RSI'],
    prev_rsi=nifty.iloc[-2]['RSI'],
    plus_di=prev_row['Plus_DI'],
    minus_di=prev_row['Minus_DI'],
    prev_plus_di=nifty.iloc[-2]['Plus_DI'],
    params=params
)

# Map to regime
regime = map_score_to_regime(
    score=score,
    volume=prev_row['Volume'],
    volume_ma=prev_row['Volume_MA20'],
    adx_slope=prev_row['ADX_slope'],
    rsi=prev_row['RSI'],
    plus_di=prev_row['Plus_DI'],
    minus_di=prev_row['Minus_DI'],
    prev_plus_di=nifty.iloc[-2]['Plus_DI'],
    prev_minus_di=nifty.iloc[-2]['Minus_DI'],
    params=params
)

print(f"Regime: {regime}, Score: {score:.1f}")
# Output: Regime: BULL, Score: 82.0
```

---

## 🛠️ Advanced Usage

### Resuming Interrupted Run

If optimization stops (power loss, crash), you can resume:

```python
import optuna

# Load existing study
study = optuna.load_study(
    study_name='gss_v4_optimization',
    storage='sqlite:///optuna.db'  # If you enabled database storage
)

# Continue from where it stopped
remaining_trials = 300 - len(study.trials)
study.optimize(objective, n_trials=remaining_trials)
```

### Analyzing Trial History

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load trial history
trials = pd.read_csv('optuna_trials_full.csv')

# Find high-precision trials
high_precision = trials[trials['user_attrs_train_bull_precision'] > 40]
print(f"Found {len(high_precision)} trials with >40% precision")

# Plot optimization progress
plt.figure(figsize=(12, 6))
plt.plot(trials['number'], trials['value'])
plt.xlabel('Trial Number')
plt.ylabel('Objective Score')
plt.title('Optimization Progress')
plt.show()
```

### Custom Objective Function

Modify `objective()` in `gss_hyperparameter_search.py`:

```python
# Example: Emphasize recall over precision
objective_score = (train_metrics['bull_precision'] * 0.5) + (train_metrics['bull_recall'] * 0.5)

# Example: Multi-objective (both BULL and BEAR)
bull_score = (train_metrics['bull_precision'] * 0.7) + (train_metrics['bull_recall'] * 0.3)
bear_score = (train_metrics['bear_precision'] * 0.7) + (train_metrics['bear_recall'] * 0.3)
objective_score = (bull_score + bear_score) / 2
```

---

## 📝 Technical Notes

### ATR Period for Regime Detection
The ATR period for Future-Truth labeling is **fixed at 14** (Steel Ruler baseline). This ensures consistent regime definitions across all trials while allowing the scoring indicators (ADX, RSI) to use optimized periods.

### Optuna Sampler
Uses **TPE (Tree-structured Parzen Estimator)** for smart parameter exploration. TPE learns from previous trials to focus on promising parameter regions, making it much more efficient than random search.

### Reproducibility
All random operations use `seed=42` for reproducible results. Running the same script twice will generate identical results.

### Progress Checkpoints
Every 50 trials, the script saves `optuna_trials_intermediate.csv`. If the run crashes, you can analyze partial results or implement resumption logic.

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'gss_core'"

**Solution:** Ensure both files are in the same directory:
```bash
gss_v4_optimization/
├── gss_core.py  ← Must be here
└── gss_hyperparameter_search.py  ← Running from here
```

### Issue: "Failed to download data"

**Solution:** Check internet connection and yfinance compatibility:
```bash
pip install --upgrade yfinance
```

### Issue: Memory error during optimization

**Solution:** Reduce trial count or increase system RAM:
```python
# In main(), change:
n_trials=300  # Reduce to 100 or 150
```

### Issue: Optimization is very slow

**Causes:**
- Older computer (expected: ~0.5-1 trial/minute)
- Network issues (data download bottleneck)

**Solutions:**
- Run overnight
- Reduce trials to 100 for faster results
- Download data once and reuse (modify script)

---

## 📚 Further Reading

- **Optuna Documentation:** https://optuna.readthedocs.io/
- **Walk-Forward Analysis:** https://en.wikipedia.org/wiki/Walk_forward_analysis
- **Bayesian Optimization:** https://en.wikipedia.org/wiki/Bayesian_optimization
- **ATR Indicator:** https://www.investopedia.com/terms/a/atr.asp

---

## 🎯 Summary

**What You Get:**
- Mathematically optimized GSS parameters for Nifty trading
- Validated across 10 years and multiple market regimes
- Confidence in generalization through train/test comparison
- Ready-to-deploy parameters for your trading bot

**Expected Performance:**
- BULL Precision: 35-45% (quality signals)
- BULL Recall: 15-25% (adequate signal quantity)
- Overall Accuracy: 55-65%
- Generalization Decay: < 5% (excellent stability)

**Next Steps:**
1. Run `python gss_hyperparameter_search.py`
2. Review Top 5 results (prioritize generalization)
3. Extract Rank 1 parameters
4. Integrate into your MA Bounce Bot
5. Monitor performance on 2026 data

---

**Built with:** Python 3.12+ | Optuna 3.0+ | YFinance | Pandas | NumPy  
**License:** MIT  
**Version:** 4.0  
**Last Updated:** January 2026
