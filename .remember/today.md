# Session Log — 2026-06-05

## H5 slider fix
p10 max_tb_gap slider max changed 9→3 in h5_full.html (3 places: slider definition line 411, default state line 50, reset button line 441).

## WFA replay (5 stocks)
Replayed WFA using frozen 2022 Optuna params (tb3) against pre-computed signal CSVs for 2023/2024/2025. Results match earlier session findings. Key numbers:
- ITC 2022: PF 1.94 → 2023: 0.72 → 2024: 0.90 → 2025: 1.02
- POWERGRID 2022: PF 1.78 → 2023: 1.16 → 2024: 0.99 → 2025: 0.57
- NATIONALUM 2022: 1.44 → 2023: 1.41 → 2024: 0.83 → 2025: 1.04
- HDFCBANK 2022: 1.43 → 2023: 0.76 → 2024: 1.02 → 2025: 0.78
- PNB 2022: 1.49 → 2023: 1.07 → 2024: 1.32 → 2025: 0.82
tb9 results all zero — no tb9 signal CSVs exist.

## Universal Optuna attempt
Built h5_universal_optuna.py — single Optuna study across all 30 stocks × 4 years (182,517 signals). Three attempts:
1. Hard 5% per-stock floor + PF>1.0 → all -1e9 (BAJFINANCE bottleneck at 4.6%)
2. Soft coverage penalty (PF × stocks_ok/30) + PF>1.0 → still all -1e9 (baseline pooled PF = 0.924, below hard floor)
3. Soft coverage + no PF floor → score 0.842 found immediately, but abandoned because regime problem makes 4-year universal set meaningless
Script saved at Framework_V2/scripts/h5_universal_optuna.py for future reference.

## Regime analysis (best vs worst years)
Computed daily ATR%, MA50 slope, up-day%, volume, vol_StdDev% for 5 worst and 5 best stock-years.
Key finding: ATR% (normalized volatility) and Vol_StdDev% (volume consistency) are strongest separators.
- Best years: ATR% avg 2.78%, Vol_StdDev% avg 83.7%
- Worst years: ATR% avg 2.10%, Vol_StdDev% avg 53.1%
Conclusion: MA bounce needs minimum volatility + active/erratic volume to generate edge. Quiet markets kill it.

## Regime filter WFA
Applied two day-level filters to worst 5 stock-years (all signals, no Optuna params):
- Filter 1: ATR14% >= 2.25%
- Filter 2: Vol_StdDev20% >= 65%
Results: 3 of 5 worst years had ZERO valid days. ITC 2023 kept 10.2% but PF got worse. NATIONALUM 2024 kept 23.3%, PF 0.954→1.004 (marginal).
Key insight: filters work as year-level go/no-go gates, not day-level signal selectors.
CSV saved: Framework_V2/outputs/h5/regime_filter_wfa_20260605_*.csv

## Handed to Claude.ai for discussion
User is discussing findings with Claude.ai and will return with next action steps.
