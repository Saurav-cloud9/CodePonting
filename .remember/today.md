# Session Log — 2026-07-19

## Key Work Done

### backtesting_rules_v2.md final alignment
- Confirmed full alignment with CC scripts
- Added LONG charge direction note: `stt = exit × 0.00025`, `stamp = entry × 0.000003`

### 6BCE SHORT strategy — full sweep and analysis
- Built sl_tgt_sweep_6bce_short.py: 90-combo sweep (SL 1.5-6.0 × TGT 2.0-6.0), Zerodha charges, DS3 30 stocks 2015-2025
- Best ZPF = 0.888 (SL=6.0/TGT=6.0) — all 90 combos below ZPF=1.0; strategy dead
- ZSh(D) negative all years for all combos
- Post-2022 structural decay confirmed

### Charts built (all in Backtesting Extended/6BCE/)
- chart_zpf_lines_6bce.py — ZPF vs TGT, 10 SL lines, plasma colormap (user: "one of the better graphs")
- chart_consistency_6bce.py — scatter + year-wise ZPF lines; cache save added
- chart_spaghetti_6bce.py — all 90 combos overlaid; smoothest (cyan) vs volatile (red dashed)
- chart_spaghetti_zshd_6bce.py — same format but Y-axis = ZSh(D) per year

### Cache system
- sweep_cache_6bce.npz: overall_grid (10×9) + yearly_grid (10×9×11) + yearly_zshd_grid (10×9×11)
- Downstream chart scripts load from cache — no re-run needed

### Key findings
- Smoothest ≠ best: SL=2.0/TGT=2.0 (std=0.06) is consistently bad (ZPF=0.714)
- Best ZPF = Best ZSh(D) = same combo (SL=6.0/TGT=6.0); ZSh(D) adds no new info here
- Best consistency (mean−std): SL=6.0/TGT=5.5; only 2020 had ZPF>1.0 across any combo
- Plan: delegate sweep/chart work to Grok CLI; CC focuses on cloud engine build

## Key Numbers
- 6BCE best ZPF: 0.888 (SL=6.0/TGT=6.0)
- 6BCE best consistency: SL=6.0/TGT=5.5, cs=0.8198
- All combos ZSh(D) negative (mean ≈ -1.5 best case)
