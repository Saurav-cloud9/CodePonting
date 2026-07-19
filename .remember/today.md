# Session Log — 2026-07-18

## Key Work Done

### backtesting_rules_v2.md reviewed and aligned
- Confirmed full alignment with CC scripts on: EOD logic, ATR14, entry rules, position guard, 90-combo grid
- Zerodha charges replace NPF/Kotak (Kotak archived correctly in the file)
- ZPF / ZSh(D) are new primary metrics replacing raw PF + monthly Sharpe
- Added LONG direction note to charge formula: `stt = exit × 0.00025`, `stamp = entry × 0.000003`

### Two P1 script fixes identified
1. Sharpe → daily: all CC scripts use monthly resample (×√12); new standard is daily (×√252)
2. Entry bar hour check: add `if hour[i+1] >= 15: skip`; currently 14:55 signals enter and zero-PNL exit

### Priority reset
- Cloud backtesting engine (Oracle primary, AWS fallback) is the major build target
- P4 covers ongoing signal exploration: VWAP, RSI, MACD, Beluga + metrics (drawdown, equity curve, AUC/ROC)
- Old stale TODO items removed; glossary updated with ZPF/ZSh(D)

## Key Numbers (from prior session, locked)
- SHORT baseline: SL=1.5/TGT=4.0 → PF=1.116, Sharpe=2.275, N=172,360
- SHORT v1: SL=2.0/TGT=4.5 → PF=1.135, Sharpe=2.358, N=110,641
- LONG: dead across all 90 combos at both variants (PF<1.0)
