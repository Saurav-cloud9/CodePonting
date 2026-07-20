# Handoff Note — 2026-07-21

## Current State
- 6BCE baseline + VWAP variant both confirmed dead (ZPF<1.0 all combos)
- All charts built: zpf_lines, consistency, spaghetti (ZPF+ZSh(D)), equity+drawdown for both variants
- Strategic pivot: pursue regime-adaptive online learning model (MemLabs video 2)
- MemLabs notebook ($5.50 on Patreon) — purchase attempted, card declined, retry tomorrow
- SL/TP terminology locked project-wide (was SL/TGT)

## Next Step (START HERE)
1. **Buy MemLabs notebook** — patreon.com/cw/MemLabs, $5.50, "How to make your Models adaptive to Regime Changes"
2. **Build regime-adaptive model for NSE** — adapt online learning (passive aggressive regressor) to MA rejection SHORT signal; use trade outcomes (win/loss) + regime features (ATR%, vol) as inputs
3. **Kite bot (market hours only)** — confirm EOD tick-based fix live; trace reconciliation gap with concrete example; build CSV archival

## Known Issues
- Kite bot EOD exit fix applied but not yet live-tested
- Reconciliation gap (48/270 bars mismatched) root cause unconfirmed
- Old baseline sweep scripts still use monthly Sharpe (not ZSh(D) compliant)
- Both baselines not yet copied to baseline_reserve/
