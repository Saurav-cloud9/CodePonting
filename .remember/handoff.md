# Handoff Note — 2026-05-13

## State
max_tb_gap added as p10, G3a→p11, G3b→p12. CSV re-exported with 12 params.
Line-by-line review of export_h5_signals.py paused at line 46.

## Next
1. Continue line-by-line review from line 47
2. Upload new CSV to H5 Lite, validate p10 slider
3. H5 Lite chart refinement (P1)

## Known Issues
- p03=0 for 65/100 signals — expected after T0 fix, not a bug
- CSV column names have trailing spaces — handled in script (str.strip() on load)
