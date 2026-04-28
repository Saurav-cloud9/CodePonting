# CodePonting — Algorithmic Trading System

MA Bounce strategy research and development for NSE F&O stocks.

## Status

| Framework | Status | Notes |
|-----------|--------|-------|
| Framework_V0 | ⛔ Archived | Legacy bot v0.1–v1 |
| Framework_V1 | ❌ Closed (2026-03-25) | Signal insufficient, charges 3.4× raw profit |
| Framework_V1_Sandbox | ❌ Closed | BQS + DT/RF exhausted, no viable filter |
| **Framework_V2** | ✅ **Active** | Signal redesign, Gap 1 done, raw edge target |

**Active Work:** fv2 signal redesign — TATAMOTORS 5-min, Gap 1 implemented (rising slope filter).  
Gap 1 result: CAGR -172% → -2.07%, MDD -169% → -17.88%, PF 0.77 → 0.95  
Next: improve raw edge from PF 0.95 → >1.01

**Market:** NSE F&O stocks  
**Trading Hours:** 9:30 AM - 3:00 PM IST

## fv2 Signal Design (Active)

True MA bounce — 12 params across a 3-gate temporal evaluation system:

| Gate | Params | What it checks |
|------|--------|---------------|
| G1 — Pre-touch (#01–#04) | slope_threshold, slope_offset, candles_above, pullback_bars | Trend context + approach direction |
| G2 — Touch & bounce (#05–#10) | shoot_depth, touch_body_pct, wick_defence_ratio, bounce_vr_abs, bounce_vr_rel, same_candle_tb | Price interaction with MA at touch + bounce confirmation |
| G3 — Post-bounce (#11–#12) | follow-through params | Price behaviour after bounce |

No cascade logic — all 12 params always evaluated regardless of gate result.

Structural gaps being addressed:
- Gap 1 ✅ Trend context — rising slope filter applied
- Gap 2 ✅ Approach direction — candles_above (G1)
- Gap 3 🔄 Pullback quality — shoot_depth, touch_body_pct, wick_defence_ratio (G2, under review)
- Gap 4 🔄 Volume signature — bounce_vr_abs/rel (G2, under review)
- Gap 5 🔄 Follow-through confirmation (G3, under review)

## fv1 Signal (Closed — reference only)

1. Price touches MA20 (low ≤ MA20) — proximity detector, not true bounce
2. Volume confirmation: 1.2× average
3. ATR-based SL (SL=A), 1.8R target
4. Verdict: 28,085 trades/4yr, charges killed every filter variant

## Top Performing Stocks (48-Month Validation)

Based on TRUE bounce backtest (Jan 2022 - Dec 2025):

| Rank | Stock | Consistency | Notes |
|------|-------|-------------|-------|
| 1 | TATAMOTORS | 52.1% | Most consistent performer |
| 2 | POWERGRID | 47.9% | Emerging champion |
| 3 | VEDL | 45.8% | High volatility advantage |
| 4 | ONGC | 41.7% | Reliable support respector |
| 5 | BHARTIARTL | 41.7% | Telecom sector leader |

## Features

### Signal Detection
- TRUE bounce validation (not proximity)
- Volume confirmation (1.2x average threshold)
- 15-minute bounce window
- Enhanced signal logging (10+ metrics per trade)

### Risk Management
- Maximum 5 concurrent positions
- ₹10,000 capital cap per trade
- Automated stop-loss at 0.5%
- End-of-day square-off at 3:00 PM

### Logging & Analytics
- 22-column CSV trade logs
- Real-time dashboard with live P&L
- Signal details capture (touch/bounce candles, volume ratios, MA20 distance)
- Daily and master log files

### Infrastructure
- Upstox v3 API integration
- Dynamic position sizing with user approval
- Color-coded Rich console interface
- Audio alerts for signal detection

## Installation
```bash
# Clone repository
git clone https://github.com/yourusername/CodePonting.git
cd CodePonting

# Install dependencies
pip install requests python-dotenv rich --break-system-packages

# Configure environment
cp .env.example .env
# Add your Upstox API credentials to .env
```

## Configuration

Edit bot configuration in code (lines 125-135):
```python
TARGET_PCT = 0.015          # 1.5% target
STOP_LOSS_PCT = 0.005       # 0.5% stop loss
BOUNCE_THRESHOLD_PCT = 0.5  # Within 0.5% of MA20
MA_PERIOD = 20              # MA20 only
MAX_CAPITAL_PER_ORDER = 10000  # ₹10k max per order
MAX_POSITIONS = 5           # Max 5 concurrent positions
EOD_EXIT_TIME = "15:00"     # 3:00 PM square-off
```

## Usage

### Generate Access Token
```bash
python get_access_token.py
# Copy token to .env file
```

### Run Live Bot
```bash
python ma_bounce_bot_v1_3_PRODUCTION.py
```

### Monitor Mode (Paper Trading)
Set `MONITOR_ONLY = True` in code for signal-only mode without live orders.

## Project Structure
```
CodePonting/
├── ma_bounce_bot_v1_3_PRODUCTION.py    # Main bot
├── get_access_token.py                  # Token generator
├── .env                                 # API credentials
├── Docs/                                # Documentation
│   ├── strategy_core_v1.md             # Strategy logic
│   ├── day1_validation_jan12.md        # Live testing notes
│   └── fixes_needed_v1.1.md            # Improvement roadmap
├── logs/                                # Trade logs
│   ├── bot_activity_YYYYMMDD.log       # Daily activity
│   ├── trades_log_YYYYMMDD.csv         # Daily trades
│   └── trades_log_master.csv           # All-time trades
└── README.md                            # This file
```

## fv2 Roadmap

### Signal Review (active)
- [x] 3-gate system locked (G1/G2/G3, 12 params, no cascade)
- [x] 22 signals reviewed — POWERGRID (9) + HDFCBANK (2) + TATAMOTORS (11)
- [ ] Target 30–50 signals before drawing param conclusions
- [ ] H5 — master combined tuner (coarse grid → 4-condition filter)

### Scale
- [ ] Expand TATAMOTORS signal to all 29 DS3 stocks
- [ ] Aggregate view across universe

### Future
- [ ] Paper trading once PF > 1.1 confirmed OOS
- [ ] Live trading via Upstox adapter

## Backtesting Results

**48-Month Validation (Jan 2022 - Dec 2025)**
- Total stocks tested: 30 F&O stocks
- Total iterations: 1,440 (48 months × 30 stocks)
- Execution time: 2.5 hours
- Data source: Upstox v3 API (5-minute candles)

**Key Findings:**
- TRUE bounce logic (touch + bounce) outperforms proximity detection
- "No Filter" configuration wins 94% of Top 10 appearances
- 1.5% target optimal balance (vs 0.5% or 1.0%)
- Bear markets show higher efficiency per trade than bull markets

## Risk Disclosure

**This is an automated trading system. Past performance does not guarantee future results.**

- Maximum loss per trade: 0.5% (stop loss)
- Average holding period: 2-4 hours
- Win rate: 40-55% (varies by stock and market conditions)
- Recommended capital: Minimum ₹50,000 for proper risk management

**Always test in monitor mode before deploying live capital.**

## Contributing

Contributions welcome! Areas of focus:
- Signal quality improvements
- Regime detection filters
- Performance optimization
- Documentation enhancements

## License

Open Source — Research & Educational purposes

## Author

**Saurav (CodePonting)**  
Quant | Algorithmic Trader | Python Developer | Strategy Researcher

*Built in Dehradun with Claude AI assistance*

---

**Trading involves risk. Use at your own discretion.**
