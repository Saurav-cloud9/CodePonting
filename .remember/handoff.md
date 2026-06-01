# Handoff Note — 2026-06-01

## State
- HTML fully cleaned: p11 = entry_open_above, p12 removed
- PNB manual WFA complete: regime problem confirmed, no single combo holds all 4 years
- Cross-val JSONs exist for 2022/2023/2024/2025 for 5 stocks in outputs/h5/optuna/{year}/
- NATIONALUM WFA not yet done (train on 2023, PF 2.26 best year)
- Voice Bridge built and confirmed running:
    - voice_bridge.py → file watcher, run in CC terminal
    - voice_bridge_mcp.py → MCP server, launched by Claude Desktop automatically
    - claude_desktop_config.json updated with voice-bridge entry
    - CD shows MCP status: running ✅

## Next
1. NATIONALUM manual WFA — load 2023 signals, refine params manually, test on 2022/2024/2025
2. Voice Bridge end-to-end test — trigger write_instruction from CD, confirm CC picks it up
3. Regime filter — raw bounce success rate per year across 5 stocks

## Known Issues
- Regime problem confirmed: 2024/2025 break all param combos found on 2022/2023
- Regime filter needed before any further Optuna re-tuning makes sense
