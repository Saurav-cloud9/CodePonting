# GSS Integration Attempts - Learnings

## What We Tried:
- v1.5: Adding GSS as stock-level entry filter
- Calculated GSS on 5-min data (wrong timeframe)
- Mixed regime detection with bounce detection

## What We Learned:
- Regime = Daily timeframe (market macro view)
- Bounce = 5-min timeframe (entry timing)
- NEVER mix timeframes in indicator calculations
- NumPy optimization techniques from Copilot
- Difference between observation vs prediction

## What We Keep:
- `calculate_actual_regime_lookahead()` - Ground truth labeling
- Optimization patterns for future use
- Understanding of playbook system design

## Next Steps:
- Use actual regime labeling (observation)
- Build playbooks on ground truth
- Test GSS predictions separately (v1.5 proper)