# Handoff Note — 2026-06-05

## State
- h5_full.html p10 slider fixed (max 9→3 in 3 places)
- WFA replayed for 5 stocks — full results table available, matches prior findings
- Universal Optuna script written (h5_universal_optuna.py) but abandoned — regime problem makes 4-year universal set structurally unsound
- Regime analysis complete: ATR% and Vol_StdDev% are the two strongest separators between good and bad stock-years
- Regime filter WFA complete: filters work as year-level go/no-go gates, not day-level selectors
    - 3/5 worst years: zero valid days under both filters
    - NATIONALUM 2024: only survivor, PF barely crosses 1.0 (1.004)
- User is discussing all findings with Claude.ai — next action steps to come

## Key numbers to remember
- Baseline pooled PF (all 30 stocks, 4 years, no filters): 0.924
- Worst year separators: ATR14% < 2.25% and Vol_StdDev20% < 65%
- Best year avg ATR%: 2.78% | Worst year avg ATR%: 2.10%
- Best year avg Vol_StdDev%: 83.7% | Worst year avg Vol_StdDev%: 53.1%

## Next (pending Claude.ai discussion)
- Likely: define regime as a year-level or month-level gate using ATR% + Vol metrics
- Then: re-run Optuna only on regime-approved periods
- Or: signal redesign if regime filter alone can't solve the problem

## Files created this session
- Framework_V2/scripts/h5_universal_optuna.py — universal Optuna (abandoned but saved)
- Framework_V2/scripts/_temp_wfa_replay.py — WFA replay script
- Framework_V2/scripts/_temp_regime_analysis.py — regime metric comparison
- Framework_V2/scripts/_temp_regime_filter_wfa.py — regime filter WFA
- Framework_V2/outputs/h5/regime_filter_wfa_20260605_*.csv — results

## Known Issues
- tb9 signal CSVs don't exist — only tb3 available
- BAJFINANCE is the tightest stock (lowest signal density, hardest to satisfy per-stock floors)
- No VIX data available in dataset — external data needed if VIX correlation is explored
