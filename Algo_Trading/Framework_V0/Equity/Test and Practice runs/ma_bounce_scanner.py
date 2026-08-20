import requests
import time
from datetime import datetime, timedelta

# Your Upstox credentials - UPDATE THESE
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTNhNzA5OTAzZTJlODcyOGNhYTBmMzciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTQzNzU5MywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1NDkwNDAwfQ.BH7uL8T4nPNXlx-SzseXxkRKWPrHTvUdme6XMYsD7no'  # ← Put today's token here
API_KEY = '15m0va42ni'

# Headers for API calls
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

# 100+ Most liquid cheap stocks under ₹500
STOCKS = {
    # PSU Banks (Very liquid)
    'YESBANK': 'NSE_EQ|INE528G01035',
    'PNB': 'NSE_EQ|INE160A01022',
    'BANKBARODA': 'NSE_EQ|INE028A01039',
    'SBIN': 'NSE_EQ|INE062A01020',
    'CANBK': 'NSE_EQ|INE476A01022',
    'UNIONBANK': 'NSE_EQ|INE692A01016',
    'INDIANB': 'NSE_EQ|INE562A01011',
    'CENTRALBK': 'NSE_EQ|INE483A01010',
    'IOB': 'NSE_EQ|INE565A01014',
    'MAHABANK': 'NSE_EQ|INE457A01014',

    # Telecom
    'IDEA': 'NSE_EQ|INE669E01016',

    # Power & Energy
    'SUZLON': 'NSE_EQ|INE040H01021',
    'IRFC': 'NSE_EQ|INE053F01010',
    'NTPC': 'NSE_EQ|INE733E01010',
    'POWERGRID': 'NSE_EQ|INE752E01010',
    'TATAPOWER': 'NSE_EQ|INE245A01021',
    'NHPC': 'NSE_EQ|INE848E01016',
    'SJVN': 'NSE_EQ|INE002L01015',
    'RECLTD': 'NSE_EQ|INE020B01018',
    'PFC': 'NSE_EQ|INE134E01011',

    # Oil & Gas
    'IOC': 'NSE_EQ|INE242A01010',
    'ONGC': 'NSE_EQ|INE213A01029',
    'BPCL': 'NSE_EQ|INE029A01011',
    'OIL': 'NSE_EQ|INE274J01014',
    'GAIL': 'NSE_EQ|INE129A01019',

    # Metals & Mining
    'SAIL': 'NSE_EQ|INE114A01011',
    'NMDC': 'NSE_EQ|INE584A01023',
    'COALINDIA': 'NSE_EQ|INE522F01014',
    'TATASTEEL': 'NSE_EQ|INE081A01012',
    'HINDALCO': 'NSE_EQ|INE038A01020',
    'VEDL': 'NSE_EQ|INE205A01025',
    'JSWSTEEL': 'NSE_EQ|INE019A01038',
    'JINDALSTEL': 'NSE_EQ|INE749A01030',
    'HINDZINC': 'NSE_EQ|INE267A01025',

    # Auto
    'TATAMOTORS': 'NSE_EQ|INE155A01022',
    'ASHOKLEY': 'NSE_EQ|INE208A01029',
    'ESCORTS': 'NSE_EQ|INE042A01014',
    'APOLLOTYRE': 'NSE_EQ|INE438A01022',
    'MOTHERSON': 'NSE_EQ|INE775A01035',
    'CEATLTD': 'NSE_EQ|INE482A01020',
    'BALRAMCHIN': 'NSE_EQ|INE119A01028',
    'MRF': 'NSE_EQ|INE883A01011',

    # Infra & Engineering
    'L&T': 'NSE_EQ|INE018A01030',
    'BEL': 'NSE_EQ|INE263A01024',
    'BHEL': 'NSE_EQ|INE257A01026',
    'LTTS': 'NSE_EQ|INE010V01017',
    'SIEMENS': 'NSE_EQ|INE003A01024',
    'ABB': 'NSE_EQ|INE117A01022',
    'CUMMINSIND': 'NSE_EQ|INE298A01020',

    # Realty
    'DLF': 'NSE_EQ|INE271C01023',
    'GODREJPROP': 'NSE_EQ|INE484J01027',
    'OBEROIRLTY': 'NSE_EQ|INE093I01010',
    'PRESTIGE': 'NSE_EQ|INE811K01011',

    # Pharma
    'SUNPHARMA': 'NSE_EQ|INE044A01036',
    'DRREDDY': 'NSE_EQ|INE089A01023',
    'CIPLA': 'NSE_EQ|INE059A01026',
    'AUROPHARMA': 'NSE_EQ|INE406A01037',
    'LUPIN': 'NSE_EQ|INE326A01037',
    'TORNTPHARM': 'NSE_EQ|INE685A01028',
    'BIOCON': 'NSE_EQ|INE376G01013',
    'DIVISLAB': 'NSE_EQ|INE361B01024',

    # IT
    'TCS': 'NSE_EQ|INE467B01029',
    'INFY': 'NSE_EQ|INE009A01021',
    'WIPRO': 'NSE_EQ|INE075A01022',
    'HCLTECH': 'NSE_EQ|INE860A01027',
    'TECHM': 'NSE_EQ|INE669C01036',
    'LTI': 'NSE_EQ|INE214T01019',
    'MPHASIS': 'NSE_EQ|INE356A01018',
    'PERSISTENT': 'NSE_EQ|INE262H01013',

    # FMCG
    'ITC': 'NSE_EQ|INE154A01025',
    'HINDUNILVR': 'NSE_EQ|INE030A01027',
    'NESTLEIND': 'NSE_EQ|INE239A01024',
    'BRITANNIA': 'NSE_EQ|INE216A01030',
    'DABUR': 'NSE_EQ|INE016A01026',
    'MARICO': 'NSE_EQ|INE196A01026',
    'GODREJCP': 'NSE_EQ|INE102D01028',

    # Cement
    'ULTRACEMCO': 'NSE_EQ|INE481G01011',
    'SHREECEM': 'NSE_EQ|INE070A01015',
    'GRASIM': 'NSE_EQ|INE047A01021',
    'ACC': 'NSE_EQ|INE012A01025',
    'AMBUJACEM': 'NSE_EQ|INE079A01024',

    # Finance/NBFC
    'BAJFINANCE': 'NSE_EQ|INE296A01024',
    'BAJAJFINSV': 'NSE_EQ|INE918I01018',
    'LICHSGFIN': 'NSE_EQ|INE013A01015',
    'SBILIFE': 'NSE_EQ|INE123W01016',
    'HDFCLIFE': 'NSE_EQ|INE795G01014',
    'ICICIGI': 'NSE_EQ|INE765G01017',
    'SBICARD': 'NSE_EQ|INE018E01016',

    # Consumer Durables
    'VOLTAS': 'NSE_EQ|INE226A01021',
    'WHIRLPOOL': 'NSE_EQ|INE716A01013',
    'HAVELLS': 'NSE_EQ|INE176B01034',
    'CROMPTON': 'NSE_EQ|INE299U01018',

    # Retail
    'DMART': 'NSE_EQ|INE192R01011',
    'TRENT': 'NSE_EQ|INE849A01020',

    # Media
    'ZEEL': 'NSE_EQ|INE256A01028',

    # Chemicals
    'UPL': 'NSE_EQ|INE628A01036',
    'PIDILITIND': 'NSE_EQ|INE318A01026',
    'AARTI': 'NSE_EQ|INE769A01020',

    # Airlines/Transport
    'INDIGO': 'NSE_EQ|INE646L01027',

    # Hotels
    'INDHOTEL': 'NSE_EQ|INE053A01029',

    # Diversified
    'RELIANCE': 'NSE_EQ|INE002A01018',
    'ADANIENT': 'NSE_EQ|INE423A01024',
    'ADANIPORTS': 'NSE_EQ|INE742F01042',
}


def get_historical_data(instrument_key, days=50):
    """Get historical data for MA calculation"""
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')  # ← INCREASED from 60 to 100

    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/day/{to_date}/{from_date}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'candles' in data['data']:
                return data['data']['candles']
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def calculate_ma(candles, period):
    """Calculate Moving Average"""
    if not candles or len(candles) < period:
        return None

    closes = [candle[4] for candle in candles[:period]]
    return sum(closes) / period


def check_ma_bounce(stock_name, instrument_key):
    """Check if stock has MA Bounce setup"""
    candles = get_historical_data(instrument_key)

    if not candles or len(candles) < 50:
        return None, f"Not enough data"

    # Calculate MAs
    ma20 = calculate_ma(candles, 20)
    ma50 = calculate_ma(candles, 50)

    if not ma20 or not ma50:
        return None, "Can't calculate MAs"

    # Current price
    current_price = candles[0][4]

    # Check 1: Uptrend (MA20 > MA50)
    if ma20 <= ma50:
        return None, f"No uptrend"

    # Check 2: Near MA20 (within 2%)
    distance_to_ma20 = abs(current_price - ma20) / ma20 * 100
    if distance_to_ma20 > 2:
        return None, f"Too far from MA20"

    # Check 3: Above MA20
    if current_price < ma20:
        return None, f"Below MA20"

    # SIGNAL FOUND!
    entry = current_price
    stop = ma20 * 0.99  # 1% below MA20
    target = entry * 1.03  # 3% profit target
    risk = entry - stop
    reward = target - entry
    rr_ratio = reward / risk if risk > 0 else 0

    signal = {
        'stock': stock_name,
        'price': current_price,
        'ma20': ma20,
        'ma50': ma50,
        'distance': distance_to_ma20,
        'entry': entry,
        'stop': stop,
        'target': target,
        'risk': risk,
        'reward': reward,
        'rr_ratio': rr_ratio
    }

    return signal, "✅ SIGNAL!"


# Main Scanner
print("=" * 80)
print("MA BOUNCE SCANNER - 100+ STOCKS")
print("=" * 80)
print(f"⏰ Starting scan at {datetime.now().strftime('%H:%M:%S')}")
print(f"🔍 Scanning {len(STOCKS)} stocks for MA Bounce setups...\n")

signals = []
errors = []
count = 0

for stock_name, instrument_key in STOCKS.items():
    count += 1

    result, reason = check_ma_bounce(stock_name, instrument_key)

    if result:
        signals.append(result)
        print(f"{count:3d}. {stock_name:15} ✅ SIGNAL @ ₹{result['price']:.2f}")
    else:
        print(f"{count:3d}. {stock_name:15} ❌ {reason}")

    time.sleep(0.3)  # Rate limiting - 3 requests per second

print("\n" + "=" * 80)
print(f"🎯 SCAN COMPLETE: {len(signals)} SIGNAL(S) FOUND")
print("=" * 80)

if signals:
    print("\n📊 DETAILED SIGNALS:\n")
    for i, signal in enumerate(signals, 1):
        print(f"{i}. {signal['stock']}")
        print(f"   Price: ₹{signal['price']:.2f} | MA20: ₹{signal['ma20']:.2f} | MA50: ₹{signal['ma50']:.2f}")
        print(f"   Distance to MA20: {signal['distance']:.2f}%")
        print(f"   📈 Entry: ₹{signal['entry']:.2f}")
        print(f"   🛑 Stop: ₹{signal['stop']:.2f} (Risk: ₹{signal['risk']:.2f})")
        print(f"   🎯 Target: ₹{signal['target']:.2f} (Reward: ₹{signal['reward']:.2f})")
        print(f"   💰 Risk:Reward = 1:{signal['rr_ratio']:.2f}\n")
else:
    print("\n❌ No signals found. Market conditions may not be suitable for MA Bounce.")

print(f"⏰ Scan completed at {datetime.now().strftime('%H:%M:%S')}")