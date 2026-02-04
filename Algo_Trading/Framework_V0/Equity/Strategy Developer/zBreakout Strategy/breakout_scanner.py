import upstox_client
from datetime import datetime, timedelta
import time

# Hardcode token
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 70)
print("BREAKOUT SCANNER - 52-WEEK HIGH STRATEGY")
print("=" * 70)

# Same 93 stocks from MA Bounce scanner
# 100 STOCKS - Mixed prices for zBreakout Strategy
STOCKS = {
    # Under ₹50 (3 stocks)
    'YESBANK': 'NSE_EQ|INE528G01035',  # ₹22
    'IDEA': 'NSE_EQ|INE669E01016',  # ₹12
    'SUZLON': 'NSE_EQ|INE040H01021',  # ₹60

    # ₹50-100 (4 stocks)
    'NMDC': 'NSE_EQ|INE584A01023',  # ₹75
    'SJVN': 'NSE_EQ|INE002L01015',  # ₹120
    'NHPC': 'NSE_EQ|INE848E01016',  # ₹76
    'RPOWER': 'NSE_EQ|INE191H01014',  # ₹15

    # ₹100-200 (15 stocks)
    'PNB': 'NSE_EQ|INE160A01022',  # ₹100
    'SAIL': 'NSE_EQ|INE114A01011',  # ₹130
    'IRFC': 'NSE_EQ|INE053F01010',  # ₹111
    'ZEEL': 'NSE_EQ|INE256A01028',  # ₹94
    'CANBK': 'NSE_EQ|INE476A01022',  # ₹105
    'BANKBARODA': 'NSE_EQ|INE028A01039',  # ₹245
    'UNIONBANK': 'NSE_EQ|INE692A01016',  # ₹120
    'INDIANB': 'NSE_EQ|INE562A01011',  # ₹540
    'IOB': 'NSE_EQ|INE565A01014',  # ₹60
    'BANKINDIA': 'NSE_EQ|INE084A01016',  # ₹115
    'CENTRALBK': 'NSE_EQ|INE483A01010',  # ₹58
    'MAHABANK': 'NSE_EQ|INE457A01014',  # ₹50
    'JSWENERGY': 'NSE_EQ|INE121E01018',  # ₹560
    'TATAPOWER': 'NSE_EQ|INE245A01021',  # ₹440
    'TORNTPOWER': 'NSE_EQ|INE813H01021',  # ₹1,600

    # ₹200-400 (20 stocks)
    'IOC': 'NSE_EQ|INE242A01010',  # ₹165
    'ONGC': 'NSE_EQ|INE213A01029',  # ₹285
    'BPCL': 'NSE_EQ|INE029A01011',  # ₹310
    'GAIL': 'NSE_EQ|INE129A01019',  # ₹205
    'HPCL': 'NSE_EQ|INE094A01015',  # ₹405
    'HINDALCO': 'NSE_EQ|INE038A01020',  # ₹650
    'VEDL': 'NSE_EQ|INE205A01025',  # ₹460
    'TATAMOTORS': 'NSE_EQ|INE155A01022',  # ₹780
    'GMRINFRA': 'NSE_EQ|INE776C01039',  # ₹80
    'ADANIPOWER': 'NSE_EQ|INE814H01011',  # ₹580
    'JSWSTEEL': 'NSE_EQ|INE019A01038',  # ₹990
    'TATASTEEL': 'NSE_EQ|INE081A01020',  # ₹145
    'JINDALSTEL': 'NSE_EQ|INE749A01030',  # ₹950
    'AUROPHARMA': 'NSE_EQ|INE406A01037',  # ₹1,260
    'COALINDIA': 'NSE_EQ|INE522F01014',  # ₹380
    'NTPC': 'NSE_EQ|INE733E01010',  # ₹370
    'POWERGRID': 'NSE_EQ|INE752E01010',  # ₹335
    'RECLTD': 'NSE_EQ|INE020B01018',  # ₹530
    'PFC': 'NSE_EQ|INE134E01011',  # ₹495
    'ITC': 'NSE_EQ|INE154A01025',  # ₹403

    # ₹400-800 (18 stocks)
    'SUNPHARMA': 'NSE_EQ|INE044A01036',  # ₹1,810
    'CIPLA': 'NSE_EQ|INE059A01026',  # ₹1,520
    'DRREDDY': 'NSE_EQ|INE089A01023',  # ₹1,275
    'DIVISLAB': 'NSE_EQ|INE361B01024',  # ₹6,100
    'AMBUJACEM': 'NSE_EQ|INE079A01024',  # ₹585
    'ACC': 'NSE_EQ|INE012A01025',  # ₹2,145
    'ULTRACEM': 'NSE_EQ|INE481G01011',  # ₹11,695
    'GRASIM': 'NSE_EQ|INE047A01021',  # ₹2,720
    'ASHOKLEY': 'NSE_EQ|INE208A01029',  # ₹230
    'M&M': 'NSE_EQ|INE101A01026',  # ₹3,015
    'EICHERMOT': 'NSE_EQ|INE066A01021',  # ₹4,995
    'SBIN': 'NSE_EQ|INE062A01020',  # ₹850
    'AXISBANK': 'NSE_EQ|INE238A01034',  # ₹1,135
    'FEDERALBNK': 'NSE_EQ|INE171A01029',  # ₹215
    'DABUR': 'NSE_EQ|INE016A01026',  # ₹515
    'GODREJCP': 'NSE_EQ|INE102D01028',  # ₹1,190
    'MARICO': 'NSE_EQ|INE196A01026',  # ₹630
    'HAVELLS': 'NSE_EQ|INE176B01034',  # ₹1,710

    # ₹800-1500 (20 stocks)
    'BAJAJ-AUTO': 'NSE_EQ|INE917I01010',  # ₹9,075
    'HEROMOTOCO': 'NSE_EQ|INE158A01026',  # ₹4,350
    'TVSMOTOR': 'NSE_EQ|INE494B01023',  # ₹2,550
    'MARUTI': 'NSE_EQ|INE585B01010',  # ₹11,100
    'TECHM': 'NSE_EQ|INE669C01036',  # ₹1,680
    'WIPRO': 'NSE_EQ|INE075A01022',  # ₹310
    'TCS': 'NSE_EQ|INE467B01029',  # ₹3,198
    'INFY': 'NSE_EQ|INE009A01021',  # ₹1,611
    'LTI': 'NSE_EQ|INE214T01019',  # ₹6,455
    'LTIM': 'NSE_EQ|INE214T01019',  # ₹6,455
    'COFORGE': 'NSE_EQ|INE591G01017',  # ₹9,010
    'MPHASIS': 'NSE_EQ|INE356A01018',  # ₹3,090
    'INDUSINDBK': 'NSE_EQ|INE095A01012',  # ₹955
    'ICICIBANK': 'NSE_EQ|INE090A01021',  # ₹1,280
    'BRITANNIA': 'NSE_EQ|INE216A01030',  # ₹4,860
    'COLPAL': 'NSE_EQ|INE259A01022',  # ₹2,870
    'BHARATFORG': 'NSE_EQ|INE465A01025',  # ₹1,370
    'CUMMINSIND': 'NSE_EQ|INE298A01020',  # ₹3,550
    'ABB': 'NSE_EQ|INE117A01022',  # ₹7,300
    'VOLTAS': 'NSE_EQ|INE226A01021',  # ₹1,745

    # ₹1500+ (20 stocks)
    'HDFCBANK': 'NSE_EQ|INE040A01034',  # ₹1,845
    'KOTAKBANK': 'NSE_EQ|INE237A01028',  # ₹1,760
    'HINDUNILVR': 'NSE_EQ|INE030A01027',  # ₹2,420
    'SIEMENS': 'NSE_EQ|INE003A01024',  # ₹7,735
    'DLF': 'NSE_EQ|INE271C01023',  # ₹860
    'GODREJPROP': 'NSE_EQ|INE484J01027',  # ₹2,950
    'OBEROIRLTY': 'NSE_EQ|INE093I01010',  # ₹2,115
    'PRESTIGE': 'NSE_EQ|INE811K01011',  # ₹1,795
    'L&T': 'NSE_EQ|INE018A01030',  # ₹3,750
    'ADANIPORTS': 'NSE_EQ|INE742F01042',  # ₹1,270
    'ADANIENT': 'NSE_EQ|INE423A01024',  # ₹2,530
    'ADANIGREEN': 'NSE_EQ|INE364U01010',  # ₹1,845
    'RELIANCE': 'NSE_EQ|INE002A01018',  # ₹1,543
    'SHREECEM': 'NSE_EQ|INE070A01015',  # ₹26,000
    'ASIANPAINT': 'NSE_EQ|INE021A01026',  # ₹2,485
    'BHARTIARTL': 'NSE_EQ|INE397D01024',  # ₹1,800
    'APOLLOHOSP': 'NSE_EQ|INE437A01024',  # ₹7,230
    'DMART': 'NSE_EQ|INE192R01011',  # ₹3,630
    'TITAN': 'NSE_EQ|INE280A01028',  # ₹3,510
    'NESTLEIND': 'NSE_EQ|INE239A01016',  # ₹2,180
    'HCLTECH': 'NSE_EQ|INE860A01027',  # ₹1,945
    'BAJFINANCE': 'NSE_EQ|INE296A01024',  # ₹7,150
    'PIDILITIND': 'NSE_EQ|INE318A01026',  # ₹3,145
    'BERGEPAINT': 'NSE_EQ|INE463A01038',  # ₹470
}


def check_breakout_signal(stock_name, instrument_key):
    """Check if stock has breakout setup"""
    try:
        history_api = upstox_client.HistoryApi(api_client)

        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year

        candles = history_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            interval='day',
            to_date=to_date,
            from_date=from_date,
            api_version='2.0'
        )

        if not candles.data or not candles.data.candles:
            return None

        # Parse data: [timestamp, open, high, low, close, volume, oi]
        prices = [float(candle[4]) for candle in candles.data.candles]  # Close
        highs = [float(candle[2]) for candle in candles.data.candles]  # High
        volumes = [float(candle[5]) for candle in candles.data.candles]  # Volume

        prices.reverse()
        highs.reverse()
        volumes.reverse()

        if len(prices) < 252:  # Need ~1 year of data
            return None

        # Current data
        current_price = prices[-1]
        prev_high = highs[-2] if len(highs) > 1 else current_price
        today_volume = volumes[-1]

        # Calculate 52-week high
        high_52w = max(highs[-252:])  # Last 252 trading days

        # Calculate average volume (last 20 days)
        avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else today_volume

        # Breakout conditions
        distance_to_high = ((current_price / high_52w) - 1) * 100
        near_high = distance_to_high >= -2  # Within 2% of 52W high
        breaks_high = current_price > prev_high  # Today's close > yesterday's high
        high_volume = today_volume > (avg_volume * 1.5)  # 1.5x average volume

        signal = {
            'stock': stock_name,
            'price': current_price,
            'high_52w': high_52w,
            'distance': distance_to_high,
            'volume_ratio': today_volume / avg_volume if avg_volume > 0 else 0,
            'near_high': near_high,
            'breaks_high': breaks_high,
            'high_volume': high_volume,
            'signal': near_high and breaks_high and high_volume
        }

        return signal

    except Exception as e:
        return None


# Main scan
print(f"\n⏰ Scanning at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📊 Checking {len(STOCKS)} stocks for BREAKOUT signals...\n")

signals_found = []
checked = 0

for stock_name, instrument_key in STOCKS.items():
    signal = check_breakout_signal(stock_name, instrument_key)
    checked += 1

    if signal and signal['signal']:
        signals_found.append(signal)
        print(f"   ✅ {stock_name} - BREAKOUT DETECTED!")
    else:
        print(f"   ⏳ {checked}/{len(STOCKS)} checked...", end='\r')

    time.sleep(0.5)

print("\n")
print("=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

if signals_found:
    print(f"\n🚀 {len(signals_found)} BREAKOUT SIGNAL(S) FOUND:\n")
    for sig in signals_found:
        print(f"{'=' * 70}")
        print(f"📈 {sig['stock']} @ ₹{sig['price']:.2f}")
        print(f"   52-Week High: ₹{sig['high_52w']:.2f}")
        print(f"   Distance to High: {sig['distance']:.2f}%")
        print(f"   Volume: {sig['volume_ratio']:.1f}x average")
        print(f"\n   ✅ Near 52W High: {'YES' if sig['near_high'] else 'NO'}")
        print(f"   ✅ Breaks Yesterday's High: {'YES' if sig['breaks_high'] else 'NO'}")
        print(f"   ✅ High Volume: {'YES' if sig['high_volume'] else 'NO'}")
        print(f"\n   Trade Setup:")
        print(f"   → Entry: ₹{sig['price']:.2f}")
        print(f"   → Stop-Loss: ₹{sig['high_52w'] * 0.97:.2f} (3% below 52W high)")
        print(f"   → Target: ₹{sig['price'] * 1.08:.2f} (+8%)")
        print()
else:
    print("\n⚠️  No breakout signals found.")
    print("   Breakouts are rarer than MA Bounce - check again tomorrow!")

print("=" * 70)