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
Step 7.4  ✅  BAJFINANCE CSV confirmed present — BAJFINANCE_5min.csv in fv2 intraday_5min folder
           ✅  Signal insight: G4+G5 pass → hits target despite G1/G2/G3 fail (POWERGRID Dec 22 sig 1)

Step 8      — TV Pine Signal Visualisation (2026-04-10)
Step 8.1  ✅  H1 zoom/pan added: scroll-wheel, +/−/1:1 buttons, arrow key panning
Step 8.2  ✅  Pine touch candle fix: best_k accumulator picks EARLIEST touch (matches H1 forward-scan)
Step 8.3  ✅  Pine box sizing: body-only (open/close), not wicks; date filter to stay under 500 box cap
Step 8.4      TV box alignment in progress — T/B ground-truth labels added; time±150000 compiled, pending confirm

Step 9      — Manual Signal Review + Gate Restructure (2026-04-16)
Step 9.1  ✅  Gate system redesigned: 5-gate (G1-G5) → 3-gate temporal (G1=pre-touch, G2=touch&bounce, G3=post-bounce)
           ✅  H1.1 PARAMS + submitReview() updated; log row now writes G1/G2/G3 columns only
           ✅  All signal .md files restructured: TATAMOTORS (#1-8), POWERGRID (#1-9), HDFCBANK (#1-4)
           ✅  Obsidian analysis folder rebuilt: new obs files (G1_pretouch/G2_touchbounce/G3_followthrough); old G1-G5 deleted
           ✅  fv2_signal_patterns.md: Param Candidates section added; bounce_close_vs_MA parked from TATAMOTORS #8

Step 9.2  —   Python learning session (2026-04-16) — no fv2 changes; quadratic formula + Codedex basics
           ✅  touch_body_pct threshold corrected: >40% = fail (was >60%)
           ✅  LATE outcome added: entry ≥ 14:45 auto-flagged in H1.1; 3 signals flagged across stocks

Step 9.3  —   Idle session (2026-04-17) — no fv2 changes; CC desktop feature Q&A only

Step 9.4  — 2026-04-19
           ✅  TATAMOTORS signals #9–#11 logged (March 17 2025 — SL spike, EOD- resistance, wanna-be pullback)
           ✅  Pine touch loop fix deployed — removed break, earliest touch (largest k) live on TMPV 5-min
           ✅  H1 Review Signal button moved to sidebar; Chrome MCP via localhost:8765 HTTP server
           ✅  G2 param roles locked: wick_defence_ratio=hard gate, shoot_depth=wick-touch primary, touch_body_pct=uniformity proxy
           ✅  fv2_obs_G2_touchbounce.md updated with param roles + wanna-be pullback pattern note
           ✅  22 signals reviewed total (9 POWERGRID + 2 HDFCBANK + 11 TATAMOTORS)

2026-04-22  SS ───────────────────────────────────────────────────────────
           ✅  POWERGRID signals #13–#16 reviewed — #15 and #16 first winners
           ✅  H1.1 submit bug fixed — serial number regex + stock col removed + diff added
           ✅  G3a/G3b param names fixed in H1.1 (was G5a/G5b)
           ✅  Pine k=0 triangle → purple compiled; ATR mismatch (RMA vs SMA) flagged
           ✅  Emerging patterns: G1 load-bearing hypothesis + failed prior touch pattern
           ✅  27 signals reviewed total (16 POWERGRID + 11 TATAMOTORS)

2026-04-30  SS ───────────────────────────────────────────────────────────
           ✅  Signal #17 logged (POWERGRID Jun 26 12:20T) — G1 full fail, bounce vol only, Win; exception flagged
           ✅  Signal detail block serial numbers #15/#16 corrected in POWERGRID log
           ✅  TODO parked F10 updated: Stock mock + algo test merged, pre-F&O context added
           ✅  32 signals reviewed total (POWERGRID: 32 signals, 3 winners: #15 #16 #17)

2026-05-04  SS ───────────────────────────────────────────────────────────
           ✅  TV vs Kite OHLC mismatch root-caused — tick aggregation difference; Kite = ground truth
           ✅  9:15 TV touch gap explained — ₹0.005 TV/Kite ma20 delta flips borderline condition
           ✅  H1.1 bugs fixed: sl missing from candle_touch (#01), candle_t3 never in object (#02),
               touch_idx/bounce_idx missing → sameCandle always true (#09/#10)
           ✅  build_html1.py patched + H1 rebuilt; smoke test passed on k=0 and k>0 signals
           ✅  CC contract rule + SMOKE TEST RULE added to CLAUDE.md
           ✅  P2a closed; TODO cleaned to 3-item critical path; F12 TV Copilot added to parked

2026-05-05  SS ───────────────────────────────────────────────────────────
           ✅  POWERGRID signals #18–#21 reviewed — June 26 2025 flagged as momentum day anomaly
           ✅  Fakeout pattern documented: k=0/1 + extreme vr (3x+) + no pullback = noise win category
           ✅  Gate implication: min pullback bars (swing high → T0 ≥ 3) would reject all fakeouts
           ✅  Signal #21 (9:15 Win) flagged as opening bar special case; P4 added to TODO
           ✅  CLAUDE.md cleaned — 5-gap → 3-gate language, 30 stocks corrected, stale lines removed
           ✅  H1 tooltip hover delay (200ms) + hide-on-move fix implemented surgically
           ✅  36 signals reviewed total; decision pending: H5-first vs continue manual review

2026-05-06  SS ───────────────────────────────────────────────────────────
           ✅  Signal #22 logged — POWERGRID Jul 22 11:15, Win, anomaly (full G1 fail)
           ✅  Signal #23 logged — POWERGRID Jul 22 11:50, Win, not a winner (#04 fail: lows rising to T0, wick touch only)
           ✅  Signal detail headers #18–#23 fixed (missing signal numbers)
           ✅  Deep pullback analysis: lower high concept validated via CSV data; swing high unconfirmable for #23
           ✅  38 signals reviewed total; decision: move to H5 build (signal review phase complete)
           ✅  H5 planning questions raised — build script + HTML, 30 stocks, gate sliders + auto verdicts
           ✅  CC Remote Setup documented in CLAUDE.md — .bat path, correct command, bug fix logged
           ✅  CCP protocol expanded — reads all 8 files (6 SS-triggered + 2 auto-memory)
           ✅  BAJFINANCE CSV confirmed present; Step 7.4 marked complete in PROGRESS_HISTORY.md
           ✅  Signal #22 logged — POWERGRID Jul 22 2025, 11:15 touch, Win, anomaly (fails most params)
           ✅  Abbreviation rules + glossary added — CLAUDE.md 4-rule policy + TODO.md glossary
           ✅  tb_gap introduced as standard replacement for k (touch-to-bounce gap in bars)
           ✅  37 signals reviewed total; #23 (Jul 22, 11:50 touch) in progress — H1 params pending

2026-05-09  SS ───────────────────────────────────────────────────────────
           ✅  /resume vs CCP protocol clarified — resume = recovery, CCP = intentional SS
           ✅  export_h5_signals.py built — raw signal detection, 12 params, SL/target exit sim
           ✅  p04 swing high logic fixed — window: T0-1 back to prior touch, highest high wins
           ✅  bounce_bar_index + entry_bar_index added to signals CSV schema
           ✅  export_h5_candles.py built — T0-10 to exit+3 window, bar_index relative to T0
           ✅  CSV encoding fixed — UTF-8, LF line endings, no BOM
           ✅  H5 Lite React artifact built on claude.ai — 3-panel, 12 params, real CSV support
           ✅  SVG candlestick chart wired — T0/BNC/ENT markers, MA20, SL, TGT lines
           ✅  Signal tuning loop validated end-to-end on POWERGRID 2022 (100 signals)

2026-05-07  SS ───────────────────────────────────────────────────────────
           ✅  H5 param spec built — all 12 params discussed one by one (formula + H5 implementation)
           ✅  fv2_params.md created at Algo_Trading/Docs/fv2_params.md
           ✅  H5 design decisions locked: Explore/Filter modes, gate independence, N/A propagation rules
           ✅  Param types defined: tunable threshold, tunable count, tunable range, binary/quality
           ✅  Opus review completed — 7 valid findings fixed, 5 invalid/out-of-scope skipped
           ✅  Slider ranges updated (#01→0.50%, #02→0.20%, #05 max→2.0, #07 max→5.0)
           ✅  #07 edge cases hardened (negative numerator/denominator → N/A)
           ✅  F0 added to TODO: Claude-in-Claude React artifact for H5 lite

2026-05-11  Line 46 bug fixed in export_h5_signals.py — removed hardcoded prev bar condition from T0 definition; p03=0 signals now included in CSV

2026-05-16  SS ───────────────────────────────────────────────────────────
           ✅  guides/ folder created — 6 reference docs extracted from CLAUDE.md
           ✅  Excel Dark Mode Setup guide saved to guides/excel_dark_mode_setup.md
           ✅  CLAUDE.md GUIDES section added with what-goes-where decision rule
           ✅  CLAUDE.md heading hierarchy fixed: # → ## for all section headings (Obsidian)
           ✅  #01/#09/#10 Obsidian tag issue fixed — escaped with backslash
           ✅  Python learning journey section added to CLAUDE.md (Codecombat→Codedex→RealPython)
           ✅  `lm` shorthand added — learning mode: explain concepts, no solution code
           ✅  Codedex CSV module completed: file modes, csv.reader/writer, try/except, append pattern

2026-05-19  SS ───────────────────────────────────────────────────────────
           ✅  export_h5_signals.py reviewed end to end — all params p01-p12, PnL sim, for-else understood
           ✅  SL/TGT multipliers fixed in export_h5_signals.py (1.0/1.5 → 2.5/4.5 ATR)
           ✅  export_h5_candles.py partially reviewed — shift(1), ATR, signal loading done
           ✅  Framework_V2/Notebooks/ created; explore.ipynb set up with Python 3.14 kernel in VS Code
           ✅  Codedex: higher-order functions, map/filter/reduce, list comprehensions, classes, unittest basics
2026-05-21 | Completed export_h5_candles.py full review — window loop, bar_index, output section clean

2026-05-23 | Codedex intermediate Python complete (unittest ch): setUp/tearDown/assertRaises/BankAccount/CoffeeMenu
2026-05-23 | export_h5_signals.py + candles.py: entry cutoff >=14:40 + hard EOD exit at 15:00 (bar open) applied

2026-05-26 | export_h5_signals.py EOD loop bug fixed (S062/S078 W not EOD+); both CSVs re-exported (100 signals / 3687 rows)
2026-05-26 | H5 Lite tuning complete — best combo p05+p08+p11: 21 signals, WR 61.9%, PF 2.43 (POWERGRID 2022)
2026-05-26 | h5_full.html built (lightweight-charts v4, PapaParse, Optuna JSON upload, multi-stock/year)

2026-05-27 | 5-stock Optuna batch explored — tb3 wins 3-2 PF (2.00-2.77), p11 active in all 10 variants
2026-05-27 | h5_full.html: p04 NaN rendering bug fixed (empty string -> NaN in parseSignalRow line 133)
2026-05-27 | Walk-forward plan confirmed: train 2022, validate 2023/2024/2025; 30-stock sweep is next

2026-05-28 | p11 lookahead fixed → p11_open; p12 dropped; all scripts + HTML updated
2026-05-28 | 30-stock Optuna (p11_open, 2022): 9/30 cleared PF≥1.3; 5 both-variant survivors
2026-05-28 | WFA + cross-val complete: signal regime-specific; 2024 breaks all stocks

2026-05-29 | HTML cleanup: #11 renamed entry_open_above, #12 removed; temp scripts moved to scripts/
2026-05-29 | Manual WFA on PNB tb3: no single param combo holds 2022-2025; regime problem confirmed
2026-05-29 | Regime filter concept defined: pre-condition above gates; raw bounce rate = Option 1 metric

2026-06-01  Voice Bridge built — voice_bridge.py + MCP server; CD running ✅

2026-06-05 | h5_full.html p10 slider max fixed 9→3 (3 locations: slider, default state, reset)
2026-06-05 | WFA replayed: 5 stocks × 4 years — regime degradation confirmed across all stocks
2026-06-05 | Universal Optuna attempted (30 stocks × 4 years, 182k signals) — abandoned; baseline PF 0.924, regime makes it unsound
2026-06-05 | Regime analysis: ATR14% and Vol_StdDev20% are strongest year-quality separators
2026-06-05 | Regime filter WFA: ATR14%≥2.25 + Vol_StdDev20%≥65 — 3/5 worst years zero valid days; works as go/no-go gate not day filter
2026-06-05  SS ───────────────────────────────────────────────────────────
           ✅  MA sweep: 10 variants (SMA/EMA 10-30) across 30 stocks 2022-2025; EMA15 best PF (0.914), EMA25 best net PNL
           ✅  Confirmed: MA type change does not fix regime problem; all MAs still PF < 1.0
           ✅  Opus advisor: bounce rate ruled out as filter (circular); ER + MA20 run-length + VR chosen as regime metrics
           ✅  Regime filter 5-step sequence locked; shareable Claude.ai brief written
           ✅  Decision: run regime filter test first; if OOS fails → pivot to ORB (reuse fv2 infra)
2026-06-08 | Regime metrics computed (30 stocks, 29288 rows); POWERGRID monthly analysis shows no ER/run-length/VR separation; H5 export added; 30-stock correlation run is next
2026-06-10 | Pine Script W/L markers working; MA stack analysis complete (720 configs, 182k signals, best +3.7pp lift — weak); signal-bar metrics plan locked (5 visual metrics ordered: slope→approach→BB→volume→depth)
2026-06-11 | IS/OOS signal filter backtest: 0/11 metrics pass OOS PF > 1.01; Optuna best OOS PF 0.9616 — fails
2026-06-11 | p11_open renamed p11 codebase-wide (120 CSVs + 12 scripts + HTML)
2026-06-11 | TV MCP setup complete: CDP bat file, v6 fv2 MA Bounce strategy live on POWERGRID 5-min
2026-06-11 | Big Beluga regime filter visual exploration: Red=W, Green/Blue/Yellow=L/EOD confirmed on NIFTY+POWERGRID Jan-Feb 2022
2026-06-11 | 3-filter framework identified: regime (Red) + structure (clean G1) + time (10:00-13:30)
2026-06-11 | Key insight: pre-touch approach direction (downtrend delivering price to MA20) = primary W predictor

2026-06-12 | Big Beluga Python tagger built (beluga_tagger.py) — HMA formula replicated, signals tagged R/G/B/Y
2026-06-12 | Top 8 Nifty stocks regime-tested (2022 tb3): no universal quadrant filter — stock-specific at best
2026-06-12 | Opus 4.8 consulted: R:R mismatch identified — 4.5R trend-following exit on mean-reversion entry, breakeven W%=35.7%, actual=16-20%
2026-06-12 | p11 double-assignment bug found (Opus) and fixed in export_h5_signals_batch.py
2026-06-12 | P2 forward drift run: unconditional EOD+%=44-54% (survival bias exposed — was 60-74% conditional only)

2026-06-13 | Breakeven W/(W+L)=35.7% established; ITC 2022 baseline=34.4%, working target=38-40% IS
2026-06-13 | voltrend_touch < 4 = peak IS filter for ITC 2022 (36.8%, 1178 signals); high voltrend hurts
2026-06-13 | ITC Beluga quadrant split: G=41.3% (only above breakeven), R=27.4% (worst)
2026-06-13 | G+B+Y best-case OR filter: 38.8% IS, 740 signals — collapses OOS 2023-2025
2026-06-13 | ITC W/(W+L) structural decay confirmed: 34.4->28->25.6->22% across 2022-2025
2026-06-13 | Visual review: pre-T0 Beluga crossover = faster target hit; Green quad = cleanest Ws
2026-06-14 | Kijun Bounce backtest built; Kijun-HL 4/5 stocks PF>1; data issue found (demerger adj ~11%); TV ADJ PF=0.759 signals fragility
2026-06-15 | Kijun-HL backtested on 30 stocks (fv2 CSV); 11/30 PF>1; best 5-stock combo PF=1.606; ~72 trades/yr too low for standalone
2026-06-15 | Pine Script aligned to Python logic (entry bar open, bounce bar ATR, prev-day Kijun); TV gap confirmed as data-driven
2026-06-15 | Next: HMA Bounce exploration (P1); Trading ABD (P2); Kijun filter on MA20 (P3)
2026-06-15 | EOD corrected 15:15→15:00; re-ran 30-stock backtest (PF 0.848); Top 6 sweet spot (PF 1.489, N=157)
2026-06-15 | Kijun period sweep (10/20/30/40/50-day): 50-day only profitable (PF 1.378); shorter periods all fail
2026-06-15 | Next: hma_bounce_backtest.py (separate script); HMA from Beluga oscillator; do not modify fv2 MA20 script
2026-06-15 SS ──────────────────────────────────────────────────────────────
           ✅  HMA20 bounce backtest built (hma_bounce_backtest.py) — 30 stocks raw PF=0.944 vs SMA20 PF=0.918
           ✅  fv2 baseline confirmed: no volume filter better (PF 0.918, N=51,803 vs 0.906 N=44,823)
           ✅  Per-stock baseline (no vol): BHARTIARTL(1.053) > DABUR(1.049) > ASHOKLEY(1.030) > SUNPHARMA(1.013)
           ✅  BHARTIARTL adopted as reference stock going forward
           ✅  TGT-WR / PFT-WR terminology locked (never plain WR); theoretical BE = 35.7%
           ✅  Trading ABC (TV community script) fully dissected — 5-step logic: Trend Cloud → ZigZag → ABC Fib → Bounce → Signal
           ✅  lstoch = dead code in Trading ABC (computed, never wired into signal)
           ✅  Multiple C labels explained: abc_bar_count<=6 fires independently on each bar within 6-bar window
           ✅  Next: P2 Trading ABC Python backtest on BHARTIARTL (Step 4 standalone vs full 5-step)

2026-06-27 SS ──────────────────────────────────────────────────────────────
           ✅  fv2 baseline locked: ma_bounce.py N=49,039 | PF=0.922 | Prof_WR=41.5% | EOD 15:00
           ✅  RSI/MACD 40-bar DS3 warm-up added to rsi_macd_mfe.py (29 stocks fixed)
           ✅  RSI/MACD 4-panel chart confirmed: RSI<30 PF=1.31 (n=53 only); MACD flat (0.88-0.98)
           ✅  fv2_baseline_formula.md corrected: BHARTIARTL ranked #1 (PF=1.092), ASHOKLEY #2 (1.054)
           ✅  BAJFINANCE DS3 gap documented (26 trades NaN, 0.05%); fetch script created for Claude Desktop
           ✅  Next: RSI×MACD 2D combination heatmap — find zone where both push PF>1.0
