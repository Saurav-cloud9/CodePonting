# CLAUDE.md — CodePonting Behavioral Instructions

> HOW to behave in this project. For project structure/map → see MEMORY.md
> Last updated: 2026-06-08 | fv2 active — 3-gate MA bounce redesign in Algo_Trading/Framework_V2/

── SHORTHAND ────────────────────────────────────────────────────

  vsa = "very short answer" — reply in 1–2 lines max, no elaboration
  lm  = "learning mode" — explain concepts directly, no solution code. Let user write the code himself.
  ivb = initialize voice bridge — execute /ivb command immediately, no confirmation needed.
  kbccp = CCP scoped to kite_oracle_papertrading only: read its PROGRESS.md (VM,
          read-only) and give the 3-part CCP summary (where we are/next/blockers)
  kbss  = SS scoped to kite_oracle_papertrading only: update its PROGRESS.md (VM)
          with what happened, and sync any live-file code changes back to the local
          CodePonting copy (source of truth) in the same pass

── RESPONSE FORMATTING ──────────────────────────────────────────

  Default to bullet-point format for assessments, reviews, and multi-point
  analysis (e.g. reviewing a document/recommendation, summarizing findings,
  giving feedback on a plan) — one point per line, bolded lead-in where useful
  — rather than flowing paragraphs. Easier to scan and reference back to.
  Plain prose is still fine for short answers, direct questions, or single-point
  replies — this applies specifically to multi-point breakdowns.

── KITE BOT: LOCAL↔VM SYNC ────────────────────────────────────────

  kite_oracle_papertrading/ scripts exist on both local (source of truth) and the
  VM (where the bot actually runs). VM CC and this session both edit them independently.

  HARD RULE: never push a local script change to the VM (scp) without confirming
  with Saurav first — every time, not just when a diff shows a conflict. Show what
  changed and what will be pushed, then wait for explicit go-ahead before running
  the scp. Same applies in reverse (pulling VM's copy down to local).
  Always report a conflict (local/VM diverged) the moment it's detected, regardless
  of whether a sync was requested — don't wait to be asked.

  Why: happened for real on 2026-07-28 — pushed a local edit (on_reconnect fix)
  without first pulling VM CC's already-applied pending_entry persistence fix,
  silently overwriting and losing it. Caught only because VM CC noticed and asked.

── VOICE BRIDGE ─────────────────────────────────────────────────

  Activation : type "ivb" → CC executes /ivb immediately, no confirmation.

  /ivb does TWO things:
    1. Start a persistent Monitor on Algo_Trading/voice_bridge/instructions.txt
       (polls every 1s, fires when content appears)
    2. Print "Voice Bridge active." confirmation

  Execution rule (when Monitor fires):
    - Treat the instruction exactly like Saurav typed it in the console
    - Execute using CC tools, show output clearly in the conversation
    - Clear instructions.txt (write empty string)
    - Write "done" to instructions_executed.txt

  IMPORTANT — after every session resume, the Monitor does NOT survive.
  Re-arm it by running ivb again before expecting instructions.

  MCP server  : Algo_Trading/voice_bridge/voice_bridge_mcp.py
  Instruction file : Algo_Trading/voice_bridge/instructions.txt
  Done signal : Algo_Trading/voice_bridge/instructions_executed.txt
  No claude -p. No subprocess. This CC session IS the executor.

  Kite MCP approval rule:
    - ALWAYS display the instruction and wait for Saurav's explicit approval
      before executing ANY Kite-related Voice Bridge instruction.
    - Approval bypass: only if Saurav explicitly says "bypass approvals" within
      the current session. This does NOT carry over to the next session —
      every new session starts with approvals required by default.

── ABBREVIATION RULES ───────────────────────────────────────────

  1. First use in any session: spell out in full, short form in brackets.
     Example: "Position Guard (PG)", "touch-to-bounce gap (tb_gap)"
  2. Preferred short forms are defined in TODO.md → GLOSSARY section.
     Use those — do not invent new ones without adding them to the glossary.
  3. When a new abbreviation is introduced (in replies, logs, or code),
     add it to the TODO.md glossary immediately — same turn, no batching.
  4. Generic single-letter variables (k, x, n) are banned for domain
     concepts. Use descriptive short forms (tb_gap, not k).

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
  - Never use `claude -p` or any API-billed command without explicit instruction from Saurav.
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
    5. Update TODO.md (max 5 items, P1 priority first)
    6. Append to PROGRESS_HISTORY.md (never delete existing entries)
    All six are MANDATORY. Without them, next session starts with no context.
    Files: C:\Users\Saurav\CodePonting\.remember\
      today.md   → session log (what was done, key findings)
      handoff.md → current task status, next step, blockers


## Progress & Context Management Protocol

  ### End of Claude.ai session (Saurav → CC):
  - Claude.ai provides PROGRESS.md one-liners + TODO.md updates
  - CC updates PROGRESS_HISTORY.md (full audit trail, never deleted)
  - CC updates TODO.md (max 5 items, P1 priority first)

  ### When Saurav types "SS" (Save State):
  - CC updates PROGRESS.md (Recent 5 steps + 5 Milestones)
  - CC updates .remember/handoff.md + today.md
  - CC updates TODO.md (max 5 items, P1 priority first)
  - CC appends to PROGRESS_HISTORY.md (never delete existing entries)
  - CC calls /remember:remember to save state

  ### When Saurav types "CCP" (Context Catch-Up / Peek):
  - Read these files in order:
      SS-triggered (8):
        1. .remember/remember.md
        2. .remember/handoff.md
        3. .remember/today.md
        4. .remember/weekly.md
        5. PROGRESS.md
        6. PROGRESS_HISTORY.md
        7. TODO.md
        8. _explore/p5_cc_source_exploration.md (only if CC tooling work is in scope)
      Auto-memory (always live):
        9. memory/MEMORY.md
       10. memory/ linked files (project_*, feedback_*, etc.)
  - Reply with a 3-part summary: (1) where we are, (2) what's next, (3) any blockers
  - No file writes. Read-only. Fast.
  - Note: Claude.ai uses CCP to read CC memory via cc-memory MCP tools — same spirit, different mechanism.

  ### When Saurav types "SSD" (Save State + Drive):
  - Everything SS does, PLUS syncs all 4 .remember/ files to Google Drive
    CodePonting/.remember/ folder

  ### Files and their purpose:
  - PROGRESS_HISTORY.md → full chronological audit trail (CC writes)
  - PROGRESS.md         → lean reference: Recent 5 + Milestones 5 (SS trigger)
  - TODO.md             → current priorities max 5 items (CC maintains)
  - .remember/          → CC memory for CCP (SS trigger)


## ── PYTHON LEARNING JOURNEY ──────────────────────────────────

Saurav learns Python via structured platforms alongside CodePonting work.
Past: Codecombat | Current: Codedex | Next: RealPython.com
CC assists during learning sessions — explain concepts directly, no Socratic loops.
"Learning mode" = no solution code. Explain the concept, let Saurav write the code.
"Reply freely" = same rule, just more conversational tone.


## ── WHO I AM ──────────────────────────────────────────────────

Project    : CodePonting — Algorithmic Trading System
Owner      : Saurav
Domain     : NSE F&O Equity Markets (India)
Language   : Python
IDE        : VS Code (Claude Code as agentic execution layer)
Brokers    : Kotak Neo (primary) · Zerodha Kite (future scaling, post live validation)
             Note: Upstox excluded (0.1%/side brokerage, 2× Kotak).
                   Zerodha cheaper per trade (0.03%) but ₹2,000/month API fee —
                   switch to Zerodha when live trade volume justifies the fixed cost.


## ── FRAMEWORK STATUS — CRITICAL ───────────────────────────────

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
                 Signal redesign underway. 3-gate system (G1/G2/G3) addressing
                 structural gaps vs true MA bounce. Raw edge is the target.
                 Data: Framework_V2/data/historical/csv/intraday_5min/
                 Outputs: Framework_V2/outputs/reports/
                 Universe: 30 stocks (29 DS3 + BAJFINANCE via Kite MCP). All CSVs built.

Framework_V1_Sandbox → CLOSED alongside fv1.
                        All BQS/DT/RF experiments complete and documented.
                        Read-only reference. Do not run new experiments here.


## ── ACTIVE STRATEGY — MA Bounce (fv2) ─────────────────────────

Status      : REDESIGN IN PROGRESS
              fv1 was a proximity detector, NOT a true MA bounce.
              Opus review identified gaps → restructured into 3 temporal gates:
                G1 — Pre-touch  : trend context + approach direction
                G2 — Touch & bounce : pullback quality + volume signature
                G3 — Post-bounce : follow-through confirmation

fv2 Signal  : True MA bounce — 6 classic bounce criteria
              TATAMOTORS 5-min (2022–2025) as development stock
              Gap 1 result: CAGR -172% → -2.07%, PF 0.77 → 0.95
              Next: close raw edge gap (PF 0.95 → >1.01)

fv1 Signal  : CLOSED — archived for reference
              SL=A, PG+CP+AF, CAGR=-2.15% (no slippage baseline)
              With slippage: -8.62%. After charges: net negative all filters.


## ── DATA ARCHITECTURE ─────────────────────────────────────────

PRIMARY (fv2)      : Framework_V2/data/historical/csv/intraday_5min/
  fv2 CSV dataset    TATAMOTORS_5min.csv — 73,174 rows, 7 cols + outcome cols
                     Columns: signal_type, exit_reason, raw_pnl, win
                     Coverage: 2022–2025 (4 years) — ARCHIVED, see note below.
                     ⚠️  DS3 inside fv2 is the default historical dataset for
                         our projects as of now, no exceptions. This fv2 CSV
                         set is retired; these CSVs can be archived.

PRIMARY (fv2 DS3)  : Framework_V2/data/historical/intraday_5min_DS3/
  DS3 dataset        Parquet format, 30 stocks, ma20/atr14 precomputed
                     Coverage: 2015–2025 (11 years)
                     Daily NIFTY50: Framework_V2/data/historical/daily/NIFTY50.parquet
                     (2016-01-01 → present, ~10.5yr — Kite's day-candle lookback limit)
                     ⚠️  ALL sandbox scripts must use DS3. Not intraday_5min.

ARCHIVED (fv1 DS3) : Framework_V1/data/historical/intraday_5min_archived/
                     Older duplicate copy (raw OHLCV only, no ma20/atr14) —
                     renamed from intraday_5min_DS3 to mark it archived.
                     Superseded by the fv2 DS3 copy above — do not reference
                     for new work.

Legacy dataset     : Framework_V1/data/historical/intraday_5min/
                     30 stocks · Coverage: 2022–2025
                     ⚠️  DO NOT use for sandbox work. Migrated to DS3.

Daily candles      : Framework_V1/data/historical/daily/

Indicators         : Framework_V1/data/indicators/
                     Precomputed: MA20, ATR, Volume MA
                     Regenerate via: scripts/compute-indicators.py

Kaggle data        : Algo_Trading/Kaggle/
                     Used for validation only (NOT primary source)


## ── SANDBOX CONFIG — CONFIRMED WINNER (Step 3.2) ──────────────

Locked-in sandbox defaults. Do NOT change without instruction.

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

Slippage (Step 3.3 — merged):
entry_slippage       = +0.05     # 1 tick flat on every entry
sl_exit_slippage     = -0.05     # 1 tick below stop on SL exits
target_slippage      = none      # limit orders — no slippage


## ── SANDBOX BASELINES (DS3, 2022–2025, E2-A config) ───────────

Reference script: `Framework_V1_Sandbox/scripts/run_winner.py`

No slippage baseline (Step 3.2 winner):
  Trade count  : 27,871
  4yr CAGR     : -2.15%
  Win Rate     : ~42.8%

With slippage baseline (Step 3.3, used for Optuna):
  Trade count  : ~28,085
  4yr CAGR     : -8.62%   ← this is the Step 4 Optuna baseline

Transaction costs (Step 3.3): full formula → [guides/transaction_costs.md](guides/transaction_costs.md)
  ⚠️  fv1: charges = 3.4× best raw profit — killed every filter.
      fv2: charges ≈ Rs 15,950 total (~1.6% of 10L) — manageable. Fix signal first.
      Break-even: PF > ~1.01

## ── NPF — Neo Profit Factor (Kotak Neo) ──────────────────────
NPF = real-world PF after full Kotak Neo intraday charges (qty=1).
TV simulates brokerage only (0.05%/side). NPF adds statutory charges on top.

Per-trade cost formula (at ~900 INR price ≈ ₹1.38 total):
  brok  = (entry + exit) × 0.0005      # 0.05%/side — TV simulates this
  stt   = exit  × 0.00025              # sell side only
  txn   = (entry + exit) × 0.0000297   # on turnover
  sebi  = (entry + exit) × 0.000001    # on turnover
  stamp = entry × 0.00003              # buy side only
  gst   = 0.18 × (brok + txn)
  total = brok + stt + txn + sebi + stamp + gst

PF hierarchy:
  PF  = raw profit factor (Python backtest, zero charges)
  TPF = TradingView PF   (brokerage only, 0.05%/side — understates real cost)
  NPF = Neo Profit Factor (full Kotak Neo charges: brokerage + statutory)

Rule of thumb : NPF ≈ PF − 0.3 to 0.4  (at NSE intraday ~900 INR price range)
Primary target: PF ≥ 1.5 → NPF ≈ 1.1–1.2  (comfortably profitable after all charges)
Reference     : HDFCBANK v1.1, 91 trades Jun2025–Jun2026: PF=1.267 → TPF=0.794 → NPF=0.626
                v1.1 30-stock 2022-2025:                PF=1.010 → NPF=0.588


## ── SANDBOX MASTER PLAN — fv1 (SCRAPPED after Step 4) ─────────
Full step history + parked items → [[sandbox_master_plan]]

Steps 1–4 : COMPLETE / EXHAUSTED (fv1 closed — regime filter found no edge)
Step 4.3   : Bounce Quality Score — NEXT 🔄
Step 5     : Full DS3 backtest 2015–2025 — PENDING
Steps 6–9  : Phase 2 viewer → WFA+Optuna → Paper → Live


## ── CORE MODULES — Framework_V1 ───────────────────────────────

core/engine.py      : Main event loop — DO NOT refactor without discussion
core/strategy.py    : BounceStrategy — generate_signals() is a pure function
core/portfolio.py   : Position tracking, cash, PnL, risk constraints
core/indicators.py  : MA20, ATR, volume avg calculations
core/metrics.py     : Sharpe, win rate, equity curve

adapters/           : Swap these for different environments
                      Never hardcode broker/data logic in core/


## ── CODING CONVENTIONS ────────────────────────────────────────

- Adapter pattern is sacred — keep core/ broker-agnostic always
- Strategy logic lives ONLY in core/strategy.py
- New experiments → Framework_V1_Sandbox/ first, then V1 if proven
- YAML configs control environment switching — not code changes — scaffolded, not yet active
- Indicators must be precomputed, not calculated inline during backtest
- No hardcoded file paths — use configs/ YAML or relative paths
- All sandbox scripts must use DS3 (intraday_5min_DS3) — never intraday_5min
- All matplotlib charts use dark mode: `plt.style.use('dark_background')` at the top of every plot block
- Multi-script pipelines/experiments (e.g. a numbered sequence of exploratory or trial scripts within a folder) use zero-padded numeric prefixes for ordering: `01_build_trade_log.py`, `02_bucket_by_feature.py`, ... `09_...`, `10_...`. Keeps run order unambiguous and sorts correctly in a file listing regardless of count.


## ── WHAT TO AVOID ─────────────────────────────────────────────

- DO NOT modify Framework_V0 — archived, leave as-is
- DO NOT TOUCH Framework_V2/baseline_reserve/ unless explicitly asked by Saurav
- DO NOT use fixed % stop loss — ATR-based SL only
- DO NOT mix live/paper/backtest logic in core/ modules
- DO NOT use same-day close for MA calculations (lookahead bias)
- DO NOT modify fv1/fv1_sandbox — closed and frozen as learning record
- DO NOT run scripts/download_data.py without confirming data paths
- DO NOT use intraday_5min in sandbox scripts — DS3 only
- DO NOT restart optuna_study.db without explicit instruction from Saurav

## ── SURGICAL EDIT RULE (fv2 HTML + Pine Script) ───────────────
Applies to ALL files in fv2 signal viewer (HTML/Python) and ALL Pine Script files on TradingView.

Before editing any such file:
  1. Read the task carefully
  2. Identify the MINIMUM lines/functions that need to change
  3. Modify ONLY those — nothing else

Do NOT:
  - Refactor or restructure existing code
  - Rename variables or functions
  - Remove any existing feature or block
  - "Clean up" anything not mentioned in the task
  - Overwrite or modify h1_extensions.js unless explicitly instructed
  - Remove the <script src="h1_extensions.js"> tag from build_html1.py

If the fix requires changes beyond the stated scope:
  STOP → list what needs to change and why → wait for approval

After every edit, confirm:
  ✅ What was changed
  ✅ What was deliberately left untouched

## ── H1.1 CONTRACT RULES ────────────────────────────────────────
H1.1 (fv2_h1_1_signal_review.html) is a static file that receives signal data from build_html1.py via openReview(). The two files are coupled — changes to one can silently break the other.

**CC RULE** — before saving any edit to openReview() in build_html1.py:
  Check the H1.1 contract comment (above the signal object in openReview())
  and verify every field listed there is still present in the signal object.
  If a field is missing → stop and restore it before proceeding.

**SMOKE TEST RULE** — after any H1 rebuild:
  Open H1.1 on one k=0 signal and one k>0 signal and confirm:
  - \#01 shows a slope value (not "—%")
  - \#02 shows a slope value (not "N/A", unless touch is in first 3 bars of day)
  - \#09/\#10 show "N/A / Yes" for k=0, and actual ratio / "No" for k>0
  Takes 30 seconds. Catches any silent regression before signal review continues.


## ── OUTPUTS ───────────────────────────────────────────────────

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

STANDING RULE — Mobile copy: [DISABLED — re-enable when Saurav asks]
  When saving ANY output file for review (Excel, CSV, PNG charts),
  ALWAYS save a copy to the corresponding CodePonting_Mobile subfolder
  in addition to the local outputs folder.

STANDING RULE — New framework scaffolding: [DISABLED — re-enable when Saurav asks]
  Whenever a new Framework folder is scaffolded (fv2, fv3, etc.),
  automatically create a matching subfolder inside
  C:\Users\saurav\OneDrive\CodePonting_Mobile\ with the same
  optuna\reports\stats\trades\ structure.


## ── RESEARCH TOOLS ────────────────────────────────────────────

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


## ── CONTEXT FILES ─────────────────────────────────────────────

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


## ── GUIDES ────────────────────────────────────────────────────
Detailed reference docs. Read on demand — not loaded every session.

## What belongs in CLAUDE.md vs. guides/

| Stays in CLAUDE.md | Goes to guides/ |
|---|---|
| Behavioral rules (protocols, conventions, what to avoid) | Step-by-step setup instructions |
| Active config values needed when writing scripts | Historical logs and completed step records |
| Framework status (active/closed/archived) | Detailed formulas or code blocks (VBA, charge math) |
| Critical paths Claude must follow automatically | Side projects, hackathon ideas, future skill entries |
| Shorthand, abbreviations, clarification rules | Bug fix logs and one-time setup notes |

**Rule:** If removing it from CLAUDE.md would change how CC behaves → it stays.
If it's reference material CC only needs when pointed at it → it goes to guides/.
When in doubt: one-line summary + link in CLAUDE.md, full detail in guides/.

---

Excel Dark Mode Setup   : [[excel_dark_mode_setup]]
Transaction Costs       : [[transaction_costs]]
Sandbox Master Plan     : [[sandbox_master_plan]]
CC Remote Setup         : [[cc_remote_setup]]
Hackathon Ideas         : [[hackathon_ideas]]
Future Skills           : [[future_skills]]
Backtesting Rules       : Algo_Trading/Framework_V2/backtesting_rules.md — EOD exit logic, ATR14 SL/TP convention, NPF formula. Read before writing any fv2 backtest script.


## ── ADVISOR PATTERN ───────────────────────────────────────────────────────────

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


## ── FUTURE SKILLS & PLATFORM UPDATES ─────────────────────────
Full entries → [[future_skills]]

**FLAG RULE:** When the current task matches a "Flag at" step in the guide, print:
`⚑ FUTURE SKILL READY: <feature name> — <one-line reminder>`
Then ask Saurav if he wants to explore it before continuing.


## ── HACKATHON IDEAS ───────────────────────────────────────────────────────────
Side quests — revisit when fv2 signal is stable. Full details → [[hackathon_ideas]]

NSE Signal Dashboard (2026-04-22) — CC + Opus 4.7 + Claude Design.
Explainable G1-G3 signal screener for 29 NSE stocks. Post-fv2 stable.


## ── CC REMOTE SETUP ───────────────────────────────────────────
Full setup + bug fix log → [[cc_remote_setup]]
Status: configured and working (fixed 2026-05-06). Auto-launches on Windows startup.
