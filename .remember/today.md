# Session Log — 2026-05-12

## What was done
- CCP performed — context loaded from previous handoff
- Explored _explore/cc-source: identified it as Claude Code CLI source (not Claude AI model)
- Discussed TSX/JSX/React concepts and how they relate to claude.ai artifacts and CC terminal UI
- Identified practical value of CC source for quant workflow: hooks, skills, tools, MCP design
- F1 (CC source exploration) promoted from parked to P5 in TODO.md
- Former F0 (Claude-in-Claude artifacts) renumbered F1, kept parked — discussed scope vs H5 Lite
- Discussed F1 architecture: self-contained JS detection vs Claude API explanation layer
- Continued line-by-line review of export_h5_signals.py — covered lines 34–46
- Root cause found: line 46 close vs low mismatch with p03 causing ~54 signals to fail p03=1
- Saurav fixed line 46 — CSV needs re-export

## Status at SS
- export_h5_signals.py fixed but CSV not re-exported
- Line review paused at line 46, resume from line 47
- Saurav on Codedex break
