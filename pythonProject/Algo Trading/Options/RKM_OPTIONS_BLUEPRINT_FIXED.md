# RKM OPTIONS BOT 💰 - COMPLETE BLUEPRINT
## Roti Kapda Makaan - ₹40,000/Month Passive Income

**Created**: December 26, 2025  
**Target Start**: December 29, 2025 (Monday)  
**Goal**: Systematic options income generation

---

## 🎯 VISION & GOALS

### Primary Objective
Generate **₹40,000/month** passive income through conservative credit spread options trading

### Scaling Vision
- **Phase 1**: ₹1L capital → ₹40k/month (Months 1-3)
- **Phase 2**: ₹5L capital → ₹1L/month (Months 4-6)
- **Phase 3**: ₹10L capital → ₹1.5L/month (Months 7-12)
- **Phase 4**: ₹25L capital → ₹2.7L/month (Year 2+)
- **Ultimate**: ₹50L capital → ₹5L+/month (using NIFTY + BANKNIFTY)

### Why Credit Spreads?
✅ **Defined risk** - Max loss known upfront  
✅ **Time decay advantage** - Theta works FOR you  
✅ **High probability** - 75-80% win rate  
✅ **Less monitoring** - Weekly trades, not daily  
✅ **Consistent income** - Premium collected upfront  

---

## 📊 STRATEGY FUNDAMENTALS

### What is a Credit Spread?

**Bull Put Spread** (Betting price won't fall):
- SELL higher strike PUT (collect premium)
- BUY lower strike PUT (protection)
- Keep premium if price stays above short strike

**Example**:
```
NIFTY at 24,500
SELL 24,000 PE @ ₹150
BUY 23,800 PE @ ₹50
NET CREDIT: ₹100 × 25 lots = ₹2,500

If NIFTY > 24,000 at expiry → Keep ₹2,500 ✅
If NIFTY < 23,800 at expiry → Lose ₹2,500 ❌
Breakeven: 23,900
```

### Risk/Reward Profile
- **Max Profit**: ₹2,500 (premium collected)
- **Max Loss**: ₹2,500 (spread width - premium)
- **Risk:Reward**: 1:1 (balanced)
- **Win Rate**: 75-80% (conservative strikes)

---

## 🏗️ COMPLETE FEATURE CHECKLIST

### 1️⃣ STRATEGY DETAILS

#### Strike Selection
- [ ] **Distance OTM**: 500-700 points (conservative)
- [ ] **Spread Width**: 200 points (₹5,000 risk per spread)
- [ ] **Delta Target**: 0.20-0.30 (probability of expiring ITM: 20-30%)
- [ ] **Underlying**: NIFTY (most liquid)
- [ ] **Expiry**: Weekly Thursday expiry

#### Trade Timing
- [ ] **Entry Day**: Monday 9:30-10:00 AM
- [ ] **Entry Trigger**: Market opens stable, no gap down
- [ ] **Exit Day**: Friday 3:15 PM (auto-close)
- [ ] **Early Exit**: 50% profit target (₹1,250 per spread)

#### Trade Structure
- [ ] **Type**: Bull Put Spread (start with one direction)
- [ ] **Quantity**: 4 spreads per week (₹10,000 weekly target)
- [ ] **Capital**: ₹24,000 margin required (₹6,000 per spread)

---

### 2️⃣ BOT AUTOMATION

#### Entry Logic
- [ ] Auto-scan option chain at 9:30 AM Monday
- [ ] Calculate optimal strikes (500-700 points OTM)
- [ ] Verify Delta in 0.20-0.30 range
- [ ] Check VIX < 20 (avoid high volatility)
- [ ] Place 4 spreads as combo orders
- [ ] Confirm all orders filled

#### Exit Logic
- [ ] **Profit Target**: Close at 50% max profit (₹1,250 per spread)
- [ ] **Stop Loss**: Close at 2x loss (-₹5,000 per spread)
- [ ] **Time Exit**: Friday 3:15 PM close all positions
- [ ] **Manual Override**: Allow manual intervention

#### Monitoring
- [ ] Check P&L every hour (9:30 AM - 3:30 PM)
- [ ] Alert if any position hits 80% max loss
- [ ] Daily summary at 3:30 PM
- [ ] Weekly summary Friday evening

---

### 3️⃣ RISK MANAGEMENT

#### Position Limits
- [ ] **Max spreads per week**: 4 (₹10k profit target)
- [ ] **Max capital at risk**: ₹10,000 (4 × ₹2,500)
- [ ] **Max margin used**: ₹24,000
- [ ] **Reserve capital**: ₹76,000 (for adjustments)

#### Circuit Breakers
- [ ] **Weekly loss limit**: -₹10,000 (stop trading for week)
- [ ] **Monthly loss limit**: -₹20,000 (pause strategy, review)
- [ ] **Consecutive losses**: 2 weeks (reduce to 2 spreads)
- [ ] **Win rate drops below 65%**: Stop and review

#### Market Conditions
- [ ] **VIX Filter**: Don't trade if VIX > 20
- [ ] **Trend Filter**: Only Bull Puts if NIFTY > 50-day MA
- [ ] **Event Calendar**: No trades during RBI, Budget, Fed meets
- [ ] **Gap Filter**: Skip if market gaps down > 1%

#### Adjustments
- [ ] **If threatened**: Roll down strikes (collect more premium)
- [ ] **If ITM**: Accept loss, don't fight market
- [ ] **Maximum adjustments**: 1 per position

---

### 4️⃣ TECHNICAL INFRASTRUCTURE

#### Data Requirements
- [ ] Live option chain from Upstox API
- [ ] Current NIFTY spot price
- [ ] Greeks (Delta, Theta, Vega)
- [ ] Implied Volatility (IV)
- [ ] VIX level

#### Order Management
- [ ] Place spread as combo order (both legs together)
- [ ] Handle partial fills (cancel and retry)
- [ ] Order status tracking
- [ ] Modification capability (adjust strikes)

#### Position Tracking
- [ ] Real-time P&L per position
- [ ] Total portfolio P&L
- [ ] Days to expiry countdown
- [ ] Delta exposure
- [ ] Margin utilization

#### Alerts System
- [ ] Telegram/WhatsApp notifications
- [ ] Order fill confirmations
- [ ] Profit target hit alerts
- [ ] Stop loss triggered alerts
- [ ] Daily summary reports

---

### 5️⃣ DATA & VALIDATION

#### Manual Testing Phase (Week 1-2)
- [ ] Place 2 spreads manually Monday
- [ ] Track P&L daily in Excel
- [ ] Document adjustments needed
- [ ] Note slippage, execution issues
- [ ] Validate win rate expectations

#### Paper Trading (Week 3-4)
- [ ] Run bot in simulation mode
- [ ] Track hypothetical trades
- [ ] No real money at risk
- [ ] Test all entry/exit scenarios
- [ ] Validate alerts and monitoring

#### Backtesting Challenges
- [ ] Historical option chain data expensive/unavailable
- [ ] Focus on forward testing (paper + small live)
- [ ] Build confidence through real market exposure

---

### 6️⃣ OPERATIONAL WORKFLOW

#### Monday Morning Routine (9:15-10:00 AM)
1. Check market sentiment (news, global cues)
2. Verify VIX < 20
3. Confirm NIFTY above 50-day MA
4. Run bot to identify strikes
5. Review suggested spreads
6. Place 4 spreads manually (Phase 1) or auto (Phase 3+)
7. Set alerts for profit/loss levels

#### Daily Check (5 minutes)
1. Open positions dashboard
2. Check P&L status
3. Any positions near profit target? → Close early
4. Any positions threatened? → Prepare adjustment
5. Review alerts received

#### Friday Closing (3:00-3:30 PM)
1. Check all open positions
2. Close any remaining positions by 3:15 PM
3. Generate weekly summary report
4. Calculate win rate for the week
5. Plan for next Monday

#### Weekly Review (Friday evening/Saturday)
1. Analyze week's performance
2. Winning trades: What worked?
3. Losing trades: Why? Could we avoid?
4. Adjust parameters if needed
5. Update strategy document

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: Core Strategy Definition ✅ (DONE - Dec 26)
**Duration**: 1 session  
**Status**: Complete  
**Deliverable**: This blueprint document

**What we decided**:
- Bull Put Spreads (conservative)
- 500-700 points OTM
- 200 point spread width
- 4 spreads per week
- ₹40k/month target with ₹1L capital

---

### Phase 2: Manual Testing 📅 (STARTS MONDAY DEC 29)
**Duration**: 2 weeks (Dec 29 - Jan 10)  
**Capital**: ₹1L (start with 2 spreads, scale to 4)  
**Goal**: Learn the mechanics, validate strategy

#### Week 1 Checklist (Dec 29 - Jan 2):

**Monday Dec 29**:
- [ ] 9:00 AM: Review market sentiment
- [ ] 9:15 AM: Check VIX level
- [ ] 9:30 AM: Identify 500-700 OTM strike
- [ ] 9:30 AM: Calculate spread (200 points below)
- [ ] 9:35 AM: Place 2 Bull Put Spreads manually
- [ ] 9:40 AM: Confirm both legs filled
- [ ] Record: Entry prices, strikes, premium collected

**Tuesday-Thursday**:
- [ ] 10:00 AM: Check P&L
- [ ] 3:00 PM: Check P&L again
- [ ] Note any adjustments needed
- [ ] Track Theta decay (daily premium erosion)

**Friday Jan 2**:
- [ ] 3:00 PM: Decide close or hold overnight
- [ ] 3:15 PM: Close all positions
- [ ] Calculate: Total premium vs realized P&L
- [ ] Document: What worked, what didn't

#### Week 2 Checklist (Jan 6 - Jan 10):
- [ ] Monday: Place 4 spreads (double Week 1)
- [ ] Track same metrics
- [ ] Compare 2-spread vs 4-spread management
- [ ] End of week: Calculate 2-week win rate

**Success Criteria**:
- ✅ Win rate ≥ 65% (at least 1 out of 2 weeks profitable)
- ✅ No single loss > ₹5,000
- ✅ Comfortable with mechanics
- ✅ Strategy feels repeatable

---

### Phase 3: Build Bot 🤖 (WEEK 3-4, JAN 13-24)
**Duration**: 2 weeks  
**Prerequisite**: Phase 2 successful  
**Goal**: Automate the manual process

#### Week 3: Core Bot Logic
- [ ] Build option chain data fetcher
- [ ] Calculate optimal strikes algorithm
- [ ] Strike selection based on delta/OTM
- [ ] Order placement (combo orders)
- [ ] Position tracking dashboard

#### Week 4: Monitoring & Alerts
- [ ] Real-time P&L tracking
- [ ] Profit target alerts
- [ ] Stop loss alerts
- [ ] Daily summary generation
- [ ] Telegram integration

**Deliverable**: Working bot (tested with paper trades only)

---

### Phase 4: Paper Trading 📄 (WEEK 5-6, JAN 27 - FEB 7)
**Duration**: 2 weeks  
**Capital**: ₹0 (simulation only)  
**Goal**: Validate bot automation

#### Paper Trading Protocol:
- [ ] Bot identifies strikes Monday 9:30 AM
- [ ] Record suggested trades (don't execute)
- [ ] Track hypothetical P&L all week
- [ ] Close positions Friday
- [ ] Compare bot performance vs manual Phase 2

**Success Criteria**:
- ✅ Bot identifies same quality strikes as manual
- ✅ No execution errors or bugs
- ✅ Alerts trigger correctly
- ✅ Win rate matches manual testing

---

### Phase 5: Live Automation 🎯 (WEEK 7+, FEB 10+)
**Duration**: Ongoing  
**Capital**: Start ₹1L, scale to ₹10L  
**Goal**: Achieve ₹40k/month consistently

#### Scaling Timeline:
- **Month 1** (Feb): 2-4 spreads, ₹20-40k target
- **Month 2** (Mar): 4 spreads consistently, ₹40k achieved
- **Month 3** (Apr): Increase to ₹5L capital, 10 spreads
- **Month 4+**: Scale based on performance

---

## 📝 MANUAL TESTING TEMPLATES

### Daily Trade Log (Excel/Google Sheets)

| Date   | Day | Spread 1 | Spread 2 | Spread 3 | Spread 4 | Daily P&L | Notes |
|--------|-----|----------|----------|----------|----------|-----------|-------|
| Dec 29 | Mon | 24000/23800 PE | 24000/23800 PE | - | - | ₹0 | Entry day |
| Dec 30 | Tue | | | | | +₹500 | Theta decay working |
| Dec 31 | Wed | HOLIDAY | HOLIDAY | - | - | ₹0 | Market closed |
| Jan 1  | Thu | | | | | +₹800 | Nearing profit target |
| Jan 2  | Fri | CLOSED | CLOSED | - | - | +₹2,500 | Target hit! |

### Spread Entry Tracker

```
Date: __________
Time: __________
NIFTY Spot: __________
VIX Level: __________

SPREAD 1:
Short Strike: ________ PE @ ₹_______ (Delta: _____) 
Long Strike: ________ PE @ ₹_______ (Delta: _____)
Net Credit: ₹_______
Max Profit: ₹_______
Max Loss: ₹_______
Breakeven: _______

SPREAD 2-4: (same format)

Market Conditions: ___________________________
Sentiment: ___________________________
Why this trade: ___________________________
```

### Weekly Summary Template

```
WEEK: __________ to __________

TRADES EXECUTED: ____
SPREADS WON: ____
SPREADS LOST: ____
WIN RATE: ____%

GROSS PREMIUM COLLECTED: ₹_______
TOTAL P&L: ₹_______
ROI: ____%

LEARNINGS:
1. ___________________________
2. ___________________________
3. ___________________________

ADJUSTMENTS FOR NEXT WEEK:
1. ___________________________
2. ___________________________
```

---

## 🎓 LEARNING RESOURCES

### Options Basics (Refresh if needed)
- Zerodha Varsity: Options Module
- YouTube: "Credit Spreads Explained"
- Understand: Delta, Theta, IV

### Upstox Platform
- Option chain interface
- How to place spread orders
- GTT orders for options
- Margin requirements

### Risk Psychology
- Accepting losses (2 out of 8 spreads may lose)
- Not over-trading after wins
- Sticking to system rules
- Managing emotions during market swings

---

## ⚠️ CRITICAL REMINDERS

### Before Going Live:
1. ✅ Completed 2 weeks manual testing
2. ✅ Win rate ≥ 65% validated
3. ✅ Comfortable with adjustments
4. ✅ Bot tested in paper mode
5. ✅ Emergency exit plan documented

### Red Flags to Stop Trading:
- 🚫 2 consecutive weekly losses
- 🚫 Win rate drops below 60%
- 🚫 VIX spikes above 25
- 🚫 Unable to monitor positions daily
- 🚫 Feeling stressed or emotional about trades

### Golden Rules:
1. **Never exceed 4 spreads per week** (Phase 1)
2. **Always use stop losses**
3. **Don't fight the market** (accept losses gracefully)
4. **Trade the plan, not emotions**
5. **Weekly review is mandatory**

---

## 📞 SUPPORT & ESCALATION

### If Things Go Wrong:
1. **Position threatened**: Close immediately, don't adjust multiple times
2. **Bot error**: Revert to manual mode
3. **Unexpected loss**: Document, review, don't revenge trade
4. **Consecutive losses**: STOP, review with fresh perspective

### Decision Tree:
```
Is win rate > 65% after 4 weeks?
  ├─ YES → Continue, consider scaling
  └─ NO → Pause, review strategy
      ├─ Market conditions changed? → Adapt parameters
      ├─ Execution issues? → Fix process
      └─ Strategy flawed? → Back to drawing board
```

---

## 🎯 SUCCESS METRICS

### After Month 1:
- [ ] Executed 4-8 spreads
- [ ] Win rate ≥ 65%
- [ ] Total profit ≥ ₹20k
- [ ] No single loss > ₹5k
- [ ] Confident in strategy

### After Month 3:
- [ ] Executed 12+ spreads
- [ ] Win rate ≥ 70%
- [ ] Total profit ≥ ₹1L
- [ ] Strategy feels systematic
- [ ] Ready to scale capital

### After Month 6:
- [ ] Executed 24+ spreads
- [ ] Win rate ≥ 75%
- [ ] Total profit ≥ ₹3L
- [ ] Bot fully automated
- [ ] Scaling to ₹5L capital

---

## 📅 NEXT STEPS

### Today (Dec 27, Saturday):
- [ ] Review this blueprint thoroughly
- [ ] Ask any clarifying questions
- [ ] Mental preparation for Monday start

### Saturday/Sunday (Dec 27-28):
- [ ] Open Upstox, familiarize with option chain
- [ ] Practice identifying 500-700 OTM strikes
- [ ] Set up tracking spreadsheet
- [ ] Review Zerodha Varsity options module

### Monday (Dec 29) - GO TIME! 🚀:
- [ ] 9:00 AM: Read this blueprint one more time
- [ ] 9:15 AM: Check market, VIX, sentiment
- [ ] 9:30 AM: Place first 2 credit spreads
- [ ] 9:40 AM: Celebrate first RKM trade! 🎉
- [ ] Rest of day: Monitor calmly
- [ ] Evening: Update trade log

---

## 💎 FINAL THOUGHTS

**Remember:**
- This is a marathon, not a sprint
- ₹40k/month = ₹480k/year = Life-changing money
- Conservative approach = Sustainable income
- Losses are part of the game (aim for 75%, not 100%)
- The goal is consistency, not perfection

**You're building:**
- Financial independence
- Passive income stream
- Scalable system
- Long-term wealth

**Start small, learn well, scale smart!**

---

*Blueprint Version: 1.0*  
*Last Updated: December 26, 2025*  
*Next Review: After Phase 2 completion (Jan 10)*

---

## 🔗 RELATED DOCUMENTS

- `PLATINUM_HANDOVER.md` - Equity bot upgrade plan
- `ma_bounce_bot_v0_6_PLATINUM.py` - Equity bot code
- `daily_report_generator.py` - Trade tracking tool

**Keep all these together in: `/Algo Trading/Options/rkm_credit_spreads/`**
