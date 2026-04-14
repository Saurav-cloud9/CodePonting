# PROGRESS.md — CodePonting fv1 Sandbox
# One line per completed step. Status only. No lengthy details.
# Update: add new line at bottom when a step completes.
# ─────────────────────────────────────────────────────────────

Step 1    ✅  fv1 code review — 13 verdicts documented in fv1_pending_changes.md
Step 2    ✅  Sandbox blockers implemented (Changes 1–6)
Step 3.1  ✅  16-combo brute-force feature sweep
Step 3.2  ✅  SL variant Optuna — winner: SL=A, PG+CP+AF, CAGR=-2.15% (DS3)
Step 3.3  ✅  Slippage + charges merged — baseline: -8.62% raw CAGR
Step 4.1  ✅  Regime filter Optuna 2022–2025 — overfit (PF9+TF4, zero trades 2015–2020)
Step 4.2  ✅  Regime filter Optuna 2015–2025 — exhausted, no viable regime signal found
Step 4.3  ✅  BQS export: 9 R1 metrics on 28,085 trades; bqs_trades.parquet generated
Step 4.3a ✅  BQS R1 M1–M6/M8 validated w1/w2/w3 on DS3 2022–2025; M5/M6 best signals
Step 4.3b ✅  BQS R2 M1–M10 validated (10 new metrics); no star bucket found
           ✅  BQS_DECISIONS.md created — charge formulas, w1/w2/w3 definitions documented
           ✅  Full R1+R2 leaderboard: 19 metrics tested, no standalone filter found; need combos
Step 4.4a ✅  Signal foundation sanity check — MA20 bounce edge confirmed via forward return analysis
           ✅  V2 (vol filter) shows strong edge (t-stat 13–22, p=0.0000 all N); V1 (pure touch) is noise
           ✅  Volume filter is critical; higher threshold improves edge but cuts trades — BQS is the right path
Step 4.4b ✅  DT/RF on combined R1+R2 metrics; parquet rebuilt (w2/w3, 11 R2 cols, 38 total)
           ✅  DT leaf analysis: w1 best bucket +5.7pp (9,735 trades), w2 +9.1pp (1,795), w3 +5.5pp (1,540)
Step 4.4b ✅  DT/RF 19 BQS metrics — no star bucket, F4 best +0.62% raw
           ✅  Charges confirmed as killer — 3.4× raw profit, fv1 closed
Step 4.4c ✅  9-filter CAGR replay: F4 best (+0.62% CAGR raw, -Rs62k after Upstox charges)
Step 4.4  ✅  COMPLETE. DT/RF on 19 BQS metrics done. F4 best filter but loses after charges.
           ✅  fv1 signal confirmed insufficient. fv2 direction: fix raw signal foundation first.
Step 5    ✅  Skipped — fv1 closed before full DS3 backtest warranted

── DATA & INFRA ──────────────────────────────────────────────
DS3 migration  ✅  All 13 sandbox scripts migrated to intraday_5min_DS3
Daily data     ✅  Built from DS3 5-min resample (2015–2025) + yfinance warmup for 28/29 stocks
CLAUDE.md      ✅  Updated with full master plan, baselines, sandbox config, clarification protocol
CLAUDE.md      ✅  Added PROGRESS/TODO protocol + context file links

── FRAMEWORK V2 ──────────────────────────────────────────────
Step 1    ✅  Direction locked: 5 structural signal gaps → fv2 signal redesign
Step 2    ✅  fv2 scaffold in place

Step 3      — Data Build
Step 3.1  ✅  TATAMOTORS_5min.csv: outcome columns added (signal_type / exit_reason / raw_pnl / win)
Step 3.2  ✅  All 30 stock CSVs generated (29 DS3 + BAJFINANCE via Kite MCP); 43,902 + 1,538 signals
           ✅  fv2 universe locked: 30 stocks (DS3 - VI + BAJFINANCE)
Step 3.3  ✅  vol_ma20 added to all 30 CSVs; DS3 warmup for 29 stocks; BAJFINANCE via 2021 chunks
Step 3.4  ✅  CLAUDE.md + README.md + codeponting_structure.md updated; charge formula corrected

Step 4      — Visualisation Build
Step 4.1  ✅  fv2_h1_signal_viewer built — signal viewer + Gap 1 toggle (TATAMOTORS 5min)
           ✅  fv2_h2_calculator built — calculator, delta bar, slope breakdown
Step 4.2  ✅  Claude.ai project created; CCP context loaded; fv2_h2_calculator Panel A→B insight confirmed
Step 4.3  ✅  fv2_h2_calculator expanded: 30-stock dropdown + All Stocks aggregate mode (45,440 signals)
Step 4.4  ✅  fv2_h1_signal_viewer rebuilt for 30 stocks; build_html1.py created; bounce+2 logic locked (88 MB)
Step 4.5  ✅  fv2_h1_signal_viewer P1+P2: sidebar stats (WR/PF/AvgPnL) + click-to-inspect with SL/TGT overlay
           ✅  MA20 display precision fixed (1dp→2dp); Vol Ratio tooltip added (orange >=1.2x)
           ✅  OHLC precision fixed (1dp→2dp); default opens on earliest date; dual border for touch+bounce candle (blue outer, orange inner)
Step 4.6  ✅  VS Code watcherExclude fix applied; SSD trigger designed (GCP setup parked)
Step 4.7  ✅  fv2_h3_slope_tuner built — dual heatmap, sliders, per-stock table, export button
Step 4.8  ✅  fv2_h3_chart built — Top 10 Combos Navigator, ◀/▶ nav, cluster check, chart dots
           ✅  fv2_h3_chart view live; Top 10 navigator spec locked + implemented

Step 5      — Gap 1 Analysis
Step 5.1  ✅  Gap 1 result (TATAMOTORS): CAGR -172% → -2.07% | PF 0.77 → 0.95 | Max DD -169% → -17.88%
Step 5.2  ✅  30-stock universe confirmed; Gap 1 holds universally; PF 0.95 across all stocks
Step 5.3  ✅  fv2_h3_slope_tuner heatmap: best combo T-3 0.07–0.08%; no single combo clearly dominant
           ✅  fv2_h3_chart scoring upgraded: stability_factor + PF>=1.0 gate + 0.96 fallback
Step 5.4  ✅  gap_1_observations.md saved; conclusion: zero combos stable+profitable; Gap 1 alone insufficient

Step 6      — Gap 2+3 Analysis
Step 6.1  ✅  Gap 2+3 root cause confirmed via fv2_h1_signal_viewer: touch dependent on bounce window = foundational flaw
           ✅  Gap 2+3 overlap confirmed — both fix "approached from above"; Gap 2+3 > Gap 1 in impact
Step 6.2  ✅  Gap 2 visual intuition built via Opus + fv2_h1_signal_viewer: good pullback = orderly 3–8 bars, fading vol, shallow depth
Step 6.3  ✅  4 H4 metrics defined by Opus: pullback_bars, pullback_depth_pct, vol_trend, candle_compression
           ✅  Key insight: depth needs duration context → rate_of_descent = depth/bars (flagged pre-H4 spec)

Step 7      — Code Audit + CSV Rebuild (2026-04-09)
Step 7.1  ✅  Cross-day bug fixed (606 invalid signals); Pine Script updated; all 30 CSVs rebuilt (44,834)
Step 7.2  ✅  Two-stage review hooks wired: Stop hook (scan_modified.py) + Stage 1 plan review in CLAUDE.md
Step 7.3  ✅  Full independent cold audit: 2 MEDIUM + 5 LOW bugs found across fv2_batch_build.py + build_html1.py
           ✅  Bug 4 (MEDIUM): slope computed post-filter → first 5 bars of 2022 forced flat; fixed pre-filter
           ✅  Bug 9 (MEDIUM): CSV labels 'rising'/'flat'/'falling' vs H1 'R'/'L'/'F' mismatch; standardised to R/L/F
           ✅  Bug 1: eod_map positional → eod_datetimes set (robust, no index dependency)
           ✅  Bugs 3,7,8: dead code removed, NaN ATR skip added to H1, unreachable path fixed
           ✅  29 DS3 CSVs rebuilt clean: 43,296 signals; BAJFINANCE Kite fetch pending
Step 7.4      BAJFINANCE CSV missing — Kite MCP returned no candles; retry pending
           ✅  Signal insight: G4+G5 pass → hits target despite G1/G2/G3 fail (POWERGRID Dec 22 sig 1)

Step 8      — TV Pine Signal Visualisation (2026-04-10)
Step 8.1  ✅  H1 zoom/pan added: scroll-wheel, +/−/1:1 buttons, arrow key panning
Step 8.2  ✅  Pine touch candle fix: best_k accumulator picks EARLIEST touch (matches H1 forward-scan)
Step 8.3  ✅  Pine box sizing: body-only (open/close), not wicks; date filter to stay under 500 box cap
Step 8.4      TV box alignment in progress — T/B ground-truth labels added; time±150000 compiled, pending confirm
