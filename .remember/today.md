# Session Log — 2026-06-27

## Key Work Done

### Context resumed from previous session
- fv2 baseline already locked: ma_bounce.py N=49,039 | PF=0.922 | Prof_WR=41.5%
- RSI/MACD analysis already built (rsi_macd_mfe.py) with DS3 warm-up

### Confirmed findings this session
- BHARTIARTL is best performer (PF=1.092), NOT ASHOKLEY (PF=1.054) — was listed alphabetically in formula doc
- fv2_baseline_formula.md corrected: BHARTIARTL ranked first now
- RSI/MACD 4-panel chart verified: RSI<30 PF=1.31 (n=53, too small); MACD flat across all zones

### BAJFINANCE DS3 fix attempt
- BAJFINANCE is NOT in DS3 directory — was never downloaded for DS3 (26 stocks list excluded it)
- fetch_bajfinance_ds3.py created at Framework_V1/scripts/ using Kite MCP subprocess pattern
- Failed: Kite OAuth is managed inside Claude Desktop (Electron), not accessible from CC scripts
- Impact: 26 missing trades out of 49,039 = 0.05% — negligible
- Documented in fv2_baseline_formula.md; script ready to run from Claude Desktop

### Codedex
- User opened exercise13_The_Final_Scrub.ipynb — pandas data cleaning exercise (in progress)

## Key Numbers (locked baseline)
- ma_bounce.py: N=49,039 | PF=0.922 | Prof_WR=41.5% | Net=-8,573 ATR pts
- BHARTIARTL: PF=1.092 (best) | ASHOKLEY: PF=1.054 (2nd) | DABUR: 1.023 | SUNPHARMA: 1.012
- RSI<30 bucket: PF=1.31, n=53 — signal exists but sample too small to rely on alone
