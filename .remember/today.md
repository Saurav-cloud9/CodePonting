# Session Log — 2026-07-21

## 6BCE VWAP — validation + charts

### Grok script validated
- Logic review: VWAP formula correct (TP=(H+L+C)/3, intraday reset), strict close<VWAP, exit priority correct, Zerodha SHORT charges correct, daily ZSh(D) correct
- Spot-check SL=4.0/TP=6.0: CC got N=71,873 / ZPF=0.895 / ZSh(D)=-1.319 — exact match with Grok
- Minor flag: np.isnan(vwap) doesn't catch inf (if volume=0), low risk in practice

### ConsScr computed and verified
- SL=4.0/TP=6.0 (Best ZPF): ConsScr=-2.905 — matches Grok exactly
- SL=6.0/TP=6.0 (Best ConsScr): ConsScr=-2.709 — matches Grok exactly
- Locked SL=6.0/TP=6.0 as best combo for 6BCE VWAP variant

### Equity + drawdown chart
- chart_equity_6bce_vwap.py built and run
- N=70,269 / ZPF=0.8916 / PeakEquity=₹1,122 / MaxDD=₹-16,288
- VWAP filter nearly halves max drawdown vs baseline (₹-28,494)
- Both still FAIL (ZPF<1.0)

## Terminology
- SL/TP locked as standard going forward (replacing SL/TGT)
- Glossary updated in TODO.md

## Strategic direction — regime adaptive model
- 6 months of static regime filter attempts all failed OOS
- MemLabs video 2 (How to handle Regime Changes) identified as the right approach
  - 4 methods: sliding window, hidden states, online learning, RL+entropy
  - Online learning (passive aggressive regressor) most directly applicable
  - Key idea: model updates weights on every new data point, not frozen after training
- Concept is instrument-agnostic — confirmed applicable to NSE stocks
- MemLabs notebook ($5.50) attempted purchase — card declined, retry tomorrow
- Decision: buy notebook as reference, adapt to NSE stocks with CC

## Key numbers
- 6BCE baseline best: SL=6.0/TP=6.0, ZPF=0.888, MaxDD=₹-28,494
- 6BCE VWAP best consistency: SL=6.0/TP=6.0, ZPF=0.892, MaxDD=₹-16,288
