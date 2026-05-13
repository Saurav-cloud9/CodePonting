# Session Log — 2026-05-13

## What was done
- CCP performed — context loaded
- Discussed CC source code: TSX/JSX/React concepts, practical value for quant workflow
- F1 (CC source exploration) promoted to P5 in TODO.md
- F0 (Claude-in-Claude) renumbered F1, kept parked — architecture discussed
- Continued line-by-line review of export_h5_signals.py (lines 34–46)
- Discussed pandas/numpy as data stack, vectorized operations, rolling windows across days
- bounce_bar_index distribution analysed: 14/100 signals have gap > 3, WR identical above/below
- max_tb_gap added as p10 (G2, ceiling), G3a→p11, G3b→p12
- export_h5_signals.py, fv2_params.md, TODO.md glossary all updated
- CSV column name trailing spaces fixed — str.strip() on load
- CSV re-exported: 100 signals, p10-p12 present, p03=0 for 65/100 (expected after T0 fix)
- claude.ai H5 Lite updated to match — both ends in sync

## Key decisions
- max_tb_gap = p10, ceiling threshold, range 0–9, default 9 (most permissive)
- Optuna to determine optimal ceiling — POWERGRID 2022 alone insufficient to hardcode
- Line 46 fix confirmed: 65/100 signals now have p03=0 vs 54 before
