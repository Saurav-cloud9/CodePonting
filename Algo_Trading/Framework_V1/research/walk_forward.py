"""
WALK-FORWARD VALIDATION

Responsibility:
- Split data into rolling train/test windows.
- Optimize on past window.
- Evaluate on next unseen window.

Rules:
- Does NOT change core strategy logic.
- Uses the same engine and adapters.
- Produces comparative statistics only.

Purpose:
- Detect look-ahead bias and parameter fragility.
"""
