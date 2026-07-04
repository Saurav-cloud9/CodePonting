# Session Log — 2026-07-04

## Key Work Done

### Baseline files restructured and cleaned
- Previous structure (ma_baseline_v*.py in core/) abandoned — too complex
- Rebuilt as two standalone scripts in scripts/trials/baseline_explorations/:
  - ma_bounce.py — LONG bare baseline (multi-bar bounce off MA20)
  - ma_rejection.py — SHORT bare baseline (mirror of ma_bounce, directional flip)
- Both cleaned: removed dead MA_COL variable, added bounds check + date guard, numpy added to rejection

### baseline_reserve/ locked
- ma_bounce.py in baseline_reserve/ confirmed clean: bounce_bar=None sentinel restored
- CLAUDE.md rule added: DO NOT TOUCH baseline_reserve/ unless explicitly asked by Saurav
- ma_bounce_edited.py deleted (redundant)

### Results confirmed
- LONG (ma_bounce): N=49,062, PF=0.922, Sharpe=-1.458 — 30 stocks, 2022-2025
- SHORT (ma_rejection): N=47,787, PF=1.079, Sharpe=1.455 — 27/30 stocks PF>1.0
- SHORT yearwise: 2022=1.131, 2023=1.035, 2024=1.094, 2025=1.053 — edge positive ALL 4 years
- NPF reality: PF=1.079 raw → NPF~0.7 after charges — not yet tradeable, but strong directional signal

### Next plan agreed
1. Lock both baseline files into baseline_reserve/
2. Analyse why SHORT beats LONG — structural factors, TV visualisation
3. Build SHORT v1 (wick-only mirror of ma_bounce v1) — properly this time
4. Equity curve, drawdown, NPF analysis on SHORT side

## Key Numbers
- LONG bare: PF=0.922, Sharpe=-1.458 (N=49,062)
- SHORT bare: PF=1.079, Sharpe=1.455 (N=47,787)
- SHORT top stock: TATAMOTORS PF=1.394, Sharpe=2.406
- SHORT weakest: SUNPHARMA PF=0.888
