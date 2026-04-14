## Gap Naming Convention

Gap 2 (Pullback Quality) and Gap 3 (Touch Precision) are formally combined for H4 development.
Reason: both fix the same root problem — "price must approach MA20 from above."
Gap 3 (candles_above) = Dimension 1 of H4 heatmap
Gap 2 (pullback_bars)  = Dimension 2 of H4 heatmap

HTML build order (observation phase, not execution order):
H3 = Gap 1 (Slope) ✅ done
H4 = Gap 2+3 combined
H5 = Gap 4 (Volume Signature)
H6 = Gap 5 (Follow-Through)
H7 = Master combined view
Optuna decides production execution order post-H7.

---

## Gap 1 — Slope Offset + Threshold
Date: 2026-03-29
Scoring: PF_test × log(signals) × stability_factor
Min PF filter: 1.0 (fallback 0.96) — Primary mode — all combos pass PF_test ≥ 1.0

### Top 10 Combos
| Rank | Offset | Threshold | PF_train | PF_test | Signals | ΔPF | Stable | Score |
|------|--------|-----------|----------|---------|---------|-----|--------|-------|
| 1 | T-2 | 0.12% | 0.940 | 1.026 | 5,101 | +0.087 | Unstable | 1.182 |
| 2 | T-3 | 0.15% | 0.911 | 1.005 | 3,755 | +0.094 | Unstable | 0.496 |
| 3 | T-2 | 0.15% | 0.904 | 1.002 | 3,518 | +0.098 | Unstable | 0.139 |
| 4 | T-3 | 0.14% | 0.912 | 1.019 | 4,207 | +0.106 | Unstable | 0.000 |
| 5 | T-2 | 0.13% | 0.924 | 1.037 | 4,500 | +0.113 | Unstable | 0.000 |
| 6 | T-2 | 0.14% | 0.906 | 1.034 | 3,959 | +0.128 | Unstable | 0.000 |
| 7 | T-1 | 0.11% | 0.920 | 1.021 | 5,384 | +0.101 | Unstable | 0.000 |
| 8 | T-1 | 0.12% | 0.894 | 1.031 | 4,669 | +0.137 | Unstable | 0.000 |
| 9 | T-1 | 0.13% | 0.858 | 1.027 | 4,049 | +0.168 | Unstable | 0.000 |
| 10 | T-1 | 0.14% | 0.856 | 1.047 | 3,568 | +0.192 | Unstable | 0.000 |

### Cluster Check
No strong cluster detected — results scattered across offsets/thresholds.

### Key Observations
- Best combo: Offset T-2, Threshold 0.12% (PF_test 1.026, N=5,101)
- Train vs Test regime note: test period (2024–2025) shows cleaner trending conditions vs 2022–2023 chop
- Gap 1 alone: PF > 1.0 requires high threshold → low signals
- Parameters NOT locked — awaiting Gaps 2–5 + joint Optuna

### Closest to Stable + Profitable
| Rank | Offset | Threshold | PF_train | PF_test | Signals | ΔPF   | Stable   | Score |
|------|--------|-----------|----------|---------|---------|-------|----------|-------|
| 1    | T-4    | 0.11%     | 0.993    | 0.993   | 6,232   | 0.000 | Stable   | — (both < 1.0) |
| 2    | T-5    | 0.08%     | 1.009    | 0.982   | 8,967   | -0.027| Marginal | — (test < 1.0) |
| 3    | T-2    | 0.15%     | 0.904    | 1.002   | 3,518   | +0.098| Unstable | — (ΔPF > 0.05) |

### Structural Conclusion
Zero combos satisfy BOTH PF_test >= 1.0 AND |ΔPF| < 0.05.
Gap 1 alone = regime selector, not a stable edge.
Gaps 2-5 required before slope threshold becomes reliable.

### Next Step
H4 — Gap 2: Pullback quality (depth + structure)
