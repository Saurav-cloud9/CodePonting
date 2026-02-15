import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.indicators import (
    add_intraday_indicators,
    compute_daily_mas,  # Fixed name
    add_atr
)
from core.engine import BacktestEngine

print("SUCCESS: All imports from core modules working correctly")