# GSS v5.0 - ML-Enhanced Feature Selection Optimization

## 🆕 What's New in v5.0

### 1. **Feature Selection (10 Boolean Parameters)**
Optuna now decides which GSS features to enable/disable:
- Long-term Anchor (price > EMA200)
- MA Slope momentum
- ADX Strength
- ADX Acceleration
- RSI Equilibrium (>50)
- RSI Rising
- RSI Ignition (50 crossover)
- RSI Exhaustion penalty
- Price Proximity to MA
- Volume Confirmation

**Impact:** Reduces noise by eliminating low-value features. Discovers optimal feature subsets.

### 2. **ATR Multiplier Parameterization (1 Float Parameter)**
- **v4.0:** Fixed at 1.5 (hard-coded regime threshold)
- **v5.0:** Searchable from 1.0 to 3.0
- **Impact:** Adapts regime labeling sensitivity to market conditions

### 3. **Bull Threshold as Searchable Parameter (1 Integer Parameter)**
- **v4.0:** Fixed at 67
- **v5.0:** Searchable from 50 to 95 (step=5)
- **Impact:** Finds mathematically optimal cutoff point

### 4. **Expanded Search Space**
- **v4.0:** 14 parameters
- **v5.0:** 28 parameters (14 continuous + 10 boolean + 4 categorical)
- **Search Combinations:** ~10^15 (10 quadrillion+)

---

## 📊 Expected Outcomes

### Best Case Scenario
- **Feature Selection** removes 3-4 noisy features → +3-5% precision boost
- **ATR Multiplier** finds optimal value (e.g., 2.0 instead of 1.5) → +2-3% precision boost
- **Bull Threshold** finds sweet spot (e.g., 75 instead of 67) → +1-2% precision boost
- **Combined Effect:** 24% → 30-34% BULL precision

### Realistic Case
- **Feature Selection** marginally improves (~2-3%)
- **ATR/Threshold** stay close to v4.0 defaults
- **Combined Effect:** 24% → 26-28% BULL precision

### Worst Case
- All improvements cancel out
- v5.0 matches v4.0's 23.9% ceiling
- **Conclusion:** GSS architecture fundamentally limited, proceed to full ML

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Optimization (400 trials, ~20 hours)
```bash
python gss_hyperparameter_search_v5.py
```

### 3. Monitor Progress
- Checkpoint saved every 50 trials: `optuna_trials_v5_intermediate.csv`
- Progress printed to console
- Resume automatically if interrupted (uses SQLite persistence)

---

## 📁 Output Files

| File | Description |
|------|-------------|
| `optuna_gss_v5.db` | SQLite database with all trial data |
| `optuna_trials_v5_full.csv` | Complete trial history (400 rows) |
| `optuna_trials_v5_intermediate.csv` | Last checkpoint for recovery |

---

## 🔍 Analysis Questions After Completion

### 1. Feature Importance
- Which features were **disabled** in top trials?
- Does fewer features = better precision?
- Which single feature matters most?

### 2. ATR Multiplier
- Did optimal value differ from 1.5?
- If so, by how much? (e.g., 2.0 = 33% more lenient labeling)

### 3. Bull Threshold
- Did optimal value differ from 67?
- What's the precision vs. threshold curve?

### 4. Breakthrough Check
- Did v5.0 break v4.0's 23.9% ceiling?
- If yes, by how much? (Target: 35-45%)
- If no, confirm GSS exhausted → Pivot to full ML

---

## 📈 Comparison to v4.0

| Metric | v4.0 (Best Trial #364) | v5.0 (Target) |
|--------|------------------------|---------------|
| **Train BULL Precision** | 23.9% | 28-34% (hoped) |
| **Test BULL Precision** | 16.6% | 24-30% (hoped) |
| **Parameters Optimized** | 14 | 28 |
| **Feature Selection** | ❌ None | ✅ 10 features |
| **ATR Multiplier** | ❌ Fixed (1.5) | ✅ Searchable (1.0-3.0) |
| **Bull Threshold** | ❌ Fixed (67) | ✅ Searchable (50-95) |

---

## 🛠️ Code Structure

```
GSS_V5_Optimization/
├── gss_core_v5.py                    # Core GSS logic with feature flags
├── gss_hyperparameter_search_v5.py   # Main optimization script
├── README.md                          # This file
├── requirements.txt                   # Dependencies
├── optuna_gss_v5.db                  # Generated during run
├── optuna_trials_v5_full.csv         # Generated after completion
└── optuna_trials_v5_intermediate.csv # Generated every 50 trials
```

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Setup + Install | 5 min |
| Single Trial Runtime | 2-3 min |
| 400 Trials (Unattended) | 20-24 hours |
| Analysis of Results | 1-2 hours |
| **Total Active Work** | ~2-3 hours |

---

## 🎯 Next Steps After v5.0

### If v5.0 Breaks Through (30%+ precision):
1. Analyze which features were critical
2. Test on multiple stocks (extend beyond Nifty)
3. Paper trade for 4-8 weeks
4. Live pilot with ₹50K

### If v5.0 Matches v4.0 Ceiling (24-26%):
1. **Declare GSS exhausted** - single-indicator logic ceiling confirmed
2. Pivot to **full ML workflow** (HMM, K-Means, Random Forest)
3. Start Phase 1.1: ML learning (2-3 weeks)
4. Build clean ML architecture from scratch

---

## 📞 Support

If optimization fails or results look wrong:
- Check `optuna_trials_v5_intermediate.csv` for last valid checkpoint
- Review console output for error messages
- Verify all features enabled in at least 1 trial (sanity check)

---

## 🧪 Experimental Features

This is an **exhaustion test** to confirm whether GSS has a fundamental ceiling or if feature selection can unlock higher precision. Results will determine next phase strategy (refine vs. pivot).
