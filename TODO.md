# TODO.md — CodePonting fv2
# Max 5 items at any time. Always prioritized P1→P5.
# Update: replace completed items, add new ones at bottom.
# When done → move to PROGRESS.md as one line, delete from here.
# ─────────────────────────────────────────────────────────────

P1  Complete H5 Lite on claude.ai — chart refinement (T0/BNC/ENT labels, MA20/SL/TGT)
        CSVs: Framework_V2/outputs/h5/powergrid_2022_h5_signals.csv + candles.csv

P2  Build H5 full (Python build script + HTML viewer, 30 stocks) — after lite validated
        Spec: Algo_Trading/Framework_V2/docs/fv2_params.md

P3  Optuna joint sweep — all 12 params, maximise PF_test

P4  Opening bar framework — 9:15 signals need separate G1 evaluation (3/4 params
        structurally N/A). Collect more data points before designing. Seen: #5, #21.

# ── PARKED / FUTURE ───────────────────────────────────────────
F0  Explore "Claude-in-Claude" Artifacts — paste raw OHLCV into React artifact,
    Claude API analyses signal quality + gate status + gives H1 verdict.
    Zero backend, runs in browser. Ref: Anthropic API in Artifacts (claude-sonnet-4-20250514)

F1  CC source code exploration
F2  GCP OAuth → SSD Google Drive sync
F3  H2: per-stock comparison table
F4  Signal replacement / position upgrade logic (post-WFA)
F5  Oct 2022 per-stock WR% → contrast stock
F6  YouTube Strategy Scanner (post paper-trading)
F7  H1 bar replay mode
F8  Insurance review
F9  Add and manage MCP servers in VS Code
F10 Stock mock + algo test — paper run on equity cash with full algo execution
    Revisit before F&O go-live (post Step 8 paper trading)
F11 Checkout VSCode Agent
F12 TradingView AI Chart Copilot — explore when Pine dev resumes

# ── GLOSSARY ──────────────────────────────────────────────────
# Keep this updated. Rule: any new abbreviation used in replies,
# logs, or code must be added here before or on first use.

## Signal Geometry
# T0          — touch bar: candle where price touches MA20
# T-n         — n bars before T0 (e.g. T-3 = 3 bars before touch)
# tb_gap      — touch-to-bounce gap: bars between T0 and bounce bar (replaces k)
# diff        — bars between bounce bar and entry bar

## Gates & Params
# G1          — Gate 1: pre-touch regime check (slope, approach direction, pullback)
# G2          — Gate 2: touch & bounce quality (depth, body, wick, volume)
# G3          — Gate 3: post-bounce follow-through (entry close, entry volume)

# slope_threshold   — G1 #01: MA20 slope at T0 > 0.05%
# slope_offset      — G1 #02: MA20 slope at T0-3 > 0.05%
# candles_above     — G1 #03: ≥1 consecutive low > MA20 before T0
# pullback_bars     — G1 #04: bars from swing high to T0 (pass: 3–8)

# shoot_depth       — G2 #05: how far price pierced below MA20 at touch
# touch_body_pct    — G2 #06: touch candle body as % of candle range
# wick_defence_ratio— G2 #07: lower wick recovery ratio at touch
# bounce_vr_abs     — G2 #08: bounce candle volume ratio vs vol_ma20
# bounce_vr_rel     — G2 #09: bounce candle VR relative to touch candle VR
# same_candle_tb    — observation column (not a gate param): touch and bounce in same candle (tb_gap = 0)

# G3a / G3b         — G3 #10/#11: entry close > bounce close / entry VR holds

## Metrics & System
# vr          — volume ratio: bar volume ÷ vol_ma20
# vol_ma20    — 20-period average volume
# MA20        — 20-period simple moving average of close
# ATR         — average true range
# PF          — profit factor (gross profit ÷ gross loss)
# WR          — win rate
# CAGR        — compound annual growth rate
# PG          — position guard: max 1 open trade per stock at a time
# SL          — stop loss
# TGT         — price target
# EOD         — end-of-day forced exit at 14:50

## Outcomes
# Win         — target hit before 14:50
# EOD+        — exit at 14:50, in profit
# EOD-        — exit at 14:50, at loss
# LATE        — entry ≥ 14:45 (auto-flagged)

## Frameworks & Data
# fv1 / fv2   — Framework V1 (closed) / Framework V2 (active)
# DS3         — Dataset 3: primary 2015–2025 parquet data (29 stocks)
# BQS         — Bounce Quality Score (fv1 analysis metric)
# H1/H2/H3/H5 — fv2 HTML viewers (signal / calculator / slope tuner / gate tuner)
