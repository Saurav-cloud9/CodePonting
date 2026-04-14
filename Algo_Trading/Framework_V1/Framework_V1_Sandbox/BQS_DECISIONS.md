# BQS_DECISIONS.md — Bounce Quality Score Decision Log
# ══════════════════════════════════════════════════════════════
# Source of truth for BQS definitions, verdicts, and R2 status
# Last updated: 2026-03-20
# ══════════════════════════════════════════════════════════════


## DATASET

DS3 2022–2025 | 28,085 trades | SL=A config | Baseline CAGR -8.62% (with slippage)


## WINNER DEFINITIONS

w1 = exit_reason == "target"
     → 4,163 trades (14.8%)
     → Used as `winner` column in bqs_trades.parquet
     → NOTE: winner col also includes EOD exits where pnl > 0.5 × risk_amt,
       but per session validation all EOD exits fall below this threshold,
       so winner == w1 in practice.

w2 = raw pnl > Upstox round-trip charges (net_pnl_upstox > 0)
     → 9,128 trades (32.5%)
     → NOT in current bqs_trades.parquet — requires charge columns

w3 = raw pnl > Kite round-trip charges (net_pnl_kite > 0)
     → 9,904 trades (35.3%)
     → NOT in current bqs_trades.parquet — requires charge columns


## CHARGE FORMULAS (source: core/portfolio.py → _compute_charges)

Round-trip NSE equity intraday charges:

  buy_val   = entry_price × qty
  sell_val  = exit_price  × qty

  brokerage = min(buy_val × bkr_rate, 20.0) + min(sell_val × bkr_rate, 20.0)
  stt       = sell_val × 0.00025                   # 0.025% sell-side only
  exchange  = (buy_val + sell_val) × 0.0000345     # 0.00345% per side
  sebi      = (buy_val + sell_val) × 0.000001      # 0.0001% per side
  gst       = (brokerage + exchange + sebi) × 0.18 # 18% on fees
  stamp     = buy_val × 0.00003                    # 0.003% buy-side only

  total_charges = brokerage + stt + exchange + sebi + gst + stamp

Upstox: bkr_rate = 0.0005 (0.05%, capped Rs 20 per leg)
Kite:   bkr_rate = 0.0003 (0.03%, capped Rs 20 per leg)


## STAR BUCKET DEFINITION

Target: a single filter bucket that captures 70%+ of winners
        with clear W vs L separation vs the baseline (14.8%)
Goal:   identify the "good trade" zone, not recover all 9,128


## BQS-R1 VERDICTS (DS3 2022–2025, w1 only)

M1  volume_ratio        → WEAK      | gap +0.071, high std — no actionable pattern
M2  bounce_strength_pct → WEAK      | direction REVERSED — lower = better (tiny gradient)
M3  wick_ratio          → EXCLUDE   | std=3.7–4.4, zero predictive value
M4  candle_color        → EXCLUDE   | 87% bullish for both W and L — zero filtering value
M5  hours_until_close   → MODERATE  | sweet spot 3–5hrs, killer bucket 1–2hrs (7.55%)
                                       use as exclusion filter (drop last 2hrs), not scorer
M6  touch_candle_index  → MODERATE  | earlier = better, correlated with M5
                                       validate independence before assigning full weight
M7  bounce_gap          → EXCLUDE   | win rate range 1.74pp — not actionable
M8  ma20_distance_pct   → WEAK      | 96% trades in <0.3% bucket — weak standalone filter
M9  prev_candle_dir     → EXCLUDE   | 0.0pp gap — completely uninformative


## BQS-R2 STATUS

New metrics under investigation (hypotheses defined, validation pending):

M10 MA20 slope at touch  → hypothesis: rising slope = better bounce quality
                            math: slope = (MA20[touch_idx] - MA20[touch_idx-5]) / price × 100
                            categories: rising >+0.05% | flat ±0.05% | falling <-0.05%
                            CC validation: PENDING (R2 M1 task)

M11 RSI at touch         → PENDING
M12 MA Freshness         → PENDING
M13–M19                  → PENDING


## SESSION WORKFLOW

Visual → Hypothesis → Math Mode → CC Validation


## KEY FILE PATHS

bqs_trades.parquet : Framework_V1_Sandbox/outputs/bqs/bqs_trades.parquet
bqs_export.py      : Framework_V1_Sandbox/scripts/bqs_export.py
charge formula     : Framework_V1_Sandbox/core/portfolio.py → _compute_charges()
DS3 data           : Framework_V1/data/historical/intraday_5min_DS3/


## KNOWN GAPS IN CURRENT PARQUET

1. touch_idx dropped at export (bqs_export.py line 407: drop touch_idx, bounce_idx)
   → needed for R2 MA slope analysis — must re-export or compute slope during export
2. No charge columns (net_pnl_upstox, net_pnl_kite)
   → needed for w2/w3 winner definitions
   → current parquet supports w1 analysis only
