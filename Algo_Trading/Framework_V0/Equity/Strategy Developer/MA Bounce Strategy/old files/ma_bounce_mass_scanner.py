import upstox_client
import pandas as pd
from datetime import datetime, timedelta
import time

# Hardcode token
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 70)
print("MA BOUNCE MASS SCANNER - 50+ CHEAP STOCKS")
print("=" * 70)

# 50+ cheap liquid stocks (under ₹300)
# 100+ cheap liquid stocks (under ₹500)
STOCKS = {
    # Under ₹50
    'YESBANK': 'NSE_EQ|INE528G01035',
    'IDEA': 'NSE_EQ|INE669E01016',
    'SUZLON': 'NSE_EQ|INE040H01021',
    'TATASTEEL': 'NSE_EQ|INE081A01020',  # Check current price

    # ₹50-100
    'NMDC': 'NSE_EQ|INE584A01023',
    'SJVN': 'NSE_EQ|INE002L01015',
    'NHPC': 'NSE_EQ|INE848E01016',
    'RPOWER': 'NSE_EQ|INE191H01014',

    # ₹100-150
    'PNB': 'NSE_EQ|INE160A01022',
    'SAIL': 'NSE_EQ|INE114A01011',
    'IRFC': 'NSE_EQ|INE053F01010',
    'ZEEL': 'NSE_EQ|INE256A01028',
    'CANBK': 'NSE_EQ|INE476A01022',
    'BANKBARODA': 'NSE_EQ|INE028A01039',
    'UNIONBANK': 'NSE_EQ|INE692A01016',
    'INDIANB': 'NSE_EQ|INE562A01011',
    'IOB': 'NSE_EQ|INE565A01014',
    'BANKINDIA': 'NSE_EQ|INE084A01016',
    'CENTRALBK': 'NSE_EQ|INE483A01010',
    'MAHABANK': 'NSE_EQ|INE457A01014',
    'JSWENERGY': 'NSE_EQ|INE121E01018',

    # ₹150-250
    'IOC': 'NSE_EQ|INE242A01010',
    'ONGC': 'NSE_EQ|INE213A01029',
    'BPCL': 'NSE_EQ|INE029A01011',
    'GAIL': 'NSE_EQ|INE129A01019',
    'HPCL': 'NSE_EQ|INE094A01015',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'VEDL': 'NSE_EQ|INE205A01025',
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'GMRINFRA': 'NSE_EQ|INE776C01039',
    'ADANIPOWER': 'NSE_EQ|INE814H01011',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'TATASTEEL': 'NSE_EQ|INE081A01020',
    'JINDALSTEL': 'NSE_EQ|INE749A01030',
    'AUROPHARMA': 'NSE_EQ|INE406A01037',
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'CIPLA': 'NSE_EQ|INE059A01026',
    'DRREDDY': 'NSE_EQ|INE089A01023',
    'DIVISLAB': 'NSE_EQ|INE361B01024',

    # ₹250-400
    'COALINDIA': 'NSE_EQ|INE522F01014',
    'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    'RECLTD': 'NSE_EQ|INE020B01018',
    'PFC': 'NSE_EQ|INE134E01011',
    'AMBUJACEM': 'NSE_EQ|INE079A01024',
    'ACC': 'NSE_EQ|INE012A01025',
    'ULTRACEM': 'NSE_EQ|INE481G01011',
    'SHREECEM': 'NSE_EQ|INE070A01015',
    'GRASIM': 'NSE_EQ|INE047A01021',
    'ASHOKLEY': 'NSE_EQ|INE208A01029',
    'M&M': 'NSE_EQ|INE101A01026',
    'EICHERMOT': 'NSE_EQ|INE066A01021',
    'BAJAJ-AUTO': 'NSE_EQ|INE917I01010',
    'HEROMOTOCO': 'NSE_EQ|INE158A01026',
    'TVSMOTOR': 'NSE_EQ|INE494B01023',
    'MARUTI': 'NSE_EQ|INE585B01010',

    # Tech/IT (₹200-500)
    'TECHM': 'NSE_EQ|INE669C01036',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'LTI': 'NSE_EQ|INE214T01019',
    'COFORGE': 'NSE_EQ|INE591G01017',
    'MPHASIS': 'NSE_EQ|INE356A01018',
    'LTIM': 'NSE_EQ|INE214T01019',

    # Telecom/Media
    'BHARTIARTL': 'NSE_EQ|INE397D01024',

    # Financial Services
    'SBIN': 'NSE_EQ|INE062A01020',
    'AXISBANK': 'NSE_EQ|INE238A01034',
    'ICICIBANK': 'NSE_EQ|INE090A01021',
    'HDFCBANK': 'NSE_EQ|INE040A01034',
    'KOTAKBANK': 'NSE_EQ|INE237A01028',
    'INDUSINDBK': 'NSE_EQ|INE095A01012',
    'FEDERALBNK': 'NSE_EQ|INE171A01029',

    # Consumer/Retail
    'ITC': 'NSE_EQ|INE154A01025',
    'HINDUNILVR': 'NSE_EQ|INE030A01027',
    'BRITANNIA': 'NSE_EQ|INE216A01030',
    'DABUR': 'NSE_EQ|INE016A01026',
    'GODREJCP': 'NSE_EQ|INE102D01028',
    'MARICO': 'NSE_EQ|INE196A01026',
    'COLPAL': 'NSE_EQ|INE259A01022',

    # Telecom Equipment
    'BHARATFORG': 'NSE_EQ|INE465A01025',
    'CUMMINSIND': 'NSE_EQ|INE298A01020',
    'ABB': 'NSE_EQ|INE117A01022',
    'SIEMENS': 'NSE_EQ|INE003A01024',
    'HAVELLS': 'NSE_EQ|INE176B01034',
    'VOLTAS': 'NSE_EQ|INE226A01021',

    # Real Estate/Infra
    'DLF': 'NSE_EQ|INE271C01023',
    'GODREJPROP': 'NSE_EQ|INE484J01027',
    'OBEROIRLTY': 'NSE_EQ|INE093I01010',
    'PRESTIGE': 'NSE_EQ|INE811K01011',
    'L&T': 'NSE_EQ|INE018A01030',

    # Misc
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
    'ADANIENT': 'NSE_EQ|INE423A01024',
    'ADANIGREEN': 'NSE_EQ|INE364U01010',
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'TATAPOWER': 'NSE_EQ|INE245A01021',
    'TORNTPOWER': 'NSE_EQ|INE813H01021',
    'BHARATFORG': 'NSE_EQ|INE465A01025',
}


def calculate_ma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def check_signal(stock_name, instrument_key):
    try:
        history_api = upstox_client.HistoryApi(api_client)

        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        candles = history_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            interval='day',
            to_date=to_date,
            from_date=from_date,
            api_version='2.0'
        )

        if not candles.data or not candles.data.candles:
            return None

        prices = [float(candle[4]) for candle in candles.data.candles]
        prices.reverse()

        if len(prices) < 50:
            return None

        current_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 else current_price

        ma20 = calculate_ma(prices, 20)
        ma50 = calculate_ma(prices, 50)

        if not ma20 or not ma50:
            return None

        distance = ((current_price - ma20) / ma20) * 100
        uptrend = ma20 > ma50
        near_ma20 = abs(distance) <= 2
        bouncing = current_price > prev_price

        if uptrend and near_ma20 and bouncing:
            return {
                'stock': stock_name,
                'price': current_price,
                'ma20': ma20,
                'ma50': ma50,
                'distance': distance
            }
        return None

    except Exception as e:
        return None


# Scan all stocks
print(f"\n⏰ Scanning {len(STOCKS)} stocks...\n")
print("🔍 Checking (this may take 1-2 minutes)...")

signals = []
checked = 0

for stock_name, instrument_key in STOCKS.items():
    signal = check_signal(stock_name, instrument_key)
    checked += 1

    if signal:
        signals.append(signal)
        print(f"   ✅ {stock_name} - SIGNAL FOUND!")
    else:
        print(f"   ⏳ {checked}/{len(STOCKS)} checked...", end='\r')

    time.sleep(0.5)  # Rate limiting

print("\n")
print("=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

if signals:
    print(f"\n🎯 {len(signals)} MA BOUNCE SIGNAL(S) FOUND:\n")
    for sig in signals:
        print(f"{'=' * 70}")
        print(f"📈 {sig['stock']} @ ₹{sig['price']:.2f}")
        print(f"   MA20: ₹{sig['ma20']:.2f} | MA50: ₹{sig['ma50']:.2f}")
        print(f"   Distance to MA20: {sig['distance']:.2f}%")
        print(f"\n   Trade Setup:")
        print(f"   → Entry: ₹{sig['price']:.2f}")
        print(f"   → Stop-Loss: ₹{sig['ma20'] * 0.99:.2f}")
        print(f"   → Target: ₹{sig['price'] * 1.03:.2f} (+3%)")
        print()
else:
    print("\n⚠️  No signals found in scanned stocks.")
    print("   Try again later or add more stocks to the list!")

print("=" * 70)