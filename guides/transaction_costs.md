# Transaction Costs — NSE Equity (CodePonting)

## Charge Formula (per trade, applied to buy_val + sell_val)

```
brokerage = min(buy_val × bkr_rate, 20.0) + min(sell_val × bkr_rate, 20.0)
stt       = sell_val × 0.00025              # 0.025% sell-side only
exchange  = (buy_val + sell_val) × 0.0000297 # 0.00297% NSE equity cash ⚠️ was 0.0000345 (F&O rate — wrong)
sebi      = (buy_val + sell_val) × 0.000001
ipft      = (buy_val + sell_val) × 0.000001  # IPFT charge ⚠️ was missing
gst       = (brokerage + exchange + sebi) × 0.18
stamp     = buy_val × 0.00003               # 0.003% buy-side only
total     = brokerage + stt + exchange + sebi + ipft + gst + stamp
```

## Broker Rates

| Broker | bkr_rate | Cap per leg |
|---|---|---|
| Upstox | 0.0005 (0.05%) | Rs 20 |
| Kite | 0.0003 (0.03%) | Rs 20 |

## Observed Averages

### fv1 (28,085 trades, DS3 2022–2025)
- `net_pnl_upstox` → ~Rs 49.70/trade avg (141% of capital)
- `net_pnl_kite` → ~Rs 34.44/trade avg (98% of capital)

### fv2 (319 trades, TATAMOTORS 2022–2025)
- Total charges ≈ Rs 15,950 = ~1.6% of Rs 10L capital
- Raw edge (PF 0.95) is the bottleneck — NOT charges
- Break-even threshold: PF > ~1.01

## Key Verdicts
- fv1: charges = 3.4× best raw profit — killed every filter
- fv2: lower frequency makes charges manageable — fix signal first
