# fv2 Baseline Formula — MA Bounce Strategy

**Script:** `Framework_V2/scripts/trials/ma_bounce.py`
**Data:** 30 stocks | 2022–2025 | 5-min bars | fv2 CSVs
**Locked:** 2026-06-26

---

## Signal Logic

| Step | Rule |
|---|---|
| Touch | `low <= MA20` on any bar |
| Touch cutoff | Skip if `hour >= 15` |
| Bounce | `close > MA20` within 3 bars of touch, same day, `hour < 15` |
| Entry | Next bar open after bounce bar |
| Entry guard | Skip if entry bar is next day |
| Stop Loss | `entry - 2.5 × ATR14` |
| Target | `entry + 4.5 × ATR14` |
| EOD exit | Exit at open of first bar where `hour >= 15` |
| Exit order | EOD checked first, then TP, then SL |
| Position guard | `i = k + 1` — no new trade until current trade exits |

---

## Config

| Param | Value |
|---|---|
| MA | MA20 (simple moving average, 20 bars) |
| ATR | ATR14 (precomputed, DS3 warm-up, saved in fv2 CSV) |
| SL multiplier | 2.5 |
| TP multiplier | 4.5 |
| Max bounce window | 3 bars |
| EOD hard stop | 15:00 bar open |
| Slippage | None |
| Charges | None |
| Capital | Not applied (raw points) |

---

## Aggregate Results

| Metric | Value |
|---|---|
| Total Trades (N) | 49,039 |
| Prof WR | 41.5% |
| BE prof | 44.3% |
| Pure WR (TP hits only) | 15.0% |
| BE pure | 35.7% |
| Profit Factor | 0.922 |
| Net PnL (raw ATR points) | -8,573 |

---

## Per-Stock Results

See `outputs/reports/baseline_summary.csv` for full table.

Profitable stocks (PF > 1.0, ranked): BHARTIARTL (1.092) > ASHOKLEY (1.054) > DABUR (1.023) > SUNPHARMA (1.012)
Worst stock: TATAMOTORS (PF=0.750), DIVISLAB (Net=-2601)

---

## Key Design Decisions

- Hard EOD stop at 15:00 (not 15:25) — no entries or bounces found at/after 15:00
- ATR14 precomputed with DS3 warm-up to avoid NaN at start of 2022
- TP checked before SL on same bar
- BAJFINANCE has no DS3 parquet — ATR computed from fv2 CSV only; first ~26 trades of 2022 excluded from RSI/MACD analysis (NaN warmup, 0.05% impact). To fix: run `Framework_V1/scripts/fetch_bajfinance_ds3.py` from Claude Desktop (Kite OAuth required).
