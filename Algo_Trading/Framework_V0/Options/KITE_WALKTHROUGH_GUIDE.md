# KITE PLATFORM WALKTHROUGH 🎯
## RKM Options Bot - Monday Morning Guide

**Date**: December 29, 2025 (Monday)  
**Time**: 9:00 AM - 10:00 AM  
**Goal**: Place first 2 Bull Put Spreads on NIFTY

---

## 🚀 PRE-MARKET CHECKLIST (9:00 AM - 9:15 AM)

### Step 1: Login to Kite
- Go to **kite.zerodha.com** or open Kite mobile app
- Login with your credentials
- Ensure you're on the **Dashboard** home screen

### Step 2: Check Market Sentiment
**Where**: Top of Kite dashboard or News section

**What to look for**:
- 📰 Any major news overnight? (RBI announcement, global market crash, etc.)
- 🌍 Global cues: US markets, Asian markets performance
- 📊 NIFTY futures indication (gap up/down?)

**Decision Rule**:
- ✅ **Green Flag**: Normal market, no major negative news → Proceed
- 🚫 **Red Flag**: Gap down >1%, major negative event → SKIP today

---

## 📊 STEP 1: CHECK VIX LEVEL (9:15 AM)

### How to Check VIX:

**Method 1: Search Bar**
1. Click the **Search bar** at top of Kite
2. Type: **INDIA VIX**
3. Click on "INDIA VIX" from results
4. Check current value

**Method 2: Marketwatch**
1. Go to **Marketwatch** tab
2. Add "INDIA VIX" if not already there
3. See live value

**What You're Looking For**:
- ✅ **VIX < 20**: Safe to trade (low volatility)
- ⚠️ **VIX 20-25**: Cautious (medium volatility)
- 🚫 **VIX > 25**: SKIP trading today (high volatility)

**Why This Matters**: High VIX = high market uncertainty = your spreads are more likely to get hit

---

## 📈 STEP 2: CHECK NIFTY TREND (9:15 AM)

### Verify NIFTY is Above 50-day MA

**How to Check**:
1. Search for **NIFTY 50** in search bar
2. Click on chart icon
3. Look at the chart view
4. Add **50-day Moving Average** indicator:
   - Click "Studies" or "Indicators" button
   - Search for "Moving Average"
   - Set period to 50
   - Set type to "SMA" (Simple Moving Average)

**Decision Rule**:
- ✅ **NIFTY above 50-MA line**: Bullish trend → Safe for Bull Put Spreads
- 🚫 **NIFTY below 50-MA line**: Bearish trend → SKIP or wait

**Pro Tip**: You only need Bull Puts when market is in uptrend/neutral. In downtrend, your short puts are more likely to get breached.

---

## 🎯 STEP 3: OPEN NIFTY OPTIONS CHAIN (9:30 AM)

### Accessing the Option Chain

**Desktop/Web Version**:
1. Search for **NIFTY 50** in search bar
2. From the dropdown, select **"NIFTY" (not NIFTY 50 index)**
3. Click on the result
4. You'll see a page with NIFTY spot price
5. Look for **"Option Chain"** button/tab
6. Click it to open the full option chain

**Mobile App**:
1. Search **NIFTY**
2. Tap on NIFTY 50
3. Swipe to find **"Options"** tab
4. Tap to view option chain

### Understanding the Option Chain Layout

```
CALLS (CE)                           STRIKES                    PUTS (PE)
OI | IV | LTP | Bid | Ask     |     Strike Price      |  Bid | Ask | LTP | IV | OI
-------------------------------|----------------------|-----------------------------
                               |      24500           |
                               |      24400           |
                               |      24300           |
     YOU WANT THIS SIDE -----> |      24000           | <---- YOUR SHORT PUT
                               |      23800           | <---- YOUR LONG PUT
                               |      23600           |
```

**Key Columns to Focus On**:
- **Strike**: The strike price (24000, 23800, etc.)
- **LTP (Last Traded Price)**: Current premium price
- **Bid/Ask**: Buy/Sell prices
- **IV (Implied Volatility)**: Higher IV = higher premium
- **Delta**: Probability of finishing ITM (look for 0.20-0.30)
- **OI (Open Interest)**: Liquidity indicator (higher is better)

---

## 🔍 STEP 4: IDENTIFY OPTIMAL STRIKES (9:30 AM)

### Finding Strikes 500-700 Points OTM

**Scenario**: NIFTY spot is at **24,500**

**Your Target Short Strike**: 24,500 - 500 to 700 = **23,800 to 24,000**

**Steps**:
1. Note current NIFTY spot price (shown at top of option chain)
2. Subtract 500 points: 24,500 - 500 = **24,000 PE** (aggressive)
3. Subtract 700 points: 24,500 - 700 = **23,800 PE** (conservative)

**Choose Your Short Strike**:
- **24,000 PE** for higher premium (₹150-200 range)
- **23,800 PE** for safer distance (₹100-150 range)

**Your Long Strike** (Protection):
- 200 points below short strike
- If short = 24,000, then long = **23,800 PE**
- If short = 23,800, then long = **23,600 PE**

### Verify Delta Range (0.20-0.30)

**Where to find Delta**:
- Option chain should show Greeks column
- If not visible, click "Show Greeks" or expand view
- Look for Delta value next to your strike

**What You Want**:
- Short Put Delta: **0.20 to 0.30** (20-30% chance of expiring ITM)
- This gives you 70-80% probability of profit

**If Delta is Higher (0.40+)**: Strike is too close, move down
**If Delta is Lower (0.10)**: Strike is too far, less premium

---

## 💰 STEP 5: CHECK PREMIUM VALUES (9:30-9:35 AM)

### Reading Premium Prices

For a **24,000 / 23,800 Bull Put Spread**:

```
Strike    | LTP (₹) | Bid (₹) | Ask (₹) | You Do
----------|---------|---------|---------|------------------
24000 PE  |   150   |   148   |   152   | SELL at Bid (~148)
23800 PE  |    50   |    48   |    52   | BUY at Ask (~52)
----------|---------|---------|---------|------------------
NET CREDIT|         |         |         | 148 - 52 = ₹96
```

**What to Look For**:
- ✅ **Good Spread**: Bid-Ask difference < ₹5 (liquid market)
- ✅ **Net Credit**: Aim for ₹80-120 per lot (25 qty)
- ✅ **Risk-Reward**: 1:1 ratio (credit ≈ half of spread width)

**Calculate Your Trade**:
- Net Credit per lot: ₹96 × 25 = **₹2,400**
- Max Profit: ₹2,400
- Max Loss: (200 × 25) - 2,400 = **₹2,600**
- Breakeven: 23,800 + 96 = **23,896**

---

## 📝 STEP 6: PLACE THE SPREAD ORDER (9:35 AM)

### Option A: Basket Order (Recommended for Beginners)

**Why Basket?**: Ensures both legs execute together, no risk of partial fill

**Steps**:
1. From option chain, click **BUY** on 23,800 PE
   - Quantity: 25 (1 lot)
   - Order type: MARKET or LIMIT
   - If LIMIT: Set at Ask price or ₹1-2 above
   - Click "Add to basket" (don't place yet!)

2. From option chain, click **SELL** on 24,000 PE
   - Quantity: 25 (1 lot)
   - Order type: MARKET or LIMIT
   - If LIMIT: Set at Bid price or ₹1-2 below
   - Click "Add to basket"

3. Go to **Basket Orders** section
   - You should see both orders
   - Verify: 1 BUY (23,800 PE) + 1 SELL (24,000 PE)
   - Check quantities match (25 each)

4. Click **"Execute Basket"**
   - Both orders will fire simultaneously
   - Monitor fill status

### Option B: Spread Order (Advanced)

**Note**: Zerodha Kite supports spread orders for options

**Steps**:
1. Click on your short strike (24,000 PE)
2. Look for **"Spread"** or **"Strategy"** option
3. Select **"Bull Put Spread"** or **"Credit Spread"**
4. System will ask for:
   - Short Leg: 24,000 PE (SELL)
   - Long Leg: 23,800 PE (BUY)
   - Quantity: 25
   - Credit you want: ₹96 (or MARKET)
5. Click **Place Order**

**Advantage**: Single order executes as a spread, better execution

---

## ✅ STEP 7: CONFIRM ORDER EXECUTION (9:35-9:40 AM)

### Check Order Status

**Where to Look**:
- **Orders** tab in Kite
- Should show both orders

**Verify**:
- ✅ Both orders show "COMPLETE" status
- ✅ Quantities match (25 each)
- ✅ Net credit is close to your target (₹90-100 range)

**What If Partial Fill?**:
1. Only one leg filled? **DANGER!**
2. Cancel the unfilled order immediately
3. If SELL filled but BUY didn't: You have naked short put (risky!)
4. Exit the filled leg ASAP
5. Try again with both legs as basket order

### Record Entry Details

**Immediately fill your Excel tracker**:

**Spread Entry Tracker Sheet**:
```
Trade Date: Dec 29, 2025
Entry Time: 9:36 AM
NIFTY Spot: 24,500
VIX Level: 14.2

SPREAD 1:
Short Strike: 24000 PE @ ₹148 (Delta: 0.25)
Long Strike: 23800 PE @ ₹52 (Delta: 0.15)
Net Credit: ₹96
Max Profit: ₹2,400
Max Loss: ₹2,600
Breakeven: 23,896

Market Conditions: Stable open, no gap
Sentiment: Bullish, above 50-MA
Why this trade: VIX low, NIFTY strong, safe OTM distance
```

---

## 👀 STEP 8: MONITOR YOUR POSITION (Throughout the Day)

### Where to See Your Positions

**Positions Tab**:
- Click **"Positions"** in Kite
- You'll see both legs:
  ```
  +25 NIFTY 23800 PE (Long)
  -25 NIFTY 24000 PE (Short)
  ```

**Check**:
- ✅ Quantity shows correctly
- ✅ P&L is updating
- ✅ Net P&L for the spread

### Understanding P&L Display

**How Kite Shows Spread P&L**:
```
Position          | Qty | Avg Price | LTP  | P&L
------------------|-----|-----------|------|--------
NIFTY 24000 PE    | -25 |    148    | 140  | +₹200   (premium decaying, good!)
NIFTY 23800 PE    | +25 |     52    |  48  | -₹100   (premium decaying, good!)
------------------|-----|-----------|------|--------
NET P&L           |     |           |      | +₹100
```

**What This Means**:
- Short put premium **going down** = Profit ✅
- Long put premium going down = Small loss (but it's your insurance)
- **Net P&L positive** = You're winning!

### Daily Check Routine

**10:00 AM Check**:
- Quick P&L glance
- NIFTY still above your short strike?
- Any major market move?

**3:00 PM Check**:
- End of day P&L
- Decision: Hold or take profit early?
- Update Daily Trade Log in Excel

---

## 🎯 STEP 9: PROFIT TAKING / EXIT STRATEGY

### When to Exit Early (50% Profit Target)

**Your Entry**: Net credit = ₹96 × 25 = ₹2,400  
**Your 50% Target**: ₹1,200 profit

**How to Calculate Current P&L**:
```
Current Premium Difference = (Short LTP - Long LTP)
Exit Credit Needed = 96 - 48 = ₹48

If you can buy back the spread for ₹48:
Original Credit: ₹96
Exit Cost: ₹48
Profit: ₹96 - ₹48 = ₹48 per lot × 25 = ₹1,200 ✅
```

**How to Close Early**:
1. Reverse the original trade:
   - **BUY** 24,000 PE (close your short)
   - **SELL** 23,800 PE (close your long)
2. Use basket order (same as entry, but opposite)
3. Execute both legs together

### Friday 3:15 PM - Mandatory Close

**Final Exit Process**:
- **3:00 PM**: Start preparing to close
- **3:10 PM**: Get latest option chain prices
- **3:15 PM**: Execute basket order to close
  - BUY back 24,000 PE
  - SELL 23,800 PE
- **3:20 PM**: Confirm both orders filled
- **3:25 PM**: Final P&L check

**Why Close Early?**:
- Avoid expiry day risk
- Capture 70-80% of max profit
- Sleep peacefully over weekend

---

## 🔔 STEP 10: SET UP ALERTS (Optional but Recommended)

### Kite Price Alerts

**How to Set**:
1. Click on your position (24,000 PE)
2. Look for "Create Alert" option
3. Set alert at **80% of short strike**:
   - If short = 24,000, set alert at **24,320** (NIFTY spot)
   - This gives you warning if NIFTY approaching danger

**What Happens**:
- You get notification when NIFTY crosses 24,320
- Time to watch position closely
- Consider closing if continues falling

### Mobile App Notifications

**Enable**:
- Order confirmations
- Position updates
- Price alerts

---

## 📊 MARGIN REQUIREMENTS

### How Much Margin You Need

**For 1 Bull Put Spread (24000/23800)**:
- Zerodha SPAN margin calculator
- Approximate margin: ₹5,000-6,000 per spread

**For 2 Spreads (Your Week 1 Plan)**:
- Total margin needed: ₹10,000-12,000
- Keep ₹15,000-20,000 in account (buffer)

**Where to Check**:
- Kite → Account → Funds
- Shows available margin
- Must have enough before placing orders

**Pro Tip**: Run margin calculation on Zerodha website BEFORE market opens

**Link**: https://zerodha.com/margin-calculator/SPAN/

---

## 🚨 COMMON MISTAKES TO AVOID

### ❌ DON'T DO THIS:

1. **Selling without buying protection**
   - NEVER sell put without buying lower put
   - Naked puts = unlimited risk
   - Always execute as spread

2. **Chasing premium**
   - Don't go too close to spot for higher premium
   - Stick to 500-700 OTM range
   - Higher premium = higher risk

3. **Partial fills**
   - If only one leg fills, immediately exit
   - Don't hold naked positions
   - Use basket orders to prevent this

4. **Ignoring VIX**
   - High VIX (>20) = Skip trading
   - Market too volatile for credit spreads

5. **Fighting the market**
   - If market breaks your short strike, accept loss
   - Don't add to losing positions
   - Follow your stop loss rules

6. **Trading on event days**
   - No trades during RBI meets
   - No trades on Budget day
   - No trades on Fed announcement days

---

## 📱 QUICK REFERENCE CHECKLIST

### Monday Morning Flow (Print This!)

```
☐ 9:00 AM - Check market sentiment (news, global cues)
☐ 9:15 AM - Check VIX < 20 ✓
☐ 9:15 AM - Verify NIFTY > 50-day MA ✓
☐ 9:30 AM - Open NIFTY option chain
☐ 9:30 AM - Find strikes 500-700 OTM
☐ 9:32 AM - Check Delta (0.20-0.30 range)
☐ 9:33 AM - Note premium values (Bid/Ask)
☐ 9:35 AM - Calculate Net Credit & Risk
☐ 9:36 AM - Place Spread 1 (Basket Order)
☐ 9:37 AM - Verify both legs filled ✓
☐ 9:38 AM - Place Spread 2 (Basket Order)
☐ 9:39 AM - Verify both legs filled ✓
☐ 9:40 AM - Fill Excel Entry Tracker
☐ 9:41 AM - Set price alerts
☐ 9:45 AM - Take deep breath, celebrate first trade! 🎉
```

---

## 🎓 LEARNING RESOURCES

### Before Monday:

**Saturday/Sunday Prep**:
1. **Zerodha Varsity** - Options Module
   - Chapter on Credit Spreads
   - Understanding Greeks (Delta especially)
   - Link: varsity.zerodha.com

2. **Practice on Option Chain** (Sunday evening)
   - Open Kite
   - Browse NIFTY options (won't place orders)
   - Get familiar with layout
   - Practice calculating spreads

3. **YouTube**: Search "Bull Put Spread on Kite"
   - See visual demos
   - Understand order placement
   - Watch basket order process

---

## 🔧 TROUBLESHOOTING

### Problem: Can't find Option Chain

**Solution**: 
- Make sure you searched "NIFTY" not "NIFTY 50"
- Click on the futures/options symbol
- Look for "Option Chain" tab/button

### Problem: No Greeks showing

**Solution**:
- Look for "Show Greeks" checkbox/button
- May need to expand view
- On mobile, swipe to see more columns

### Problem: Order rejected

**Possible Reasons**:
1. Insufficient margin → Add funds
2. Wrong quantity (not in multiples of lot size) → Use 25, 50, 75
3. Market closed → Wait for 9:15 AM
4. Price limit too aggressive → Use MARKET order

### Problem: Only one leg filled

**Immediate Action**:
1. Cancel unfilled order
2. Exit filled position (reverse it)
3. Try basket order again
4. Consider using spread order type

---

## 💡 PRO TIPS

1. **First Trade Nerves?**
   - Start with just 1 spread (not 2)
   - Get comfortable with the process
   - Scale to 2 spreads in Week 2

2. **Best Execution Time**
   - 9:30-10:00 AM: Initial volatility, good premiums
   - Avoid first 5 minutes if too chaotic

3. **Liquidity Check**
   - Choose strikes with high OI (>10,000)
   - Tight bid-ask spread (<₹5)
   - This ensures easy entry/exit

4. **Weekend Planning**
   - Friday evening: Review week's performance
   - Sunday evening: Check economic calendar
   - Sunday night: Plan Monday's strikes (practice)

5. **Emotional Control**
   - Remember: 75% win rate means 25% losses
   - 1 loss in 4 trades is NORMAL
   - Stick to system, don't revenge trade

---

## 📞 SUPPORT CONTACTS

### Zerodha Support:
- **Phone**: 080-4040400 (9 AM - 6 PM)
- **Email**: support@zerodha.com
- **Ticket**: support.zerodha.com

### Common Issues:
- Margin queries
- Order execution problems
- Technical platform issues

---

## 🎯 YOUR WEEK 1 GOALS

**Success Criteria**:
- ✅ Place 2 spreads successfully
- ✅ Both legs execute (no partial fills)
- ✅ Track everything in Excel
- ✅ Learn the platform mechanics
- ✅ Close positions by Friday

**It's NOT About**:
- ❌ Making huge profits Week 1
- ❌ Perfect execution
- ❌ Avoiding all losses

**It's About**:
- ✅ Learning the process
- ✅ Building confidence
- ✅ Understanding the mechanics
- ✅ Validating the strategy

---

## 🚀 FINAL REMINDER

**You are ready!**

You have:
- ✅ Complete strategy documented
- ✅ Excel tracker ready
- ✅ This step-by-step guide
- ✅ Risk management rules
- ✅ Exit strategies planned

**Monday Morning Mindset**:
- Be calm and methodical
- Follow the checklist
- Don't rush
- It's okay to skip if conditions aren't right
- One trade at a time

**The Goal**: Not to make ₹10,000 in Week 1.  
**The Goal**: To execute your first RKM trade perfectly and learn.

---

**Good luck, Saurav! You've got this! 💪**

*"Start small, learn well, scale smart!"*

---

*Guide Version: 1.0*  
*Created: December 27, 2025*  
*For: RKM Options Bot - Week 1 Launch*
