# Smart Money Concepts (SMC) — Complete Session Reference
*Detailed notes from the fv2 strategy development session. Use this to redo the concepts with CC.*

> **Recovered 2026-09-07** from a bookmarked claude.ai session (see `01_plan.md`'s Status),
> replacing this file's earlier, shorter summary. Actual backtest results for these 3
> concepts (Liquidity/FVG/OB) live in `03_backtest_results.md`, reference diagrams in
> `diagrams/`, an early illustrative (not production) script in
> `reference_liquidity_sweep_signal_illustrative.py`.

---

## Overview

These 5 concepts are NOT standalone strategies. They are **confluence filters** layered on top of your MA20 bounce entry to improve signal quality. The core principle established in this session:

> **Build filters INTO entry signal generation upfront — do not apply them to backtest results after the fact.**

- Liquidity, FVG, OB = WHERE to trade (zone-based)
- BOS = WHEN conditions are right (regime-based)
- Inducement = timing filter to avoid traps

All three long setups (Liquidity, FVG, OB) have mirror short versions — just flip the direction.

---

## 1. Liquidity

### Definition
Clusters of resting stop-loss and pending orders sitting just below swing lows (sell-side) or just above swing highs (buy-side). Price is drawn to these zones to trigger those orders, then reverses.

- **Sell-side liquidity** = below swing lows (long traders' stop losses parked here)
- **Buy-side liquidity** = above swing highs (short traders' stop losses parked here)

### What Liquidity Actually Is
Liquidity in SMC is NOT the same as general market liquidity (bid-ask depth, volume). It specifically means a cluster of PENDING/RESTING ORDERS at a price level — stop losses + breakout entries — making that price a magnet and target for smart money.

### Why the Sweep Happens
When price dips below a swing low:
1. Long traders' stop losses get triggered (they are forced sellers)
2. Breakout short sellers also enter (fresh sell-side liquidity)
3. That burst of selling is absorbed by large buyers who needed this sell-order flow to fill their own large buy orders without moving price against themselves
4. Once the resting sell liquidity is consumed, no sellers remain → buyers dominate → sharp rejection → reversal

### Swing Low Identification (N-bar Fractal)

**The Rule:** A candle is a swing low if its LOW is lower than the lows of N candles on BOTH its left AND right side.

- N=1 → check 1 candle each side → 3 candles total → noisy, too many false signals
- N=2 → check 2 candles each side → 5 candles total → recommended for fv2
- N=3 → check 3 candles each side → 7 candles total → fewer but very significant swings

**Critical clarification:** The middle candle just needs to be the LOWEST of all N*2+1 candles. The surrounding candles do NOT need to be in any particular order (no staircase pattern required). Just the middle must be lower than all neighbours.

**Code condition for N=2:**
```
low[i] < low[i-1] AND low[i] < low[i-2]   ← left side
AND
low[i] < low[i+1] AND low[i] < low[i+2]   ← right side
```

**Confirmed at:** bar i+2 (need right side candles to close before labelling)

**Why right side candles are needed:** Left side alone means you are finding the lowest candle so far in a falling move — but price might keep falling. Right side candles prove price bounced from that level, confirming the swing low is a genuine support/rejection point.

**Multiple swing lows:** If multiple unswept swing lows exist within the lookback window, always use the most recently confirmed one (freshest stop-loss cluster).

### Diagram — Swing Low Identification

<div style="background:#0f172a; padding:10px; border-radius:8px; margin:10px 0;">
<svg viewBox="0 0 760 460" xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <rect width="760" height="460" fill="#0f172a"/>
  <text x="20" y="28" fill="#e2e8f0" font-size="15" font-weight="bold">Swing Low Identification — N-bar Fractal Logic</text>
  <line x1="40" y1="80"  x2="740" y2="80"  stroke="#1e293b"/>
  <line x1="40" y1="160" x2="740" y2="160" stroke="#1e293b"/>
  <line x1="40" y1="240" x2="740" y2="240" stroke="#1e293b"/>
  <line x1="40" y1="320" x2="740" y2="320" stroke="#1e293b"/>
  <text x="50" y="55" fill="#94a3b8" font-size="12" font-weight="bold">Example 1: N=1 (1 candle left, 1 candle right)</text>
  <line x1="80"  y1="140" x2="80"  y2="200" stroke="#ef4444" stroke-width="1.5"/><rect x="68"  y="155" width="24" height="30" rx="2" fill="#ef4444"/>
  <line x1="140" y1="180" x2="140" y2="260" stroke="#ef4444" stroke-width="1.5"/><rect x="128" y="195" width="24" height="50" rx="2" fill="#ef4444"/>
  <line x1="200" y1="155" x2="200" y2="245" stroke="#22c55e" stroke-width="1.5"/><rect x="188" y="170" width="24" height="55" rx="2" fill="#22c55e"/>
  <circle cx="140" cy="260" r="7" fill="none" stroke="#a78bfa" stroke-width="2"/>
  <text x="110" y="285" fill="#a78bfa" font-size="11">Swing Low</text>
  <text x="105" y="297" fill="#a78bfa" font-size="10">C2 low lower than</text>
  <text x="105" y="308" fill="#a78bfa" font-size="10">C1 low AND C3 low</text>
  <line x1="80" y1="200" x2="128" y2="258" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="200" y1="245" x2="152" y2="258" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="60" y="200" fill="#64748b" font-size="10">higher</text>
  <text x="205" y="240" fill="#64748b" font-size="10">higher</text>
  <text x="115" y="255" fill="#a78bfa" font-size="10">lowest</text>
  <rect x="55" y="325" width="195" height="22" rx="4" fill="#1a1a2e"/>
  <text x="65" y="340" fill="#22c55e" font-size="11">Valid swing low (N=1). Simple but noisy.</text>
  <text x="310" y="55" fill="#94a3b8" font-size="12" font-weight="bold">Example 2: N=2 (2 candles left, 2 candles right)</text>
  <line x1="320" y1="130" x2="320" y2="190" stroke="#ef4444" stroke-width="1.5"/><rect x="308" y="145" width="24" height="30" rx="2" fill="#ef4444"/>
  <line x1="375" y1="155" x2="375" y2="215" stroke="#ef4444" stroke-width="1.5"/><rect x="363" y="170" width="24" height="30" rx="2" fill="#ef4444"/>
  <line x1="430" y1="185" x2="430" y2="270" stroke="#ef4444" stroke-width="1.5"/><rect x="418" y="200" width="24" height="55" rx="2" fill="#ef4444"/>
  <line x1="485" y1="150" x2="485" y2="255" stroke="#22c55e" stroke-width="1.5"/><rect x="473" y="165" width="24" height="70" rx="2" fill="#22c55e"/>
  <line x1="540" y1="120" x2="540" y2="195" stroke="#22c55e" stroke-width="1.5"/><rect x="528" y="135" width="24" height="48" rx="2" fill="#22c55e"/>
  <circle cx="430" cy="270" r="7" fill="none" stroke="#a78bfa" stroke-width="2"/>
  <text x="400" y="295" fill="#a78bfa" font-size="11">Swing Low</text>
  <text x="382" y="307" fill="#a78bfa" font-size="10">C3 low is lower than</text>
  <text x="378" y="318" fill="#a78bfa" font-size="10">C1, C2, C4, C5 lows</text>
  <line x1="320" y1="190" x2="418" y2="268" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="375" y1="215" x2="418" y2="268" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="485" y1="255" x2="442" y2="268" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="540" y1="195" x2="442" y2="268" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
  <rect x="295" y="325" width="280" height="22" rx="4" fill="#1a1a2e"/>
  <text x="305" y="340" fill="#22c55e" font-size="11">Valid swing low (N=2). More reliable. Fewer false signals.</text>
  <text x="620" y="55" fill="#94a3b8" font-size="12" font-weight="bold">Not a Swing Low</text>
  <line x1="610" y1="140" x2="610" y2="200" stroke="#ef4444" stroke-width="1.5"/><rect x="598" y="155" width="24" height="30" rx="2" fill="#ef4444"/>
  <line x1="660" y1="175" x2="660" y2="250" stroke="#ef4444" stroke-width="1.5"/><rect x="648" y="190" width="24" height="45" rx="2" fill="#ef4444"/>
  <line x1="710" y1="200" x2="710" y2="270" stroke="#ef4444" stroke-width="1.5"/><rect x="698" y="215" width="24" height="42" rx="2" fill="#ef4444"/>
  <circle cx="660" cy="250" r="7" fill="none" stroke="#ef4444" stroke-width="2"/>
  <text x="652" y="253" fill="#ef4444" font-size="11" font-weight="bold">X</text>
  <text x="618" y="275" fill="#ef4444" font-size="10">C3 low is LOWER</text>
  <text x="615" y="287" fill="#ef4444" font-size="10">than C2. Not valid.</text>
  <rect x="590" y="325" width="155" height="22" rx="4" fill="#1a1a2e"/>
  <text x="600" y="340" fill="#ef4444" font-size="11">Trend still falling. Skip.</text>
  <rect x="40" y="370" width="680" height="75" rx="6" fill="#1e293b"/>
  <text x="60" y="390" fill="#e2e8f0" font-size="12" font-weight="bold">The Rule:</text>
  <text x="60" y="408" fill="#94a3b8" font-size="11">A candle is a SWING LOW if its LOW is lower than the lows of N candles on both its left AND right side.</text>
  <text x="60" y="424" fill="#94a3b8" font-size="11">N=1 = noisy. N=2 or N=3 = cleaner, fewer but stronger signals.</text>
  <text x="60" y="440" fill="#f59e0b" font-size="11">For fv2: N=2 or N=3 recommended. Tunable parameter.</text>
</svg>
</div>

### Diagram — Liquidity Sweep Buy Signal

<div style="background:#0f172a; padding:10px; border-radius:8px; margin:10px 0;">
<svg viewBox="0 0 760 480" xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <rect width="760" height="480" fill="#0f172a"/>
  <text x="20" y="28" fill="#e2e8f0" font-size="15" font-weight="bold">How Liquidity Sweep Generates a BUY Signal</text>
  <rect x="40"  y="45" width="200" height="330" rx="6" fill="#ef4444" opacity="0.06"/>
  <rect x="255" y="45" width="160" height="330" rx="6" fill="#eab308" opacity="0.08"/>
  <rect x="430" y="45" width="290" height="330" rx="6" fill="#22c55e" opacity="0.07"/>
  <text x="80"  y="65" fill="#ef4444" font-size="12" font-weight="bold">PHASE 1: DOWNTREND</text>
  <text x="260" y="65" fill="#eab308" font-size="12" font-weight="bold">PHASE 2: SWEEP</text>
  <text x="440" y="65" fill="#22c55e" font-size="12" font-weight="bold">PHASE 3: BUY SIGNAL</text>
  <line x1="40" y1="110" x2="720" y2="110" stroke="#1e293b" stroke-width="1"/>
  <line x1="40" y1="190" x2="720" y2="190" stroke="#1e293b" stroke-width="1"/>
  <line x1="40" y1="270" x2="720" y2="270" stroke="#1e293b" stroke-width="1"/>
  <line x1="40" y1="350" x2="720" y2="350" stroke="#1e293b" stroke-width="1"/>
  <text x="8" y="114" fill="#64748b" font-size="11">120</text>
  <text x="8" y="194" fill="#64748b" font-size="11">114</text>
  <text x="8" y="274" fill="#64748b" font-size="11">108</text>
  <text x="8" y="354" fill="#64748b" font-size="11">102</text>
  <line x1="170" y1="270" x2="720" y2="270" stroke="#a78bfa" stroke-width="1.8" stroke-dasharray="8,5"/>
  <rect x="40" y="258" width="120" height="24" rx="4" fill="#1e1535"/>
  <text x="48" y="274" fill="#a78bfa" font-size="11" font-weight="bold">Swing Low = 108</text>
  <rect x="175" y="278" width="180" height="20" rx="3" fill="#1e1535"/>
  <text x="183" y="291" fill="#a78bfa" font-size="11">Stop losses parked below 108</text>
  <line x1="80"  y1="120" x2="80"  y2="200" stroke="#ef4444" stroke-width="1.5"/><rect x="68"  y="135" width="24" height="50" rx="2" fill="#ef4444"/>
  <line x1="135" y1="155" x2="135" y2="235" stroke="#ef4444" stroke-width="1.5"/><rect x="123" y="170" width="24" height="50" rx="2" fill="#ef4444"/>
  <line x1="190" y1="200" x2="190" y2="285" stroke="#ef4444" stroke-width="1.5"/><rect x="178" y="215" width="24" height="55" rx="2" fill="#ef4444"/>
  <circle cx="190" cy="285" r="5" fill="#a78bfa"/>
  <text x="155" y="308" fill="#a78bfa" font-size="10">swing low forms here</text>
  <line x1="245" y1="215" x2="245" y2="290" stroke="#22c55e" stroke-width="1.5"/><rect x="233" y="230" width="24" height="45" rx="2" fill="#22c55e"/>
  <line x1="335" y1="175" x2="335" y2="400" stroke="#eab308" stroke-width="3"/><rect x="323" y="190" width="24" height="60" rx="2" fill="#ef4444"/>
  <circle cx="335" cy="400" r="8" fill="none" stroke="#eab308" stroke-width="2.5"/>
  <text x="355" y="395" fill="#eab308" font-size="11">Stops triggered here</text>
  <text x="355" y="410" fill="#eab308" font-size="11">Big buyers absorb selling</text>
  <line x1="480" y1="180" x2="480" y2="285" stroke="#22c55e" stroke-width="1.5"/><rect x="468" y="195" width="24" height="75" rx="2" fill="#22c55e"/>
  <polygon points="480,148 470,175 490,175" fill="#22c55e"/>
  <rect x="455" y="125" width="50" height="22" rx="4" fill="#14532d"/>
  <text x="465" y="140" fill="#22c55e" font-size="13" font-weight="bold">BUY</text>
  <line x1="545" y1="140" x2="545" y2="215" stroke="#22c55e" stroke-width="1.5"/><rect x="533" y="155" width="24" height="48" rx="2" fill="#22c55e"/>
  <line x1="610" y1="105" x2="610" y2="170" stroke="#22c55e" stroke-width="1.5"/><rect x="598" y="118" width="24" height="42" rx="2" fill="#22c55e"/>
  <line x1="675" y1="82" x2="675" y2="138" stroke="#22c55e" stroke-width="1.5"/><rect x="663" y="95" width="24" height="36" rx="2" fill="#22c55e"/>
  <rect x="40" y="430" width="680" height="38" rx="5" fill="#1e293b"/>
  <text x="60" y="446" fill="#a78bfa" font-size="11">Purple dashed = swing low (liquidity level)</text>
  <text x="60" y="461" fill="#eab308" font-size="11">Yellow = sweep candle | Green = buy signal + continuation</text>
</svg>
</div>

### Entry Logic (Locked)

```
LIQUIDITY LONG SETUP

Condition 1 — Swing Low (N=2 fractal):
  low[i] < low[i-1] AND low[i] < low[i-2]
  AND low[i] < low[i+1] AND low[i] < low[i+2]
  Confirmed at bar i+2. Store low[i] as swing_low_level.

Condition 2 — Distance:
  Sweep candle must appear within 50 bars of bar i+2 (last candle of setup).
  Multiple swing lows in range: use most recently confirmed one.

Condition 3 — Sweep Candle:
  candle.low < swing_low_level   (wick pierces below)
  AND candle.close > swing_low_level  (closes back above)

Condition 4 — Confirmation Candle:
  Very next candle after sweep.
  candle.close > swing_low_level

Condition 5 — Entry:
  Enter LONG at open of candle immediately after confirmation.

Tunable: N (default 2), lookback distance (default 50 bars)
```

---

## 2. Fair Value Gap (FVG)

### Definition
A 3-candle imbalance zone where C2 moves so fast that C1's high does not overlap C3's low, leaving a price zone that was never traded. Price tends to return to fill this zone.

### Why FVG Exists
When C2 moves extremely fast, buyers and sellers never got a chance to transact in the gap zone. Unexecuted orders remain at those prices. When price returns, those waiting orders get filled and create a reaction — support for a bounce or resistance for a rejection.

**Key distinction from Liquidity:** Liquidity is about stop orders triggered at a level. FVG is about an untouched zone of unexecuted pending orders. Different reason, similar effect — price gets attracted to the level and reacts.

### Formation Rules
- Exactly 3 consecutive candles — no gaps, no extra candles between them
- C1: any candle, note its HIGH = FVG zone bottom
- C2: displacement candle between C1 and C3. No specific condition on C2 — if C3.low > C1.high, C2 was strong enough by definition
- C3: next candle where C3.low > C1.high → FVG confirmed
- FVG zone bottom = C1.high, FVG zone top = C3.low

### Penetration Depth Concept
Shallow wick touch (zone top only) = buyers were aggressive, stepped in immediately = stronger bounce.
Deep wick penetration = buyers hesitated, price had to go much deeper = weaker conviction.

Quantifiable: `depth = (retest_low - zone_top) / (zone_top - zone_bottom)` → 0% = zone top touch, 100% = zone bottom touch. Lower depth = better signal quality (future optimization parameter).

### Diagram — FVG Formation and Retest

<div style="background:#0f172a; padding:10px; border-radius:8px; margin:10px 0;">
<svg viewBox="0 0 700 480" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="700" height="480" fill="#0f172a"/>
  <text x="350" y="26" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle">Fair Value Gap (FVG) — Formation and Retest</text>
  <rect x="50"  y="42" width="230" height="330" rx="6" fill="#22c55e" opacity="0.05"/>
  <rect x="295" y="42" width="360" height="330" rx="6" fill="#3b82f6" opacity="0.05"/>
  <text x="165" y="58" fill="#64748b" font-size="11" text-anchor="middle" font-weight="bold">PHASE 1 — FVG FORMATION</text>
  <text x="475" y="58" fill="#64748b" font-size="11" text-anchor="middle" font-weight="bold">PHASE 2 — RETEST + BOUNCE</text>
  <line x1="285" y1="42" x2="285" y2="380" stroke="#1e293b" stroke-width="1.5"/>
  <line x1="50" y1="50"  x2="660" y2="50"  stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="120" x2="660" y2="120" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="190" x2="660" y2="190" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="260" x2="660" y2="260" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="330" x2="660" y2="330" stroke="#1e293b" stroke-width="0.8"/>
  <text x="44" y="54"  fill="#475569" font-size="10" text-anchor="end">125</text>
  <text x="44" y="124" fill="#475569" font-size="10" text-anchor="end">120</text>
  <text x="44" y="194" fill="#475569" font-size="10" text-anchor="end">115</text>
  <text x="44" y="264" fill="#475569" font-size="10" text-anchor="end">110</text>
  <text x="44" y="334" fill="#475569" font-size="10" text-anchor="end">105</text>
  <rect x="50" y="218" width="610" height="56" fill="#6366f1" opacity="0.18" rx="2"/>
  <line x1="50" y1="218" x2="660" y2="218" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="7,5"/>
  <line x1="50" y1="274" x2="660" y2="274" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="7,5"/>
  <rect x="55" y="229" width="100" height="30" rx="4" fill="#1e1a3d"/>
  <text x="105" y="241" fill="#a78bfa" font-size="10" text-anchor="middle" font-weight="bold">FVG ZONE</text>
  <text x="105" y="254" fill="#a78bfa" font-size="10" text-anchor="middle">109 to 113</text>
  <rect x="644" y="210" width="48" height="16" rx="3" fill="#1e1a3d"/>
  <text x="668" y="221" fill="#a78bfa" font-size="10" text-anchor="middle">113 top</text>
  <rect x="644" y="266" width="48" height="16" rx="3" fill="#1e1a3d"/>
  <text x="668" y="277" fill="#a78bfa" font-size="10" text-anchor="middle">109 bot</text>
  <line x1="90" y1="274" x2="90" y2="358" stroke="#ef4444" stroke-width="1.5"/>
  <rect x="76" y="288" width="28" height="56" rx="2" fill="#ef4444"/>
  <line x1="90" y1="274" x2="172" y2="274" stroke="#a78bfa" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="90" y="390" fill="#94a3b8" font-size="11" text-anchor="middle">C1</text>
  <text x="90" y="403" fill="#a78bfa" font-size="10" text-anchor="middle">high=109 (gap bot)</text>
  <line x1="165" y1="106" x2="165" y2="358" stroke="#22c55e" stroke-width="1.5"/>
  <rect x="151" y="120" width="28" height="224" rx="2" fill="#22c55e"/>
  <text x="165" y="390" fill="#94a3b8" font-size="11" text-anchor="middle">C2</text>
  <text x="165" y="403" fill="#22c55e" font-size="10" text-anchor="middle">displacement</text>
  <line x1="240" y1="92" x2="240" y2="218" stroke="#22c55e" stroke-width="1.5"/>
  <rect x="226" y="106" width="28" height="42" rx="2" fill="#22c55e"/>
  <line x1="226" y1="218" x2="172" y2="218" stroke="#a78bfa" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="240" y="390" fill="#94a3b8" font-size="11" text-anchor="middle">C3</text>
  <text x="240" y="403" fill="#a78bfa" font-size="10" text-anchor="middle">low=113 (gap top)</text>
  <line x1="56" y1="218" x2="56" y2="274" stroke="#a78bfa" stroke-width="2"/>
  <line x1="52" y1="218" x2="63" y2="218" stroke="#a78bfa" stroke-width="2"/>
  <line x1="52" y1="274" x2="63" y2="274" stroke="#a78bfa" stroke-width="2"/>
  <line x1="340" y1="78" x2="340" y2="162" stroke="#ef4444" stroke-width="1.5"/><rect x="326" y="92" width="28" height="56" rx="2" fill="#ef4444"/>
  <line x1="410" y1="106" x2="410" y2="204" stroke="#ef4444" stroke-width="1.5"/><rect x="396" y="120" width="28" height="70" rx="2" fill="#ef4444"/>
  <line x1="480" y1="162" x2="480" y2="288" stroke="#eab308" stroke-width="2.5"/>
  <rect x="466" y="176" width="28" height="42" rx="2" fill="#ef4444"/>
  <circle cx="480" cy="288" r="9" fill="none" stroke="#eab308" stroke-width="2"/>
  <text x="480" y="390" fill="#eab308" font-size="11" text-anchor="middle">Retest candle</text>
  <text x="480" y="403" fill="#eab308" font-size="10" text-anchor="middle">wick touches zone top</text>
  <text x="480" y="415" fill="#eab308" font-size="10" text-anchor="middle">body stays above</text>
  <line x1="550" y1="148" x2="550" y2="232" stroke="#22c55e" stroke-width="1.5"/>
  <rect x="536" y="162" width="28" height="56" rx="2" fill="#22c55e"/>
  <polygon points="550,125 540,148 560,148" fill="#22c55e"/>
  <rect x="522" y="105" width="56" height="20" rx="4" fill="#14532d"/>
  <text x="550" y="119" fill="#22c55e" font-size="13" font-weight="bold" text-anchor="middle">BUY</text>
  <text x="550" y="390" fill="#22c55e" font-size="11" text-anchor="middle">Confirmation</text>
  <line x1="620" y1="92" x2="620" y2="176" stroke="#22c55e" stroke-width="1.5"/><rect x="606" y="106" width="28" height="56" rx="2" fill="#22c55e"/>
  <rect x="50" y="430" width="610" height="36" rx="6" fill="#1e293b"/>
  <text x="84"  y="452" fill="#94a3b8" font-size="11">Purple zone = FVG (C1.high to C3.low, never traded)</text>
  <text x="390" y="452" fill="#eab308" font-size="11">Yellow = retest | Green = bounce/BUY</text>
</svg>
</div>

### Entry Logic (Locked)

```
FVG LONG SETUP

Phase 1 — Formation (3 consecutive candles):
  C1: any candle → FVG zone bottom = C1.high
  C2: any candle between C1 and C3 (no specific condition)
  C3: C3.low > C1.high → FVG confirmed
  FVG zone top = C3.low, FVG zone bottom = C1.high

Phase 2 — Rally Condition:
  In bars AFTER C3, at least one bar must have high > C3.high.
  The retest candle itself can satisfy this simultaneously.

Phase 3 — Retest Candle (within 50 bars of C3):
  candle.low <= C3.low       (wick touches/enters zone top)
  AND candle.close > C3.low  (body stays above zone top)

Phase 4 — Confirmation Candle:
  Very next candle after retest.
  candle.close > C3.low

Phase 5 — Entry:
  Enter LONG at open of candle immediately after confirmation.

Tunable: max distance C3 to retest (default 50 bars)
```

---

## 3. Order Block (OB)

### Definition
The last opposite-direction candle just before a strong impulsive displacement move. That candle's full range (high to low, including wicks) becomes the OB zone — where institutions placed large buy orders before driving price away.

### Why OB Works
The OB candle is the footprint of the last place smart money accumulated before their displacement move. When price returns to that zone, the same institutions who drove price away step back in to fill any remaining orders, creating a demand response.

### Key Differences from FVG
- FVG = 3 candles, based on a price GAP (untouched zone)
- OB = 2 candles, based on a single candle's RANGE (institutional footprint)
- OB zone = full range of OB candle (high to low, not just gap between two candles)

### Formation Rules
- 2 consecutive candles only
- OB candle: bearish (close < open) — the last red candle before the move
- Displacement candle: bullish, must close ABOVE the OB candle's high
- OB zone top = OB candle high, OB zone bottom = OB candle low (full range, wicks included)

### Penetration Depth
Same concept as FVG — shallow wick touch at zone top = stronger signal. Future optimization parameter.

`depth = (retest_low - OB_zone_top) / (OB_zone_top - OB_zone_bottom)`

### Diagram — Order Block Formation and Retest

<div style="background:#0f172a; padding:10px; border-radius:8px; margin:10px 0;">
<svg viewBox="0 0 700 480" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="700" height="480" fill="#0f172a"/>
  <text x="350" y="26" fill="#e2e8f0" font-size="15" font-weight="bold" text-anchor="middle">Order Block (OB) — Formation and Retest</text>
  <rect x="50"  y="42" width="210" height="330" rx="6" fill="#22c55e" opacity="0.05"/>
  <rect x="275" y="42" width="375" height="330" rx="6" fill="#3b82f6" opacity="0.05"/>
  <text x="155" y="58" fill="#64748b" font-size="11" text-anchor="middle" font-weight="bold">PHASE 1 — OB FORMATION</text>
  <text x="462" y="58" fill="#64748b" font-size="11" text-anchor="middle" font-weight="bold">PHASE 2 — RETEST + BOUNCE</text>
  <line x1="268" y1="42" x2="268" y2="380" stroke="#1e293b" stroke-width="1.5"/>
  <line x1="50" y1="50"  x2="660" y2="50"  stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="120" x2="660" y2="120" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="190" x2="660" y2="190" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="260" x2="660" y2="260" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="50" y1="330" x2="660" y2="330" stroke="#1e293b" stroke-width="0.8"/>
  <text x="44" y="54"  fill="#475569" font-size="10" text-anchor="end">125</text>
  <text x="44" y="124" fill="#475569" font-size="10" text-anchor="end">120</text>
  <text x="44" y="194" fill="#475569" font-size="10" text-anchor="end">115</text>
  <text x="44" y="264" fill="#475569" font-size="10" text-anchor="end">110</text>
  <text x="44" y="334" fill="#475569" font-size="10" text-anchor="end">105</text>
  <rect x="50" y="274" width="610" height="84" fill="#f59e0b" opacity="0.12" rx="2"/>
  <line x1="50" y1="274" x2="660" y2="274" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="7,5"/>
  <line x1="50" y1="358" x2="660" y2="358" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="7,5"/>
  <rect x="55" y="297" width="105" height="30" rx="4" fill="#1c1a0a"/>
  <text x="107" y="309" fill="#f59e0b" font-size="10" text-anchor="middle" font-weight="bold">ORDER BLOCK</text>
  <text x="107" y="322" fill="#f59e0b" font-size="10" text-anchor="middle">zone 103 to 109</text>
  <rect x="638" y="266" width="52" height="16" rx="3" fill="#1c1a0a"/>
  <text x="664" y="277" fill="#f59e0b" font-size="10" text-anchor="middle">109 top</text>
  <rect x="638" y="350" width="52" height="16" rx="3" fill="#1c1a0a"/>
  <text x="664" y="361" fill="#f59e0b" font-size="10" text-anchor="middle">103 bot</text>
  <line x1="80" y1="218" x2="80" y2="288" stroke="#ef4444" stroke-width="1.5"/><rect x="66" y="232" width="28" height="42" rx="2" fill="#ef4444"/>
  <line x1="145" y1="274" x2="145" y2="372" stroke="#ef4444" stroke-width="1.5"/>
  <rect x="131" y="288" width="28" height="70" rx="2" fill="#ef4444"/>
  <text x="145" y="395" fill="#f59e0b" font-size="11" text-anchor="middle">OB candle</text>
  <text x="145" y="408" fill="#f59e0b" font-size="10" text-anchor="middle">last bearish before push</text>
  <line x1="215" y1="106" x2="215" y2="372" stroke="#22c55e" stroke-width="1.5"/>
  <rect x="201" y="120" width="28" height="238" rx="2" fill="#22c55e"/>
  <text x="215" y="395" fill="#22c55e" font-size="11" text-anchor="middle">displacement</text>
  <line x1="310" y1="92" x2="310" y2="148" stroke="#22c55e" stroke-width="1.5"/><rect x="296" y="106" width="28" height="28" rx="2" fill="#22c55e"/>
  <line x1="375" y1="92" x2="375" y2="176" stroke="#ef4444" stroke-width="1.5"/><rect x="361" y="106" width="28" height="56" rx="2" fill="#ef4444"/>
  <line x1="440" y1="148" x2="440" y2="232" stroke="#ef4444" stroke-width="1.5"/><rect x="426" y="162" width="28" height="56" rx="2" fill="#ef4444"/>
  <line x1="505" y1="232" x2="505" y2="302" stroke="#eab308" stroke-width="2.5"/>
  <rect x="491" y="246" width="28" height="14" rx="2" fill="#ef4444"/>
  <circle cx="505" cy="302" r="9" fill="none" stroke="#eab308" stroke-width="2"/>
  <text x="505" y="395" fill="#eab308" font-size="11" text-anchor="middle">Retest candle</text>
  <text x="505" y="408" fill="#eab308" font-size="10" text-anchor="middle">wick touches OB top</text>
  <line x1="575" y1="162" x2="575" y2="274" stroke="#22c55e" stroke-width="1.5"/>
  <rect x="561" y="176" width="28" height="84" rx="2" fill="#22c55e"/>
  <polygon points="575,138 563,162 587,162" fill="#22c55e"/>
  <rect x="546" y="118" width="58" height="20" rx="4" fill="#14532d"/>
  <text x="575" y="132" fill="#22c55e" font-size="13" font-weight="bold" text-anchor="middle">BUY</text>
  <line x1="635" y1="106" x2="635" y2="190" stroke="#22c55e" stroke-width="1.5"/><rect x="621" y="120" width="28" height="56" rx="2" fill="#22c55e"/>
  <rect x="50" y="435" width="610" height="34" rx="6" fill="#1e293b"/>
  <text x="84"  y="452" fill="#f59e0b" font-size="11">Orange zone = OB (last bearish candle full range)</text>
  <text x="420" y="452" fill="#eab308" font-size="11">Yellow = retest | Green = BUY</text>
</svg>
</div>

### Entry Logic (Locked)

```
ORDER BLOCK (OB) LONG SETUP

Phase 1 — Formation (2 consecutive candles):
  OB candle: bearish (close < open)
  Displacement candle: bullish, close > OB candle high
  OB zone top    = OB candle high
  OB zone bottom = OB candle low (full range including wicks)

Phase 2 — Rally Condition:
  At least one candle after displacement must have high > displacement candle high.
  The retest candle itself can satisfy this simultaneously.

Phase 3 — Retest Candle (within 50 bars of displacement candle):
  candle.low <= OB zone top      (wick touches/enters zone)
  AND candle.close > OB zone top (body stays above zone)

Phase 4 — Confirmation Candle:
  Very next candle after retest.
  candle.close > OB zone top

Phase 5 — Entry:
  Enter LONG at open of candle immediately after confirmation.

Tunable: max distance displacement to retest (default 50 bars),
         penetration depth filter (future iteration)
```

---

## 4. Break of Structure (BOS)

### Definition
A candle that closes beyond the last higher low (in an uptrend) or lower high (in a downtrend), confirming the current trend structure has broken and a new direction is forming.

### How It Differs from the Other Three
Liquidity, FVG, OB = zone-based (WHERE to trade)
BOS = trend-based (WHEN conditions are right to trade in a direction)

BOS answers one question: is the current trend still intact or has it flipped?

### How It Works
- Uptrend = higher highs (HH) + higher lows (HL) consistently
- BOS to downside = one candle closes below the last HL → trend potentially flipped to downtrend
- Post-BOS = lower lows begin forming

### Role in fv2
Used as a **G1 regime gate**. Rule: only take long bounce setups (Liquidity/FVG/OB) when BOS confirms uptrend is intact. If a BOS to the downside has already happened, skip all long signals.

### Diagram — Break of Structure

<div style="background:#0f172a; padding:10px; border-radius:8px; margin:10px 0;">
<svg viewBox="0 0 700 420" xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <rect width="700" height="420" fill="#0f172a"/>
  <text x="20" y="26" fill="#e2e8f0" font-size="15" font-weight="bold">Break of Structure (BOS) — uptrend intact then broken</text>
  <line x1="32" y1="80"  x2="680" y2="80"  stroke="#1e293b"/>
  <line x1="32" y1="180" x2="680" y2="180" stroke="#1e293b"/>
  <line x1="32" y1="280" x2="680" y2="280" stroke="#1e293b"/>
  <line x1="32" y1="360" x2="680" y2="360" stroke="#1e293b"/>
  <text x="8" y="84"  fill="#64748b" font-size="11">120</text>
  <text x="8" y="184" fill="#64748b" font-size="11">113</text>
  <text x="8" y="284" fill="#64748b" font-size="11">107</text>
  <text x="8" y="364" fill="#64748b" font-size="11">102</text>
  <polyline fill="none" stroke="#22c55e" stroke-width="1.5" stroke-dasharray="5,4" points="70,310 130,200 190,270 260,120 320,210"/>
  <text x="35" y="305" fill="#22c55e" font-size="11">HL1</text>
  <text x="120" y="195" fill="#22c55e" font-size="11">HH1</text>
  <text x="178" y="265" fill="#22c55e" font-size="11">HL2</text>
  <text x="248" y="115" fill="#22c55e" font-size="11">HH2</text>
  <text x="308" y="205" fill="#22c55e" font-size="11">HL3</text>
  <line x1="320" y1="210" x2="660" y2="210" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="560" y="205" fill="#ef4444" font-size="12">BOS level (HL3)</text>
  <g stroke-width="1.5">
    <line x1="70" y1="280" x2="70" y2="330" stroke="#22c55e"/><rect x="58" y="295" width="24" height="25" fill="#22c55e"/>
    <line x1="130" y1="180" x2="130" y2="250" stroke="#22c55e"/><rect x="118" y="195" width="24" height="40" fill="#22c55e"/>
    <line x1="190" y1="230" x2="190" y2="290" stroke="#ef4444"/><rect x="178" y="245" width="24" height="30" fill="#ef4444"/>
    <line x1="260" y1="100" x2="260" y2="210" stroke="#22c55e"/><rect x="248" y="115" width="24" height="80" fill="#22c55e"/>
    <line x1="320" y1="185" x2="320" y2="240" stroke="#ef4444"/><rect x="308" y="200" width="24" height="30" fill="#ef4444"/>
    <line x1="390" y1="195" x2="390" y2="295" stroke="#eab308" stroke-width="2.5"/><rect x="378" y="215" width="24" height="60" fill="#ef4444"/>
    <line x1="460" y1="255" x2="460" y2="320" stroke="#ef4444"/><rect x="448" y="270" width="24" height="35" fill="#ef4444"/>
    <line x1="530" y1="280" x2="530" y2="355" stroke="#ef4444"/><rect x="518" y="295" width="24" height="45" fill="#ef4444"/>
    <line x1="600" y1="310" x2="600" y2="380" stroke="#ef4444"/><rect x="588" y="325" width="24" height="40" fill="#ef4444"/>
  </g>
  <circle cx="390" cy="295" r="9" fill="none" stroke="#eab308" stroke-width="2"/>
  <text x="405" y="330" fill="#eab308" font-size="12">BOS candle closes below HL3</text>
  <text x="405" y="345" fill="#eab308" font-size="12">Uptrend is now broken</text>
  <text x="60" y="60" fill="#22c55e" font-size="13" font-weight="bold">Uptrend: higher highs + higher lows</text>
  <text x="430" y="60" fill="#ef4444" font-size="13" font-weight="bold">Downtrend after BOS</text>
</svg>
</div>

### Logic (Regime Gate, Not Standalone Entry)
```
BOS REGIME CHECK

Find last confirmed higher low (HL) in uptrend.
If current candle closes BELOW that HL → BOS confirmed.
Flag: uptrend_broken = True

For fv2 long entries:
  Only take Liquidity / FVG / OB long signals
  when uptrend_broken = False.
```

---

## 5. Inducement

### Definition
A small deliberate liquidity grab just before the real move, designed to trap early entries before smart money commits to the direction.

### How It Works
Before a real bounce up from an OB/FVG/liquidity zone, price makes one small push lower — just enough to:
1. Hit stop losses of traders who entered long too early
2. Pull in new short sellers who see the "breakdown"
Once those retail traders are trapped, smart money reverses price sharply upward. Trapped shorts must cover, adding fuel to the move.

### Role in fv2
Acts as a **timing filter**. If you enter a long before the inducement plays out, your stop loss gets hit by that fake move down. Wait for the inducement to complete first.

Primary benefit: reduces SL hits from premature entries.
Secondary benefit: indirectly reduces some EOD minus outcomes by improving entry timing (entering closer to the actual move).

### Entry Logic
Not yet finalized — pending future session. Hardest of the 5 to define precisely in code.

---

## Key Principles Locked in This Session

1. **Filters upfront, not backwards.** Applying SMC filters to raw backtest results after the fact is wrong. Build the filter conditions into entry signal generation, then run a fresh backtest. Fewer trades, higher quality.

2. **Penetration depth is a future optimization parameter** for both FVG and OB. Shallow wick touch at zone top = strongest signal. Quantify and backtest by depth buckets (0-20%, 20-50%, 50-100%).

3. **50 candles** is the starting max lookback distance for all three setups (Liquidity: from swing low setup last candle; FVG: from C3; OB: from displacement candle).

4. **The retest candle can simultaneously satisfy the rally condition** in both FVG and OB setups. No need for them to be separate candles.

5. **Triple confluence** (Liquidity sweep + inside FVG zone + inside OB zone) = highest quality signal. Individual concepts give mediocre results; combined confluence is where the real edge concentrates.

---

## Backtesting Status

| Concept    | Entry Logic | Status              |
|------------|-------------|---------------------|
| Liquidity  | Locked      | Sent to backtester  |
| FVG        | Locked      | Sent to backtester  |
| OB         | Locked      | Sent to backtester  |
| BOS        | Conceptual  | Regime gate only    |
| Inducement | Conceptual  | Pending definition  |

---

*Session conducted in claude.ai chat — September 2026*
