# Session Log — May 19–30, 2026

## Week of May 19–25

- **Codedex Python intermediate completed**: CSV/file I/O, HOF, list comprehensions, classes, unittest ch17–20 (assertions, exceptions, setUp/tearDown, dicts)
- **CLAUDE.md refactored**: 5 ref sections extracted → guides/ (transaction costs, sandbox plan, CC remote, hackathon, future skills); 607→450 lines; Obsidian wikilinks fixed
- **export_h5_signals.py**: ATR multipliers fixed (1.0/1.5→2.5/4.5); entry cutoff (≥14:40) + hard exit (15:00 @ open) implemented; exit_datetime column added; exit loop reordered (bar assign to top — fixed S062/S078 misclassification)
- **p04 NaN analysis**: 63/100 POWERGRID signals T0-1≤MA20 (expected, not a bug)
- **Framework_V2/notebooks/** created for exploratory .ipynb work
- **H5 Full spec received & built**: lightweight-charts, multi-stock/year, Optuna JSON panel; sidebar toggle, live stats, R/R metric
- **H5 Lite validated**: POWERGRID 2022 — 21 sig / 61.9% WR / 2.43 PF
- MCP Obsidian setup initiated (claude_desktop_config.json)
- CC source code explored → p5 note written

## Week of May 26–30

- **NumPy started**: ex7–9 (vectorization, unit conversion, 2D array ops, aggregations, shape)
- **H5 Full fixes (5)**: slider drag DOM teardown, IST timestamp offset, NaN gate parse (empty→0), chart alignment, autoSize/crosshair
- **Optuna objective**: PF × sqrt(min(N, N_target)/N_target); dynamic N_target = 10% signals; N_floor = N_target (prevents degenerate solutions)
- **5-stock dual CSV batch** (tb3/tb9): export_h5_signals_batch.py + h5_optuna_batch.py built; tb3 wins 3–2, PF 2.0–2.93, N ≈ 140–200
- **p11 lookahead bias** found & fixed (entry_close → entry_open); p12 dropped entirely; 3-file update (export/optuna/HTML)
- **30-stock Optuna**: 9/30 cleared PF≥1.3; ITC, NATIONALUM, PNB, HDFCBANK, POWERGRID pass both variants
- **WFA + cross-val**: regime problem confirmed — 2022/23 profitable, 2024/25 loss across all tested stocks/param combos
- **PNB manual WFA**: 2 combos tested across 4 years — no single combo holds; regime filter required before further Optuna work
- **MCP packages installed**: obsidian, rss-reader, youtube-transcript, datetime, remote; SSL cert issue (corp VPN TLS interception) resolved via --strict-ssl=false
- **Kite MCP**: expired OAuth token removed; --use-system-ca added to .mcp.json; kite_login.mjs auth flow working; user removed Kite from final config

## Key decisions this period
- tb3 chosen over tb9 for 30-stock scale (3–2 win, marginal but consistent)
- Regime filter is next blocker — NATIONALUM WFA pending, then raw bounce success rate per year
- p12 permanently dropped (lookahead — uses entry bar close data unavailable at entry time)
