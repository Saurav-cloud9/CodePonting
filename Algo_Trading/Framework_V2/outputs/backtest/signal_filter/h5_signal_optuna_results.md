# H5 Signal Filter — Optuna Combined IS/OOS Results
IS: 2022-2023 | OOS: 2024-2025 | 30 stocks pooled
Winners: W + EOD+ | Coverage floor: 15% of IS | Trials: 500 | Target OOS PF: > 1.01

## Baseline
| | N | PF |
|--|--|--|
| IS (2022-2023) | 91,994 | 0.9356 |
| OOS (2024-2025) | 90,523 | 0.9156 |

## Best Trial Result
| | IS | OOS |
|--|--|--|
| PF | 1.0099 | 0.9616 |
| N signals | 14,832 (16.1%) | 14,211 (15.7%) |
| Pass OOS > 1.01 | — | NO |

## Active Gates (best trial)
- p01 >= -1.3674
- p05 <= 0.2753
- p06 <= 41.2043
- p07 <= 3090910281391.9341 (effectively no filter — outlier threshold)

## Top 10 IS PF Trials
| Trial | IS PF |
|-------|-------|
| 464 | 1.0099 |
| 488 | 1.0084 |
| 490 | 1.0059 |
| 461 | 1.0057 |
| 499 | 1.0013 |
| 487 | 1.0000 |
| 210 | 0.9977 |
| 468 | 0.9974 |
| 466 | 0.9973 |
| 491 | 0.9963 |

**Verdict: Best Optuna combo achieves IS PF 1.0099 but OOS PF 0.9616 — fails. Signal quality filtering alone cannot produce generalizable edge. Raw MA20 bounce signal lacks baseline edge; filtering cannot create what isn't there.**
