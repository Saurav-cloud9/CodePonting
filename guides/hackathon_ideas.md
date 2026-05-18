# Hackathon Ideas

> Side quests. Not on the critical path. Revisit when fv2 signal is stable.

---

## [2026-04-22] NSE Signal Dashboard

**Name:** NSE Signal Dashboard
**Stack:** Claude Code (backend) + Opus 4.7 (explanations) + Claude Design (visual layer)

### Core Loop
1. CC runs fv2 signal pipeline on 29 NSE stocks
2. Each stock screened through G1-G3 sequentially
3. Passing signals surface with PF, equity curve, drawdown
4. Opus 4.7 explains each gate verdict in plain English
5. User can ask follow-up questions via chat input

**Differentiator:** "Existing tools show WHAT. Claude shows WHY."
Conversational drill-down on any signal/gate — unique.

**Target user:** Systematic traders + curious non-quants who want transparent, explainable signal reasoning.

### Hackathon MVP
- Backtesting data only (2022–2025, 48 months)
- No live trading needed for demo

### Post-Hackathon
- Add paper/live trade results as fv2 matures
- Gate toggling (interactive, Phase 2)
- Full dashboard once H5 + Optuna complete

**Philosophy:** Not a showcase — a tool we'd actually use daily.
Hackathon = side quest. CodePonting = main quest.
