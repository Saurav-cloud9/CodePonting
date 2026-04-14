# Session Log — 2026-04-13

## What was done
- Continued signal review from previous session (POWERGRID + TATAMOTORS)
- Fixed H1.1 row counter bug — regex now [A-Z]{4,} to exclude gate labels (G5b, G2 etc)
- Fixed POWERGRID signal numbering — #13→#9, #13→#1, table reordered 1–9
- HDFCBANK numbering fixed — #4/#5 → #1/#2
- H1.1: IndexedDB folder persistence added — no more picker on every open
- H1.1: Final comment removed from detail section (was duplicate of Notes column)
- TATAMOTORS signal review started — #1 (rejected, opening bar) and #2 (Win) logged
- wick_defence_ratio implemented — replaces lower_wick_pct
  Formula: (min(O,C)−MA) / (MA−low), threshold ≥1.0, green/red in Value column
- Feedback table format agreed: # | Param | Gate | Your Call | My Verdict | Your Comment | Notes

## Key findings this session
- wick_defence_ratio is a better metric than lower_wick_pct — captures MA defence quality not just wick length
- TATAMOTORS #2: G1+G3+G5 all pass despite G2 weakness — signal wins. Pattern to watch.
- Row counter bug root cause: param rows like "| 12 | G5b |" matched old regex → max=12 → nextNum=13

## Status at SS
- 9 POWERGRID + 2 HDFCBANK + 2 TATAMOTORS = 13 signals reviewed total
- H1.1 stable and working correctly
- Next: continue TATAMOTORS signal review
