import upstox_client
import pandas as pd
from datetime import datetime, timedelta
import time

# Hardcode token
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

# Configure
configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 70)
print("MA BOUNCE LIVE SIGNAL DETECTOR")
print("=" * 70)

# Stocks to monitor (add more if you want)
STOCKS = {
    # Under ₹50
    'YESBANK': 'NSE_EQ|INE528G01035',  # ~₹22
    'IDEA': 'NSE_EQ|INE669E01016',  # ~₹12
    'SUZLON': 'NSE_EQ|INE040H01021',  # ~₹60

    # ₹50-150
    'NMDC': 'NSE_EQ|INE584A01023',  # ~₹70
    'PNB': 'NSE_EQ|INE160A01022',  # ~₹100
    'SAIL': 'NSE_EQ|INE114A01011',  # ~₹120
    'IRFC': 'NSE_EQ|INE053F01010',  # ~₹111
    'ZEEL': 'NSE_EQ|INE256A01028',  # ~₹130

    # ₹150-300
    'NHPC': 'NSE_EQ|INE848E01016',  # ~₹80
    'SJVN': 'NSE_EQ|INE002L01015',  # ~₹120
}

def calculate_ma(prices, period):
    """Calculate moving average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def check_ma_bounce_signal(stock_name, instrument_key):
    """Check if stock has MA Bounce setup"""
    try:
        # Get historical data (last 60 days for MA50 calculation)
        history_api = upstox_client.HistoryApi(api_client)

        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # Get daily candles
        candles = history_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            interval='day',
            to_date=to_date,
            from_date=from_date,
            api_version='2.0'
        )

        if not candles.data or not candles.data.candles:
            return None

        # Parse data
        prices = [float(candle[4]) for candle in candles.data.candles]  # Close prices
        prices.reverse()  # Order: oldest to newest

        if len(prices) < 50:
            return None

        # Calculate MAs
        current_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 else current_price

        ma20 = calculate_ma(prices, 20)
        ma50 = calculate_ma(prices, 50)

        if not ma20 or not ma50:
            return None

        # Check MA Bounce conditions
        distance_to_ma20 = ((current_price - ma20) / ma20) * 100
        is_uptrend = ma20 > ma50
        is_near_ma20 = abs(distance_to_ma20) <= 2  # Within 2% of MA20
        is_bouncing = current_price > prev_price  # Rising today

        signal = {
            'stock': stock_name,
            'price': current_price,
            'ma20': ma20,
            'ma50': ma50,
            'distance': distance_to_ma20,
            'uptrend': is_uptrend,
            'near_ma20': is_near_ma20,
            'bouncing': is_bouncing,
            'signal': is_uptrend and is_near_ma20 and is_bouncing
        }

        return signal

    except Exception as e:
        print(f"   Error checking {stock_name}: {e}")
        return None


# Main scan
print(f"\n⏰ Scanning at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

signals_found = []

for stock_name, instrument_key in STOCKS.items():
    print(f"📊 Checking {stock_name}...")
    signal = check_ma_bounce_signal(stock_name, instrument_key)

    if signal:
        print(f"   Price: ₹{signal['price']:.2f}")
        print(f"   MA20: ₹{signal['ma20']:.2f} | MA50: ₹{signal['ma50']:.2f}")
        print(f"   Distance to MA20: {signal['distance']:.2f}%")
        print(f"   Uptrend: {'✅' if signal['uptrend'] else '❌'}")
        print(f"   Near MA20: {'✅' if signal['near_ma20'] else '❌'}")
        print(f"   Bouncing: {'✅' if signal['bouncing'] else '❌'}")

        if signal['signal']:
            print(f"   🔥 SIGNAL DETECTED! MA BOUNCE SETUP!")
            signals_found.append(signal)

        print()

    time.sleep(1)  # Rate limiting

# Summary
print("=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

if signals_found:
    print(f"\n🎯 {len(signals_found)} MA BOUNCE SIGNAL(S) FOUND:\n")
    for sig in signals_found:
        print(f"   {sig['stock']} @ ₹{sig['price']:.2f}")
        print(f"   → Entry: ₹{sig['price']:.2f}")
        print(f"   → Stop-Loss: ₹{sig['ma20'] * 0.99:.2f} (1% below MA20)")
        print(f"   → Target: ₹{sig['price'] * 1.03:.2f} (+3%)")
        print()
else:
    print("\n⚠️  No MA Bounce signals detected at this time.")
    print("   Check again later or scan more stocks!")

print("=" * 70)