# fv2 Baseline v2 Formula

## Signal — MA Rejection (SHORT)

Structural redesign from v1.x (long bounce) → v2 (short rejection).
The MA rejection candle fires when price rises to touch MA20 from below but closes back below it.

```
high  >= MA20   # touched MA from below
open  <  MA20   # opened below MA (price approaching from below)
close <  MA20   # rejected — closed back below MA
```

Entry: next bar open (SHORT)
SL:    entry + 2.0 × ATR14  (above entry)
TP:   entry − 3.5 × ATR14  (below entry)

## Why v2 (not v1.2 or filter extension)

- Long baseline (v1.x) best PF = 0.922 raw, reached 1.032 only after 3 filters
- Short baseline starts at PF = 1.076 with zero filters
- Different signal universe, opposite direction — structural redesign, not a tweak

## Results — 30 stocks, 2022-2025, position guard

| Year | N      | PF    | Sharpe | WR%  |
|------|--------|-------|--------|------|
| 2022 | 10,569 | 1.063 | 0.710  | 43.4% |
| 2023 | 10,417 | 0.999 | -0.010 | 41.9% |
| 2024 | 10,599 | 1.123 | 1.405  | 46.2% |
| 2025 | 11,027 | 1.093 | 0.943  | 43.2% |
| ALL  | 42,612 | 1.076 | 0.833  | 43.7% |

Best combo: SL=2.0x, TP=3.5x (from SL×TP grid sweep)

## CBQ (Charge Break-even Qty)

| Qty  | NPF   | Net PnL     |
|------|-------|-------------|
| 1    | 0.559 | -₹46,802    |
| 100  | 0.750 | -₹22,72,667 |
| 1000 | 0.898 | -₹84,01,265 |

NPF never crosses 1.0 — same structural charge problem as v1.x long.
Fix signal edge first (target PF > 1.3) before revisiting CBQ.

## vs Long Baseline (same SL=2.0x, TP=3.5x)

| | Long | Short |
|---|---|---|
| Overall PF | 0.922 | 1.076 |
| Sharpe | -0.918 | 0.833 |
| All years > 1.0 | ❌ | ✅ (2023 ≈ 0.999) |

## Next steps — v2 filter build

Apply mirror of v1.x filter progression to short side:
- v2.1: Wick-only — open > MA20 at signal bar (price must approach from above)
- v2.2: VWAP filter — close below VWAP (below-VWAP rejection stronger)
- v2.3: EMA filter — close above EMA100 (price in longer-term downtrend context)

## Files

Script : `Framework_V2/core/pine/fv2_baseline_v2.pine`
Python : `Framework_V2/scripts/baseline_short_sweep.py`
CBQ    : `Framework_V2/scripts/baseline_short_cbq.py`
Heatmap: `Framework_V2/outputs/reports/screenshots/baseline_short_sl_tp_heatmap.png`
