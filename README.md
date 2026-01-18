# MA Bounce Bot - Algorithmic Trading System

Automated intraday trading bot implementing the Moving Average Bounce strategy on Indian F&O stocks.

## Overview

MA Bounce Bot detects price bounces off the 20-period Moving Average (MA20) on 5-minute timeframes and executes trades with automated position management.

**Current Version:** v1.3 (Enhanced Signal Logging)  
**Strategy:** TRUE bounce detection (touch + bounce confirmation within 15-minute window)  
**Market:** NSE F&O stocks  
**Trading Hours:** 9:30 AM - 3:00 PM IST

## Core Strategy

The bot identifies opportunities where:
1. Price touches MA20 (low ≤ MA20)
2. Price bounces above MA20 within 3 candles (15-minute window)
3. Volume exceeds 1.2x average
4. Entry with 1.5% target and 0.5% stop loss

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

## Roadmap

### v1.4 - Bounce Quality Score (In Progress)
- [ ] Implement 0-100 scoring system
- [ ] Volume ratio (40 pts)
- [ ] Momentum strength (30 pts)
- [ ] Time remaining (20 pts)
- [ ] Wick pattern analysis (10 pts)

### v1.5 - Advanced Filters
- [ ] Nifty regime detection (trending vs sideways)
- [ ] Time window optimization (avoid 11 AM - 2 PM chop)
- [ ] Multi-timeframe confirmation

### Future Enhancements
- [ ] Trailing stop-loss
- [ ] SHORTING capability for downtrends
- [ ] Machine learning signal validation (700+ trade dataset required)

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

Private repository - Not for distribution

## Author

**Saurav (CodePonting)**  
Algorithmic Trader | Python Developer | Strategy Researcher

*Built in Dehradun with Claude AI assistance*

---

**Trading involves risk. Use at your own discretion.**