# CLAUDE.md — CodePonting Behavioral Instructions
# ══════════════════════════════════════════════════════════════
# This file tells Claude Code HOW to behave in this project.
# For project structure/map → see MEMORY.md
# Last updated: 2026-03-27
# For fv1 strategy config and review → see fv1_strategy_review.md in Algo_Trading/Framework_V1/ — this is the source of truth
# ══════════════════════════════════════════════════════════════

── SHORTHAND ────────────────────────────────────────────────────

  vsa = "very short answer" — reply in 1–2 lines max, no elaboration

  token-efficiency = always choose the method/technique/option that consumes
    fewer tokens with no compromise to the final outcome. applies to all tasks
    (patching vs rebuild, inline vs script, etc.)

── CLARIFICATION PROTOCOL ──────────────────────────────────────

Before executing ANY task, if any of the following are unclear — ASK first. Do NOT write or run any code until clarified.

Ask when:
  1. A file path is not explicitly listed in CLAUDE.md
  2. A config value or param is not in CLAUDE.md or the task prompt
  3. The task requires touching files outside Framework_V1_Sandbox
  4. Two valid interpretations exist for the same instruction

Do NOT ask when:
  1. The answer is already in CLAUDE.md
  2. The task is unambiguous and scoped to the sandbox

Rules:
  - List ALL questions in one batch — not one at a time
  - Never assume, guess, or trial-and-error your way to a solution
  - Never implement a workaround without flagging it first
  - If something unexpected is found mid-task (e.g. trade count mismatch,
    path not found, logic inconsistency) — STOP and report before continuing

── TWO-STAGE REVIEW PROTOCOL ────────────────────────────────

  Stage 1 — Plan review (before any code is written):
    For any significant task (new script, signal logic change, CSV rebuild,
    multi-file edit), call a reviewer subagent with the plan BEFORE touching
    any file. The reviewer checks for logical flaws, wrong assumptions, and
    cross-day leakage risks. If issues found → surface to Saurav and wait for
    approval. If no issues → proceed silently.

  Stage 2 — Final scan (automatic, after turn ends):
    A Stop hook reads all files modified in the turn and reviews each in full.
    If issues found → flagged to terminal for Saurav to decide. Silent if clean.
    Saurav always decides what to do with flagged issues — no auto-revert.

  Both stages: reviewer only speaks if it finds something. Silent = clean.

── EXECUTION RULES ──────────────────────────────────────────

Execution rules:
  - Before multi-step tasks: list all questions upfront, get approval ONCE, then execute start to finish
  - Do NOT pause mid-execution unless a critical error blocks continuation
  - At end of task: print a single summary of all actions
  - For long-running scripts (Optuna etc): print estimated runtime before launching. Only interrupt if script crashes or baseline confirmation fails.
  - After every task, silently update PROGRESS.md and TODO.md.
    PROGRESS: add one line (≤10 words) for what was completed.
    TODO: remove done item, re-prioritize remaining items.
    Only ask Saurav if the summary is genuinely ambiguous.
  - When Saurav types "ss" (save state), immediately:
    1. Update PROGRESS.md — Recent 5 steps + 5 Milestones (overwrite both sections)
    2. Write a brief summary of what was done to .remember/today.md
    3. Update .remember/handoff.md with current task + next step + known issues
    4. Call /remember:remember to save state
    All four are MANDATORY. Without them, next session starts with no context.
  - When Saurav types "ssc" (save state complete), do everything above PLUS:
    5. Update TODO.md (max 5 items, P1 priority first)
    6. Append to PROGRESS_HISTORY.md (never delete existing entries)
    Files: C:\Users\Saurav\CodePonting\.remember\
      today.md   → session log (what was done, key findings)
      handoff.md → current task status, next step, blockers
      weekly.md  → update only when a major milestone is crossed


## Progress & Context Management Protocol

  ### End of Claude.ai session (Saurav → CC):
  - Claude.ai provides PROGRESS.md one-liners + TODO.md updates
  - CC updates PROGRESS_HISTORY.md (full audit trail, never deleted)
  - CC updates TODO.md (max 5 items, P1 priority first)

  ### When Saurav types "SS" (Save State):
  - CC updates PROGRESS.md (Recent 5 steps + 5 Milestones)
  - CC updates .remember/handoff.md + today.md + weekly.md
    (these are Claude.ai CCP sources — read via cc-memory tools)
  - TODO.md + PROGRESS_HISTORY.md are updated by Claude.ai (Sonnet) separately

  ### When Saurav types "SSC" (Save State Complete):
  - Everything SS does, PLUS
  - CC also updates TODO.md (max 5 items, P1 priority first)
  - CC also updates PROGRESS_HISTORY.md (append new entries, never delete)

  ### When Saurav types "SSD" (Save State + Drive):
  - Everything SS does, PLUS
  - CC syncs all 4 .remember/ files to Google Drive
    CodePonting/.remember/ folder

  ### CCP (Context Catch-Up Protocol):
  - Claude.ai reads CC memory via cc-memory MCP tools
  - Provides session summary: what was done + next step
  - Triggered by typing "CCP" or "ccp"

  ### Files and their purpose:
  - PROGRESS_HISTORY.md → full chronological audit trail (CC writes)
  - PROGRESS.md         → lean reference: Recent 5 + Milestones 5 (SS trigger)
  - TODO.md             → current priorities max 5 items (CC maintains)
  - .remember/          → CC memory for CCP (SS trigger)


# ── WHO I AM ──────────────────────────────────────────────────

Project    : CodePonting — Algorithmic Trading System
Owner      : Saurav
Domain     : NSE F&O Equity Markets (India)
Language   : Python
IDE        : VS Code (Claude Code as agentic execution layer)
Brokers    : Upstox (primary) · Zerodha Kite (future scaling)


# ── FRAMEWORK STATUS — CRITICAL ───────────────────────────────

Framework_V0  →  LEGACY / ARCHIVED
                 187+ files, old live bot iterations (v0.1–v1)
                 DO NOT touch, modify, or reference for new work.
                 Read-only for historical reference only.

Framework_V1  →  CLOSED ❌ (as of 2026-03-25)
                 Signal confirmed insufficient. Charges = 3.4× raw profit at
                 28k trade frequency. No viable filter found after full BQS +
                 DT/RF analysis. Frozen as learning record. Do not modify.
                 Adapter Pattern + Strategy Pattern architecture retained for fv2.

Framework_V2  →  ACTIVE DEVELOPMENT ✅
                 Signal redesign underway. 5 structural gaps identified vs
                 true MA bounce. Lower trade frequency (~319/4yr) makes
                 charges manageable (1.6% of capital). Raw edge is the target.
                 Data: Framework_V2/data/historical/csv/intraday_5min/
                 Outputs: Framework_V2/outputs/reports/
                 Current: TATAMOTORS-only. Scale to 29 stocks next.

Framework_V1_Sandbox → CLOSED alongside fv1.
                        All BQS/DT/RF experiments complete and documented.
                        Read-only reference. Do not run new experiments here.


# ── ACTIVE STRATEGY — MA Bounce (fv2) ─────────────────────────

Status      : REDESIGN IN PROGRESS
              fv1 was a proximity detector, NOT a true MA bounce.
              Opus review identified 5 structural gaps:
                Gap 1 — Trend context (rising slope filter) ✅ implemented
                Gap 2 — Approach direction (price from above — gates G3)
                Gap 3 — Pullback quality (depth/structure/wick defence)
                Gap 4 — Volume signature (not just threshold)
                Gap 5 — Follow-through confirmation

fv2 Signal  : True MA bounce — 6 classic bounce criteria
              TATAMOTORS 5-min (2022–2025) as development stock
              Gap 1 result: CAGR -172% → -2.07%, PF 0.77 → 0.95
              Next: close raw edge gap (PF 0.95 → >1.01)

fv1 Signal  : CLOSED — archived for reference
              SL=A, PG+CP+AF, CAGR=-2.15% (no slippage baseline)
              With slippage: -8.62%. After charges: net negative all filters.


# ── DATA ARCHITECTURE ─────────────────────────────────────────

PRIMARY (fv2)      : Framework_V2/data/historical/csv/intraday_5min/
  fv2 CSV dataset    TATAMOTORS_5min.csv — 73,174 rows, 7 cols + outcome cols
                     Columns: signal_type, exit_reason, raw_pnl, win
                     Coverage: 2022–2025 (4 years), MA20 pre-warmed (0 NaN)

PRIMARY (fv1/Sandbox): Framework_V1/data/historical/intraday_5min_DS3/
  DS3 dataset        Chunked parquet format
                     Token metadata: ds3_tokens_chunks.json
                     Coverage: 2015–2025 (11 years)
                     29 stocks + NIFTY50
                     ⚠️  ALL sandbox scripts must use DS3. Not intraday_5min.

Legacy dataset     : Framework_V1/data/historical/intraday_5min/
                     30 stocks · Coverage: 2022–2025
                     ⚠️  DO NOT use for sandbox work. Migrated to DS3.

Daily candles      : Framework_V1/data/historical/daily/

Indicators         : Framework_V1/data/indicators/
                     Precomputed: MA20, ATR, Volume MA
                     Regenerate via: scripts/compute-indicators.py

Kaggle data        : Algo_Trading/Kaggle/
                     Used for validation only (NOT primary source)


# ── SANDBOX CONFIG — CONFIRMED WINNER (Step 3.2) ──────────────

# These are the locked-in sandbox defaults. Do NOT change without instruction.

sl_variant           = A         # fixed stop, no trailing
use_position_guard   = True      # max 1 open trade per stock
use_compounding      = True      # size scales with current equity
use_entry_cutoff     = False     # 14:45 cutoff disabled
use_auction_filter   = True      # skip entries before 09:45
use_fixed_fractional = False     # parked — no impact with SL=A

atr_mult_stop        = 2.5
rr_target            = 4.5       # implied target multiplier
risk_per_trade       = 0.01      # 1% of current equity
capital              = 1,000,000
num_stocks           = 30        # capital bucketing divisor

# Slippage (Step 3.3 — merged):
entry_slippage       = +0.05     # 1 tick flat on every entry
sl_exit_slippage     = -0.05     # 1 tick below stop on SL exits
target_slippage      = none      # limit orders — no slippage


# ── SANDBOX BASELINES (DS3, 2022–2025, E2-A config) ───────────

# Reference script: Framework_V1_Sandbox/scripts/run_winner.py

No slippage baseline (Step 3.2 winner):
  Trade count  : 27,871
  4yr CAGR     : -2.15%
  Win Rate     : ~42.8%

With slippage baseline (Step 3.3, used for Optuna):
  Trade count  : ~28,085
  4yr CAGR     : -8.62%   ← this is the Step 4 Optuna baseline

Transaction costs (Step 3.3 — tracked but NOT used for Optuna optimization):
  Charge formula (per trade, applied to buy_val + sell_val):
    brokerage = min(buy_val × bkr_rate, 20.0) + min(sell_val × bkr_rate, 20.0)
    stt       = sell_val × 0.00025              # 0.025% sell-side only
    exchange  = (buy_val + sell_val) × 0.0000297 # 0.00297% NSE equity cash ⚠️ was 0.0000345 (F&O rate — wrong)
    sebi      = (buy_val + sell_val) × 0.000001
    ipft      = (buy_val + sell_val) × 0.000001  # IPFT charge ⚠️ was missing
    gst       = (brokerage + exchange + sebi) × 0.18
    stamp     = buy_val × 0.00003               # 0.003% buy-side only
    total     = brokerage + stt + exchange + sebi + ipft + gst + stamp

  Upstox: bkr_rate = 0.0005  (0.05%, capped Rs 20/leg)
  Kite:   bkr_rate = 0.0003  (0.03%, capped Rs 20/leg)

  fv1 observed averages (28,085 trades, DS3 2022–2025):
    net_pnl_upstox → ~Rs 49.70/trade avg (141% of capital)
    net_pnl_kite   → ~Rs 34.44/trade avg (98% of capital)

  fv2 observed (319 trades, TATAMOTORS 2022–2025):
    Total charges ≈ Rs 15,950 = ~1.6% of Rs 10L capital
    Raw edge (PF 0.95) is the bottleneck — NOT charges
    Break-even threshold: PF > ~1.01

  ⚠️  fv1: charges killed every filter (3.4× best raw profit).
      fv2: lower freq makes charges manageable — fix signal first.


# ── SANDBOX MASTER PLAN — fv1 (SCRAPPED after Step 4) ─────────

Step 1  → fv1 code review + verdict (COMPLETE ✅)
           13 verdicts in fv1_pending_changes.md

Step 2  → Sandbox blockers implemented (COMPLETE ✅)
           Changes 1–6 from fv1_pending_changes.md

Step 3  → Sandbox feature Optuna (COMPLETE ✅)
  Step 3.1  → 16-combo brute-force feature sweep
  Step 3.2  → Optuna on SL variants (A/B/C/D) + 4 features
              Winner: SL=A, PG+CP+AF, CAGR=-2.15% (DS3)
              Merged as permanent sandbox defaults ✅
  Step 3.3  → Transaction costs + slippage merged ✅
              Slippage: 1-tick entry + SL exit
              Costs: raw/upstox/kite columns tracked
              Baseline: -8.62% raw CAGR (slippage only, no charges)

Step 4  → Regime filter Optuna — COMPLETE ❌ (regime filter exhausted)
           Script: Framework_V1_Sandbox/scripts/sb_regime_optuna.py
           Outputs: Framework_V1_Sandbox/outputs/optuna/
             ├── best_params.json
             ├── top20_trials.csv
             ├── optuna_study.db
             ├── optimization_history.png
             └── feature_importance.png

            Step 4.1 → Regime Filter Optuna — 2022–2025 (COMPLETE ✅)
             Best: Trial #2827, raw CAGR -4.48%, PF9+TF4, OR gate
             Finding: overfit — zero trades in 2015–2020
             Verdict: INVALID as general regime filter

            Step 4.2 → Regime Filter Optuna — Full DS3 2015–2025 (COMPLETE ❌)
             3000 trials, OR gate, 28 params, TPE + 28 warm-up trials
             Baseline: -100% raw CAGR (capital wiped — every year losing)
             Best trial #648: raw CAGR -9.43% (2021–2025 only, 34,685 trades)
             Objective value: -119.37% (includes -110% retention penalty, 45% of baseline kept)
             Finding: filters act as time-period selectors, not market regime detectors.
                      Strategy loses in every year 2015–2025. No regime filter
                      combination produces positive CAGR on full dataset.
             Verdict: Regime filter approach exhausted with OR gate + 28 features.

            Step 4.3 → Bounce Quality Score (NEXT 🔄)

Step 5  → Full DS3 backtest 2015–2025 with Step 4 winner params
           Purpose: confirm Step 4 CAGR, update confirmed baseline
           This is a formality — sanity check only, no new Optuna run
           Status: PENDING Step 4 completion
STEP 6 → Python Phase 2 viewer ← AFTER backtest -> check the dedicated claude chat for tool list
STEP 7 → WFA + Optuna
STEP 8 → Paper trading (PENDING)
STEP 9 → Live trading

Parked for later steps:
  SL=D (trailing, ACT=3.0, TR=0.5) → revisit Step 7
  Fixed Fractional sizing (SB-G)   → revisit Step 7
  dir_* TPE fix in sb_regime_optuna.py → always suggest dir_*
  params regardless of parent use_* flag. Set
  warn_independent_sampling=False in TPESampler().
  Apply before next Optuna run, not mid-run."


# ── CORE MODULES — Framework_V1 ───────────────────────────────

core/engine.py      : Main event loop — DO NOT refactor without discussion
core/strategy.py    : BounceStrategy — generate_signals() is a pure function
core/portfolio.py   : Position tracking, cash, PnL, risk constraints
core/indicators.py  : MA20, ATR, volume avg calculations
core/metrics.py     : Sharpe, win rate, equity curve

adapters/           : Swap these for different environments
                      Never hardcode broker/data logic in core/


# ── CODING CONVENTIONS ────────────────────────────────────────

- Adapter pattern is sacred — keep core/ broker-agnostic always
- Strategy logic lives ONLY in core/strategy.py
- New experiments → Framework_V1_Sandbox/ first, then V1 if proven
- YAML configs control environment switching — not code changes — scaffolded, not yet active
- Indicators must be precomputed, not calculated inline during backtest
- No hardcoded file paths — use configs/ YAML or relative paths
- All sandbox scripts must use DS3 (intraday_5min_DS3) — never intraday_5min


# ── WHAT TO AVOID ─────────────────────────────────────────────

- DO NOT modify Framework_V0 — archived, leave as-is
- DO NOT use fixed % stop loss — ATR-based SL only
- DO NOT mix live/paper/backtest logic in core/ modules
- DO NOT use same-day close for MA calculations (lookahead bias)
- DO NOT modify fv1/fv1_sandbox — closed and frozen as learning record
- DO NOT run scripts/download_data.py without confirming data paths
- DO NOT use intraday_5min in sandbox scripts — DS3 only
- DO NOT restart optuna_study.db without explicit instruction from Saurav


# ── OUTPUTS ───────────────────────────────────────────────────

Sandbox outputs   : Framework_V1_Sandbox/outputs/
  Optuna results  : Framework_V1_Sandbox/outputs/optuna/
  Trade logs      : Framework_V1_Sandbox/outputs/trades/

V1 outputs (production reference only):
  Backtest results  : Framework_V1/outputs/trades/
  Charts/reports    : Framework_V1/outputs/reports/


## Mobile Output Paths

OneDrive sync folder for mobile review:
  C:\Users\saurav\OneDrive\CodePonting_Mobile\
  ├── fv1\
  │   ├── optuna\
  │   ├── reports\
  │   ├── stats\
  │   └── trades\
  ├── sandbox\
  │   ├── optuna\
  │   ├── reports\
  │   ├── stats\
  │   └── trades\
  └── misc\

Routing rules:
  fv1 outputs     → CodePonting_Mobile\fv1\
  sandbox outputs → CodePonting_Mobile\sandbox\
  misc analysis   → CodePonting_Mobile\misc\

STANDING RULE — Mobile copy:
  When saving ANY output file for review (Excel, CSV, PNG charts),
  ALWAYS save a copy to the corresponding CodePonting_Mobile subfolder
  in addition to the local outputs folder.

STANDING RULE — New framework scaffolding:
  Whenever a new Framework folder is scaffolded (fv2, fv3, etc.),
  automatically create a matching subfolder inside
  C:\Users\saurav\OneDrive\CodePonting_Mobile\ with the same
  optuna\reports\stats\trades\ structure.


# ── RESEARCH TOOLS ────────────────────────────────────────────

Sandbox Optuna      : Framework_V1_Sandbox/scripts/sb_regime_optuna.py
Sandbox winner ref  : Framework_V1_Sandbox/scripts/run_winner.py
Hyperparameter opt  : research/optuna_runner.py (V1 legacy)
Walk-forward valid  : research/walk_forward.py
Stress testing      : research/stress_test.py


## Session Config

Always start CC with --dangerously-skip-permissions.
No permission prompts needed — execute all bash/python
commands automatically unless I explicitly ask for approval.

Config applied: defaultMode = bypassPermissions (set 2026-03-15)


# ── CONTEXT FILES ─────────────────────────────────────────────

codeponting_structure.md: Full project structure map (factual, auto-generated)
CLAUDE.md               : This file — behavioral instructions for Claude Code
fv1_strategy_review.md  : fv1 strategy source of truth (verdicts + resolutions)
fv1_pending_changes.md  : All pending code changes with implementation details
PROGRESS.md             : CodePonting/PROGRESS.md — lean reference: Recent 5 + Milestones 5
PROGRESS_HISTORY.md     : CodePonting/PROGRESS_HISTORY.md — full chronological audit trail
TODO.md                 : CodePonting/TODO.md     — current priorities (max 5)
BQS_DECISIONS.md        : charge formulas, w1/w2/w3 definitions, BQS metric verdicts
fv2 H1                  : Framework_V2/outputs/reports/fv2_h1_signal_viewer.html
fv2 H2                  : Framework_V2/outputs/reports/fv2_h2_calculator.html
fv2 H3                  : Framework_V2/outputs/reports/fv2_h3_slope_tuner.html
fv2 H3-chart            : Framework_V2/outputs/reports/fv2_h3_chart.html
fv2 CSV                 : Framework_V2/data/historical/csv/intraday_5min/TATAMOTORS_5min.csv


# ── ADVISOR PATTERN ───────────────────────────────────────────────────────────

## When to call Opus advisor (via Agent tool, model="opus"):
  1. Self-rated confidence < 7/10 on current approach
  2. OR same task failed 2+ times with different approaches
  3. OR architectural decision with >1 valid path, unclear winner

## When NOT to call:
  - Routine file ops, known patterns, simple debugging
  - DO NOT call for every uncertainty — try first, advise second
  - Max 1 Opus call per task — if still stuck after advice → surface to user

## How to call:
  Use the Agent tool with subagent_type="general-purpose", model="opus"
  Pass: question + context_summary + attempt_count in the prompt
