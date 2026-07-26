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

── 2026-06-28 to 2026-06-30 — v2 signal build ───────────────
           ✅  VWAP explained; v1 gives clean VWAP split (0.090 PF gap above vs below)
           ✅  guides/iteration_log.md created — 5 iterations tracked (#1 baseline → #5 v2)
           ✅  EMA sweep (EMA50-250 × VWAP combos): Below EMA100 + Above VWAP = PF=1.010 N=8,377
           ✅  Filter-at-entry vs post-hoc distinction clarified and documented in iteration log
           ✅  TV CSV (HDFCBANK) analyzed: PF=0.616 explained by 0.05%/side commission on thin edge
           ✅  Pine Scripts moved to core/pine/ (co-located with Python counterparts)
           ✅  core/ma_baseline_v2.py built: v1 + Above VWAP + Below EMA100 | N=8,374 PF=1.013
           ✅  core/pine/fv2_baseline_v2.pine built: same logic for TV visualization
           ✅  MAX_TB_GAP removed from v1 and v2 (dead code for v1-style touch)
           ✅  Next: TV PF cross-verification for v2 on HDFCBANK

2026-07-03  SS ───────────────────────────────────────────────────────────
           ✅  ABC short tight sweep: SL=0.3 TGT=0.3 → PF=1.842, Sharpe=4.692, WR=67% (30 stocks)
           ✅  CBQ renamed from QVS; scripts renamed (abc_short_cbq.py, v1_1_cbq.py); glossary updated
           ✅  ABC short CBQ: NPF asymptotes 0.646@qty=1000 — dead end; iteration #7 logged
           ✅  v1.1 SL×TGT sweep + position guard bug fixed (N: 21,556→8,273); best SL=2.5x TGT=6.0x
           ✅  v1.1 CBQ: PF=1.032, NPF=0.893@qty=1000 — dead end; iteration #8 logged
           ✅  Baseline SHORT (v2) declared new structural direction: high>=MA20, open<MA20, close<MA20
           ✅  v2 results: N=42,612, PF=1.076, Sharpe=0.833, all 4 years profitable (2023=0.999)
           ✅  Long baseline at same params: PF=0.926 sub-1.0 every year — short foundation stronger
           ✅  v2 CBQ: NPF=0.898@qty=1000 — same ceiling; fix raw edge first (target PF>1.3)
           ✅  fv2_baseline_v2.pine built; guides/ma_baseline_v2_formula.md created; #9 logged
           ✅  Pine scripts synced TV→local: fv2_baseline.pine, fv2_baseline_v1_1.pine, fv2_baseline_v2.pine
           ✅  Next: v2 filter build (v2.1 wick-only → v2.2 VWAP → v2.3 EMA)


2026-07-03  SS (Evening) ─────────────────────────────────────────────────────
           ✅  Version hierarchy restructured: v2=bare SHORT (mirror v0), v3=wick-only SHORT (mirror v1)
           ✅  ma_baseline_v2.py rewritten: bare SHORT (high>=MA20, search 3 bars for close<MA20, SL=2.5x TGT=4.5x)
           ✅  ma_baseline_v3.py created: wick-only SHORT (formerly v2, SL=2.0x TGT=3.5x)
           ✅  EOD date guard fixed in ma_baseline_v3.py inner loop (no overnight holds)
           ✅  Fair comparison v0 vs v2 at default SL=2.5x TGT=4.5x: SHORT PF=1.078 vs LONG PF=0.911 — SHORT wins all years + Sharpe
           ✅  Iteration log split: LONG (8 iterations) + SHORT (new section, #1=v2 pending, #2=v3)
           ✅  Runner scripts created: run_baseline_v0/v1_1/v2/v3/all.py (minor errors — P2)
           ✅  compare_v0_v2.py built for sweep — BUG: LONG uses v1 signal not v0 (fix P1 next session)
           ✅  Next: fix LONG signal bug, write locked standalone baseline scripts, run proper sweep
           ✅  2026-07-04: Rebuilt standalone baselines — ma_bounce.py (LONG) + ma_rejection.py (SHORT) in baseline_explorations/
           ✅  LONG bare final: N=49,062 PF=0.922 Sharpe=-1.458 | SHORT bare final: N=47,787 PF=1.079 Sharpe=1.455
           ✅  SHORT edge positive all 4 years (2022-2025), 27/30 stocks PF>1.0, top: TATAMOTORS PF=1.394
           ✅  baseline_reserve/ma_bounce.py locked clean; CLAUDE.md folder protection rule added
           ✅  Next: lock both into reserve → analyse SHORT edge → build SHORT v1 (wick-only mirror)
2026-07-18 | Reviewed backtesting_rules_v2.md; aligned with CC; 2 P1 fixes identified (daily Sharpe, entry bar hour check); Zerodha/ZPF adopted; TODO reset with cloud engine as P2
2026-07-19 SS ───────────────────────────────────────────────────────────
           ✅  6BCE SHORT 90-combo sweep built + run (DS3 30 stocks 2015-2025); best ZPF=0.888 — dead
           ✅  Cache system: sweep_cache_6bce.npz (overall_grid + yearly_grid + yearly_zshd_grid)
           ✅  4 chart scripts: zpf_lines, consistency, spaghetti (ZPF), spaghetti (ZSh(D))
           ✅  Key finding: smoothest combo (SL=2.0/TGT=2.0) = consistently bad; best by ZPF=ZSh(D)
           ✅  Best consistency: SL=6.0/TGT=5.5, cs=0.8198; only 2020 had ZPF>1.0 on any combo
           ✅  Plan: Grok CLI handles new signal sweeps; CC focuses on cloud engine build

2026-07-21 SS ───────────────────────────────────────────────────────────
           ✅  Grok's 6BCE VWAP script validated — logic + spot-check N/ZPF exact match
           ✅  ConsScr computed for both combos; locked SL=6.0/TP=6.0 as best consistency (-2.709)
           ✅  Equity + drawdown chart built for 6BCE VWAP (MaxDD ₹-16,288 vs baseline ₹-28,494)
           ✅  SL/TP terminology locked project-wide (replacing SL/TGT); glossary updated
           ✅  Strategic pivot: regime-adaptive online learning model (MemLabs video 2)
           ✅  6 months of static filter failures → new direction: adaptive weights, not static gates
           ✅  MemLabs notebook purchase pending (card declined, retry tomorrow)
2026-07-19 SS (Kite paper trading bot) ───────────────────────────────────
           ✅  kite_auth.py built + validated; AVG antivirus SSL interception found, AVG uninstalled
           ✅  TATAMOTORS demerger discovered (→TMPV/TMCV, Nov 2025); DS3 confirmed unaffected (same
               instrument_token as TMPV) — live bot queries TMPV going forward, no rebuild needed
           ✅  Data architecture locked: ticks-only live engine (signal/entry/exit); historical_data
               reserved for offline reconciliation script only (not yet built)
           ✅  SL/TP naming convention adopted going forward (replaces TGT in new scripts only)
           ✅  Locked combo re-validated from iteration_log.md: SL=2.0x/TP=4.5x, N=110,641, PF=1.135,
               Sharpe=2.358 (corrects the provisional 2.5x/4.0x used earlier in planning)
           ✅  Offline paper-trading engine built (ma_30_rejection_v1_offline.py): bar-by-bar,
               live-shaped state, incremental MA20/ATR14 — matches reference PF/Sharpe exactly,
               N within 0.0036% (floating-point tie-break at exact-tie bars, root cause fully
               diagnosed and documented, not a bug); independently corroborated by Grok's review
           ✅  Automation plan: Oracle Cloud VM deploy target (not local PC), cron scheduling,
               manual Kite login to start (option 1), headless login automation to test later
           ✅  Next: position sizing + shortability check in offline engine → reconciliation script
               → live KiteTicker script → automation wrapper
2026-07-20 SS (Kite paper trading bot — first live test) ─────────────────
           ✅  Shared core logic extracted (ma_rejection_v1_core.py); offline engine refactored
               to import it, no behavior change, already-validated logic preserved
           ✅  Live engine built (ma_30_rejection_v1_live.py): KiteTicker builds own 5-min bars
               from real ticks, tick-based SL/TP exit monitoring, historical_data warm-up only
           ✅  First live connection test during market hours (~12:30pm-3:10pm IST): auth,
               instrument resolution, warm-up, tick-based bar building, signal detection all
               confirmed working correctly on real data
           ✅  Real signals fired live: DABUR, WIPRO, JSWSTEEL (13:55) — first live proof the
               wick-touch signal works on real market data, not just DS3 replay
           ✅  First live trade closed: WIPRO SL hit. Verified math by hand: entry=176.23,
               exit=176.5314286 (=sl exactly), pnl=-0.3014286; SL/TP ratio=2.25 matches
               TP_MULT/SL_MULT (4.5/2.0) exactly
           ✅  Two real bugs found + fixed live: (1) CSV PermissionError crashed the script when
               live_bars.csv was open in Excel — now caught, skip+retry, no data lost; (2)
               EOD-hour exit was ~5min late (bar-close-based) — now tick-based like SL/TP,
               fires the instant an hour>=15 bucket starts. Fix #2 not yet live-tested
           ✅  Reconciliation script built (ma_rejection_v1_reconcile.py): bar-level + trade-level
               diff vs Kite's official historical_data. First real run: 270/270 bars matched in
               count but 48 (17.8%) had real OHLC diffs up to ₹4.50 (bigger than DS3's floating-
               point tie-break scale); 13 live trades vs 11 official-replay, only 7 matched.
               Causes hypothesized (mid-bucket startup effect, ticks as periodic snapshots) but
               not yet confirmed with a concrete traced example
           ✅  Found live_bars.csv/live_trades.csv get overwritten each run — no cross-day
               persistence yet; today's data saved manually, archival automation planned next
           ✅  Position sizing and shortability check remain deliberately deferred/stubbed
           ✅  Next: confirm EOD fix live → trace one concrete reconciliation mismatch to root
               cause → build CSV archival + recon-output-to-file → position sizing → shortability
               → automation wrapper
2026-07-21 SS (Kite paper trading bot — MODE_FULL fix, EOD hard-stop) ────────
           ✅  Root cause of tick-bucketing bug found: MODE_QUOTE never provides exchange_timestamp
               (verified in pykiteconnect source) — ticks were bucketed by local datetime.now()
               instead of real exchange time. Fixed: subscribed in MODE_FULL instead
           ✅  EOD hard-stop added: eod_reached event + grace period, bot fully terminates itself
               (not just idles) once all positions are flat after EOD_HOUR is crossed
           ✅  Confirmed live, twice: temporary EOD_HOUR=14 test (3 positions closed exactly at
               14:00:00, auto-stopped) and the real EOD_HOUR=15 (3 positions closed at
               15:00:00-15:00:02, auto-stopped) — both tick-based exit and hard-stop work correctly
           ✅  Reconciliation script now saves fetched bars + findings to data/recon/ (was
               console-only); re-run against 2026-07-20 matched the manual run exactly (deterministic)
           ✅  Found a real bug in reconcile script: fetch window excludes the session_end bar
               itself, so it can never capture an EOD-triggered trade — explains most of a
               3-live-vs-0-recon-trades gap on today's short test session
           ✅  Traced the 3-vs-0 gap to two distinct causes: fetch-window bug (JSWSTEEL — signal
               timing actually matched exactly) and the startup-corrupted first bar affecting
               real signal detection (INFY — suppressed a real early signal; SUNPHARMA — opposite,
               unresolved after a reconstruction attempt didn't match live's actual behavior)
           ✅  Added warmup_bars.csv logging to live script — future analysis uses real captured
               warm-up data instead of error-prone after-the-fact reconstruction
           ✅  Oracle Cloud VM setup started: SSH key found and validated, WSL confirmed not
               installed, install deferred (needs restart) until live testing finished
           ✅  Cron + automated login discussed: option 1 (manual login) confirmed as the path
               forward, option 2 (headless login) technical shape covered but risks flagged
               (stored credentials, likely bot-detection) — deferred as an experiment only
           ✅  TODO.md reprioritized: Kite bot promoted to P1
           ✅  Next: install WSL/Ubuntu + SSH to VM → fix reconcile fetch-window bug → add
               MA20/ATR14+touch-eval logging → resolve SUNPHARMA mismatch → full-day live test
2026-07-22 SS (Kite paper trading bot — first VM deployment) ─────────────
           ✅  WSL/Ubuntu installed on laptop; SSH to Oracle Cloud VM (161.118.164.160,
               ubuntu@instance-20260712-0412) established using the found key file
           ✅  VM had pending updates ("system restart required") — rebooted via sudo reboot,
               reconnected successfully, kernel confirmed up-to-date after
           ✅  VM environment set up: python3-pip, python3-venv, kite_bot_env virtual env with
               kiteconnect/pandas/numpy/python-dotenv (matplotlib/plotly deliberately skipped -
               VM only executes+logs, charting stays local)
           ✅  Live bot deployed: only the 2 files actually needed (ma_30_rejection_v1_live.py +
               ma_rejection_v1_core.py) plus .env + kite_auth.py, not the whole scripts/ folder
           ✅  First scp attempt failed silently (run in PowerShell with WSL-style paths, wrong
               shell for that path syntax) - fixed by running from an actual WSL Ubuntu terminal
           ✅  Found + fixed a real rate-limit bug: 30 sequential unbatched kite.ltp() calls
               worked "by accident" locally (network latency masked it) but broke on the VM's
               faster connection - batched into 1 call; added 0.34s delay to warm-up's
               historical_data loop (can't be batched, inherently per-instrument)
           ✅  Bot ran successfully on VM and produced real bars - but found two NEW VM-specific
               bugs: (1) VM's system timezone is UTC not IST, so Kite tick timestamps resolve
               wrong (masked locally since laptop's own clock is IST) - also means EOD_HOUR
               would fire at the wrong real-world time on the VM as-is, fix known
               (timedatectl set-timezone Asia/Kolkata) but not applied yet; (2) bot process
               silently exited after ~2 bar cycles, no crash visible yet, CSV data intact
               through that point (rules out mid-cycle freeze) - root cause unknown
           ✅  Concepts clarified: scp vs sftp vs ftp, scp's fixed transfer direction (needs the
               reachable side, i.e. the VM with public IP, not the laptop), venv purpose, WSL
               vs cloud-provider CLI tools (fundamentally different categories)
           ✅  Next: diagnose the silent VM process exit → fix VM timezone → re-run full-day VM
               test → recon script against VM's live_bars.csv → older open items (reconcile
               fetch-window bug, MA20/ATR14 logging, SUNPHARMA mismatch) still carried forward
2026-07-23 SS (Kite bot — VM hardening, position-recovery, full-day validation) ─────
           ✅  VM timezone fixed (Asia/Kolkata applied, verified via date/timedatectl)
           ✅  Built kitebot.service (systemd) + kitebot-alert.service (OnFailure hook) - crash
               alerts pushed via ntfy.sh (topic codeponting-kitebot-x7j2m9); enabled for
               auto-start on VM reboot; tested end-to-end via kill -9, confirmed push landed on
               both desktop (PWA) and phone (native app)
           ✅  Built event-driven position-recovery: save_positions()/load_positions() snapshot
               open_positions.json on every open/close (not polled); reconcile_gap_positions()
               replays historical_data since entry against fixed SL/TP to check if a restored
               position was actually hit during downtime - closes retroactively if so
           ✅  Full real-data validation: 6 open positions, Ctrl+C, restart - all 6 restored
               correctly, SUNPHARMA correctly gap-closed (SL hit during downtime), independently
               re-verified against official Kite historical_data - exact match
           ✅  EOD tick-exit validated live (clean 15:00 auto-stop, all positions closed) and via
               standalone simulation (fires on exact boundary tick, no duplicate exits)
           ✅  Ran 4 iterations of VM live testing today, archived to data/trades/daily
               data/23rdJuly/ - discovered live_bars.csv/live_trades.csv only overwrite once
               their in-memory list is non-empty (not every cycle) - explains why old trades
               persisted across some pulls and vanished by others
           ✅  Ran original recon script against full session - bar-level clean, trade-level
               showed real mismatches; independently spot-verified 3 trades (SUNPHARMA, NTPC,
               JSWSTEEL) against raw official data - all correct on price/timing
           ✅  Built ma_rejection_v1_trade_check.py (new, separate script) - custom --start/--end
               window + full-universe replay, to check specific known bot-uptime windows instead
               of the whole market session
           ✅  Key finding: ATR14 (unlike MA20) is sensitive to live-tick-bar high/low vs official
               bar high/low, causing official-replay SL/TP to diverge from live's actual SL/TP
               even on otherwise-correct data - explains most of today's trade-level mismatches
               (only 2/17 checked trades matched exactly across 3 verified uptime windows)
           ✅  Side task: pulled a save-state git commit, resolved a VS Code Settings Sync
               conflict between desktop/laptop (merged, excluded colorTheme from sync)
           ✅  Next: decide how to handle the ATR14 divergence for validation → dig into
               remaining unexplained mismatches → confirm VM's live.py is the updated version →
               fix live_trades.csv silent data-loss on restart
2026-07-24 SS (baseline_reserve_lock cleanup + MemLabs regime-model real implementation) ─────
           ✅  Renamed TGT→TP across all 4 files in baseline_reserve_lock/ for terminology
               consistency (explicit permission given despite folder normally being locked) -
               variables/labels/docstrings only, case-sensitive replace correctly skipped the
               two lowercase filename references; all 4 scripts verified to still parse cleanly
           ✅  Fixed markdown table alignment in iteration_log_new.md (center-aligned columns)
           ✅  Started MemLabs regime-model work for real: new
               Framework_V2/scripts/trials/regime_model/memlabs/ folder, built full pipeline
               reusing the live v1 signal logic (ma_rejection_v1_core.py) against the correct
               DS3 parquet source
           ✅  Built the "memory encoding" feature (rolling-40-mean of ATR% at touch bar, no
               lookahead) exactly matching the MemLabs video's technique, applied to ATR%
               instead of returns; added ZPF/ZSh(D) metrics (Zerodha charge formula reused
               from baseline_reserve_lock/ma_30_rejection.py)
           ✅  TATAMOTORS 2023 baseline: N=316, PF=1.415, ZPF=0.894, ZSh(D)=-0.835. Tertile
               bucketing by the memory-encoded feature showed a striking-looking regime split
               (Low-vol ZPF≈0.997 vs Mid/High ~0.86); raw (non-smoothed) ATR% showed an even
               stronger, opposite-direction split (High-vol ZPF=1.442) on 2023 alone
           ✅  Extended to full DS3 range (2015-2025, N=3,697) to validate - neither 2023
               pattern held up. Year-wise breakdown (05_bucket_yearwise.py) showed every
               bucket, for both features, swinging between good and bad years with no
               consistent winner - the 2023 numbers were overfitting to one year, not a real
               stable regime effect. Honest negative result, properly documented
           ✅  Built a small OLS demo (10-trade sample, plotted scatter+fitted-line chart) to
               clarify that memory encoding (feature engineering, done correctly) and the
               actual prediction model (fitting w/b, generating y_hat, sign() as signal) are
               two separate steps - only the first has been done so far, bucketing stood in
               for the second but isn't the same thing
           ✅  Confirmed Grok CLI is installed and invocable via Bash (agentic tool, -p flag
               for headless single-turn mode, cost confirmed not a concern) - deferred actually
               using it for independent trade-log validation to next session
           ✅  Next: decide whether to fit the actual OLS regression, test across multiple
               stocks instead of just TATAMOTORS, or try a different feature entirely → use
               Grok CLI to independently validate the memlabs trade log build → Kite bot P1
               items carried forward unchanged from 2026-07-23
2026-07-25/26 SS (Kite bot warmup fix completed, data-loss bug fixed, MemLabs online-learning
closed out, VM backtesting env + VS Code Remote-SSH set up) ─────
           ✅  Reverted temporary EOD_HOUR=16 (Friday's testing value) back to 15, local + VM
           ✅  Completed the warmup-boundary fix properly: traced the exact chronological
               sequence (script start → historical_data loop → KiteTicker creation → connect()
               → first tick) to find where "which bucket to exclude" gets decided (too early -
               right after the historical_data loop, before connect()); landed on a more
               complete design than originally scoped - on_ticks() discards any tick belonging
               to the connect-time bucket or older, and a scheduled one-shot
               catchup_current_bucket() (threading.Timer, fires 5 min later) fetches that
               bucket once genuinely closed and runs it through FULL process_bar() - giving it
               a real touch-check, not just silent MA20 seeding. Closes both the duplicate and
               the "permanently skipped bar" problem at once. Implemented, syntax-verified,
               pushed to VM - NOT yet tested live, market was closed all weekend
           ✅  Fixed the live_trades.csv/live_bars.csv data-loss bug: added
               load_existing_logs(), called at startup, loading any existing CSV data into
               memory before the periodic save cycle begins - old trades survive a restart
               instead of being silently overwritten. Verified via simulation, pushed to VM
           ✅  MemLabs: built 13_online_learning_yearwise.py - the earlier promising overall
               online-learning result (N=479, ZPF=1.01) does NOT hold up year-by-year (6 pass,
               4 fail, 1 borderline) - same instability as the static bucketing found the day
               before. Also noticed the model's filter drifts toward "take almost everything"
               over time rather than staying selectively adaptive. Closes out all 3 tested
               approaches (bucketing, OLS, online-learning) with the same negative verdict.
               Confirmed all memlabs work (scripts 01-13) committed + pushed to git
           ✅  Set up ~/backtesting/ on the VM (side quest, initiated via a separate mobile CC
               session): own venv, scoped CLAUDE.md + PROGRESS.md (deliberately no full
               .remember/ system - overkill for this scope), backtesting_rules/ copied in with
               a hard "always follow it" rule, 2 reference scripts, full DS3 dataset (160MB)
               copied in. Fully independent from kite_oracle_papertrading/, with a hard rule
               never to touch that folder unless explicitly asked. Decided NOT to make the VM
               a git repo - CodePonting (desktop) stays the single source of truth
           ✅  Set up VS Code Remote-SSH end-to-end (oracle-vm host config on the Windows
               side, key permissions fixed via icacls) - direct live VM file access without
               manual scp round-trips. Also set CSV default viewer to the already-installed
               Spreadsheet Viewer (GrapeCity.gc-excelviewer) instead of Data Wrangler, which
               stays for .parquet (better suited to deep-dive work, not quick reads)
           ✅  Next (explicitly agreed): Monday market hours - watch the bot's first restart
               under the new fix → review 24th July's PnL logs + validate against recon
               (quantify stale-tick bug impact, consolidate fragmented iterations, remember
               today's fixes are untested against old data) → resume MemLabs (multi-stock or
               different feature, possibly bring in Grok CLI first)
