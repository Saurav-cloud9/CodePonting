import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from kiteconnect import KiteConnect

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv('KITE_API_KEY')
ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

SYMBOL = "TMPV"  # Tata Motors Passenger Vehicles - continuing entity for the old TATAMOTORS instrument (884737)
quote = kite.ltp([f"NSE:{SYMBOL}"])
instrument_token = quote[f"NSE:{SYMBOL}"]["instrument_token"]
print(f"{SYMBOL} instrument_token: {instrument_token}")

to_date = datetime.now()
from_date = to_date - timedelta(days=5)

candles = kite.historical_data(
    instrument_token,
    from_date=from_date,
    to_date=to_date,
    interval="5minute",
)

print(f"\nFetched {len(candles)} 5-min candles from {from_date.date()} to {to_date.date()}")
print("\nLast 5 candles:")
for c in candles[-5:]:
    print(c)
