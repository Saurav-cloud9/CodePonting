# Iteration Log — MA Rejection (SHORT) Baseline Explorations
**Universe:** 30 stocks · 2022–2025 · 5-min CSVs  
**Baseline params:** SL=2.5×ATR · TGT=4.5×ATR · MAX_TB_GAP=3

---

## Baseline — ma_30_bounce.py (LONG) & ma_30_rejection.py (SHORT)
**Date:** 2026-07-04  
**Change:** None — raw bare baseline, no filters

| Strategy | N      | PF    | Sharpe  | Net       |
|----------|--------|-------|---------|-----------|
| LONG     | 49,062 | 0.922 | -1.458  | -8,626.85 |
| SHORT    | 47,787 | 1.079 | +1.455  | +7,972.49 |

**Yearwise SHORT:**
| Year | N      | PF    | Sharpe |
|------|--------|-------|--------|
| 2022 | 11,595 | 1.131 | 2.254  |
| 2023 | 11,568 | 1.035 | 0.688  |
| 2024 | 12,015 | 1.094 | 1.677  |
| 2025 | 12,609 | 1.053 | 1.045  |

**Notes:** SHORT edge genuine — positive PF all 4 years, 27/30 stocks PF>1.0. NPF≈0.7, not yet tradeable.

---

## SL/TGT Sweep — Both Baselines
**Date:** 2026-07-07  
**Sweep:** SL ∈ [1.5, 2.0, 2.5, 3.0, 3.5] · TGT ∈ [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

*Results pending — sweep running.*

---

## v1 — ma_30_rejection_v1.py
*Pending.*
