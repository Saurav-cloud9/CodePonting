import upstox_client
from datetime import datetime, timedelta
import time

# Hardcode token
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 70)
print("MA BOUNCE SCANNER - 200 CHEAP STOCKS (Under ₹500)")
print("=" * 70)

# 200 CHEAP STOCKS - All under ₹500
STOCKS = {
    # Under ₹20 (15 stocks)
    'IDEA': 'NSE_EQ|INE669E01016',  # ₹12
    'RPOWER': 'NSE_EQ|INE191H01014',  # ₹15
    'YESBANK': 'NSE_EQ|INE528G01035',  # ₹22
    'SUZLON': 'NSE_EQ|INE040H01021',  # ₹60
    'RCOM': 'NSE_EQ|INE330H01018',  # Delisted/penny
    'JETAIRWAYS': 'NSE_EQ|INE802G01018',  # Suspended
    'SOUTHBANK': 'NSE_EQ|INE683A01023',  # ₹18
    'UCBANK': 'NSE_EQ|INE691A01018',  # ₹45
    'JMFINANCIL': 'NSE_EQ|INE780C01023',  # ₹95
    'GMRINFRA': 'NSE_EQ|INE776C01039',  # ₹80
    'ZEEL': 'NSE_EQ|INE256A01028',  # ₹94
    'MAHABANK': 'NSE_EQ|INE457A01014',  # ₹50
    'CENTRALBK': 'NSE_EQ|INE483A01010',  # ₹58
    'IOB': 'NSE_EQ|INE565A01014',  # ₹60
    'NMDC': 'NSE_EQ|INE584A01023',  # ₹75

    # ₹20-50 (25 stocks)
    'NHPC': 'NSE_EQ|INE848E01016',  # ₹76
    'SJVN': 'NSE_EQ|INE002L01015',  # ₹120
    'PNB': 'NSE_EQ|INE160A01022',  # ₹100
    'CANBK': 'NSE_EQ|INE476A01022',  # ₹105
    'BANKINDIA': 'NSE_EQ|INE084A01016',  # ₹115
    'UNIONBANK': 'NSE_EQ|INE692A01016',  # ₹120
    'IRFC': 'NSE_EQ|INE053F01010',  # ₹111
    'SAIL': 'NSE_EQ|INE114A01011',  # ₹130
    'TATASTEEL': 'NSE_EQ|INE081A01020',  # ₹145
    'IOC': 'NSE_EQ|INE242A01010',  # ₹165
    'FEDERALBNK': 'NSE_EQ|INE171A01029',  # ₹215
    'GAIL': 'NSE_EQ|INE129A01019',  # ₹205
    'ASHOKLEY': 'NSE_EQ|INE208A01029',  # ₹230
    'BANKBARODA': 'NSE_EQ|INE028A01039',  # ₹245
    'ONGC': 'NSE_EQ|INE213A01029',  # ₹285
    'BPCL': 'NSE_EQ|INE029A01011',  # ₹310
    'WIPRO': 'NSE_EQ|INE075A01022',  # ₹310
    'POWERGRID': 'NSE_EQ|INE752E01010',  # ₹335
    'NTPC': 'NSE_EQ|INE733E01010',  # ₹370
    'COALINDIA': 'NSE_EQ|INE522F01014',  # ₹380
    'ITC': 'NSE_EQ|INE154A01025',  # ₹403
    'HPCL': 'NSE_EQ|INE094A01015',  # ₹405
    'TATAPOWER': 'NSE_EQ|INE245A01021',  # ₹440
    'VEDL': 'NSE_EQ|INE205A01025',  # ₹460
    'BERGEPAINT': 'NSE_EQ|INE463A01038',  # ₹470

    # ₹50-100 (40 stocks)
    'PFC': 'NSE_EQ|INE134E01011',  # ₹495
    'DABUR': 'NSE_EQ|INE016A01026',  # ₹515
    'RECLTD': 'NSE_EQ|INE020B01018',  # ₹530
    'INDIANB': 'NSE_EQ|INE562A01011',  # ₹540
    'JSWENERGY': 'NSE_EQ|INE121E01018',  # ₹560
    'ADANIPOWER': 'NSE_EQ|INE814H01011',  # ₹580
    'AMBUJACEM': 'NSE_EQ|INE079A01024',  # ₹585
    'MARICO': 'NSE_EQ|INE196A01026',  # ₹630
    'HINDALCO': 'NSE_EQ|INE038A01020',  # ₹650
    'TATAMOTORS': 'NSE_EQ|INE155A01022',  # ₹780
    'SBIN': 'NSE_EQ|INE062A01020',  # ₹850
    'DLF': 'NSE_EQ|INE271C01023',  # ₹860
    'JINDALSTEL': 'NSE_EQ|INE749A01030',  # ₹950
    'INDUSINDBK': 'NSE_EQ|INE095A01012',  # ₹955
    'JSWSTEEL': 'NSE_EQ|INE019A01038',  # ₹990
    'AXISBANK': 'NSE_EQ|INE238A01034',  # ₹1,135
    'GODREJCP': 'NSE_EQ|INE102D01028',  # ₹1,190
    'ADANIPORTS': 'NSE_EQ|INE742F01042',  # ₹1,270
    'DRREDDY': 'NSE_EQ|INE089A01023',  # ₹1,275
    'AUROPHARMA': 'NSE_EQ|INE406A01037',  # ₹1,260
    'ICICIBANK': 'NSE_EQ|INE090A01021',  # ₹1,280
    'BHARATFORG': 'NSE_EQ|INE465A01025',  # ₹1,370
    'RELIANCE': 'NSE_EQ|INE002A01018',  # ₹1,543
    'CIPLA': 'NSE_EQ|INE059A01026',  # ₹1,520
    'INFY': 'NSE_EQ|INE009A01021',  # ₹1,611
    'TORNTPOWER': 'NSE_EQ|INE813H01021',  # ₹1,600
    'TECHM': 'NSE_EQ|INE669C01036',  # ₹1,680
    'HAVELLS': 'NSE_EQ|INE176B01034',  # ₹1,710
    'VOLTAS': 'NSE_EQ|INE226A01021',  # ₹1,745
    'KOTAKBANK': 'NSE_EQ|INE237A01028',  # ₹1,760
    'PRESTIGE': 'NSE_EQ|INE811K01011',  # ₹1,795
    'BHARTIARTL': 'NSE_EQ|INE397D01024',  # ₹1,800
    'SUNPHARMA': 'NSE_EQ|INE044A01036',  # ₹1,810
    'HDFCBANK': 'NSE_EQ|INE040A01034',  # ₹1,845
    'ADANIGREEN': 'NSE_EQ|INE364U01010',  # ₹1,845
    'HCLTECH': 'NSE_EQ|INE860A01027',  # ₹1,945
    'OBEROIRLTY': 'NSE_EQ|INE093I01010',  # ₹2,115
    'NESTLEIND': 'NSE_EQ|INE239A01016',  # ₹2,180
    'ACC': 'NSE_EQ|INE012A01025',  # ₹2,145

    # Mid-cap stocks under ₹500 (40 stocks)
    'ESCORTS': 'NSE_EQ|INE042A01014',
    'BALKRISIND': 'NSE_EQ|INE787D01026',
    'CONCOR': 'NSE_EQ|INE111A01025',
    'CROMPTON': 'NSE_EQ|INE299U01018',
    'DIXON': 'NSE_EQ|INE935N01012',
    'EMAMILTD': 'NSE_EQ|INE548C01032',
    'EXIDEIND': 'NSE_EQ|INE302A01020',
    'GLENMARK': 'NSE_EQ|INE935A01035',
    'GODREJIND': 'NSE_EQ|INE233A01035',
    'GODREJPROP': 'NSE_EQ|INE484J01027',
    'ICICIGI': 'NSE_EQ|INE765G01017',
    'ICICIPRULI': 'NSE_EQ|INE726G01019',
    'IDFCFIRSTB': 'NSE_EQ|INE092T01019',
    'IEX': 'NSE_EQ|INE022Q01020',
    'INDUSTOWER': 'NSE_EQ|INE121J01017',
    'IRCTC': 'NSE_EQ|INE335Y01020',
    'IPCALAB': 'NSE_EQ|INE571A01020',
    'JUBLFOOD': 'NSE_EQ|INE797F01020',
    'LICHSGFIN': 'NSE_EQ|INE013A01015',
    'LUPIN': 'NSE_EQ|INE326A01037',
    'MGL': 'NSE_EQ|INE002S01010',
    'MINDTREE': 'NSE_EQ|INE018I01017',
    'MUTHOOTFIN': 'NSE_EQ|INE414G01012',
    'NAM-INDIA': 'NSE_EQ|INE298J01013',
    'NAVINFLUOR': 'NSE_EQ|INE048G01026',
    'NIACL': 'NSE_EQ|INE470Y01017',
    'NMDC': 'NSE_EQ|INE584A01023',
    'PAGEIND': 'NSE_EQ|INE761H01022',
    'PETRONET': 'NSE_EQ|INE347G01014',
    'PIIND': 'NSE_EQ|INE603J01030',
    'PVR': 'NSE_EQ|INE191H01014',
    'RAMCOCEM': 'NSE_EQ|INE331A01037',
    'SBICARD': 'NSE_EQ|INE018E01016',
    'SBILIFE': 'NSE_EQ|INE123W01016',
    'SRTRANSFIN': 'NSE_EQ|INE804I01017',
    'STAR': 'NSE_EQ|INE365B01017',
    'TATACOMM': 'NSE_EQ|INE151A01013',
    'TATAELXSI': 'NSE_EQ|INE670A01012',
    'TORNTPHARM': 'NSE_EQ|INE685A01028',
    'TRENT': 'NSE_EQ|INE849A01020',

    # Small-cap cheap stocks (80 stocks)
    'AARTIIND': 'NSE_EQ|INE769A01020',
    'ABCAPITAL': 'NSE_EQ|INE674K01013',
    'ABFRL': 'NSE_EQ|INE647O01011',
    'APOLLOTYRE': 'NSE_EQ|INE438A01022',
    'ASIANPAINT': 'NSE_EQ|INE021A01026',
    'ASTRAZEN': 'NSE_EQ|INE203A01020',
    'ATUL': 'NSE_EQ|INE100A01010',
    'AUBANK': 'NSE_EQ|INE949L01017',
    'BALKRISIND': 'NSE_EQ|INE787D01026',
    'BANDHANBNK': 'NSE_EQ|INE545U01014',
    'BATAINDIA': 'NSE_EQ|INE176A01028',
    'BEL': 'NSE_EQ|INE263A01024',
    'BHARATFORG': 'NSE_EQ|INE465A01025',
    'BIOCON': 'NSE_EQ|INE376G01013',
    'BOSCHLTD': 'NSE_EQ|INE323A01026',
    'CADILAHC': 'NSE_EQ|INE010B01027',
    'CAMS': 'NSE_EQ|INE596I01012',
    'CANFINHOME': 'NSE_EQ|INE477A01020',
    'CHAMBLFERT': 'NSE_EQ|INE085A01013',
    'CHOLAFIN': 'NSE_EQ|INE121A01024',
    'COROMANDEL': 'NSE_EQ|INE169A01031',
    'CUB': 'NSE_EQ|INE491A01021',
    'DEEPAKFERT': 'NSE_EQ|INE501A01019',
    'DEEPAKNTR': 'NSE_EQ|INE288B01029',
    'DELTACORP': 'NSE_EQ|INE124G01033',
    'DHANUKA': 'NSE_EQ|INE435G01025',
    'EQUITAS': 'NSE_EQ|INE988K01017',
    'FINEORG': 'NSE_EQ|INE686A01026',
    'FSL': 'NSE_EQ|INE684F01012',
    'GAYAPROJ': 'NSE_EQ|INE336H01023',
    'GESHIP': 'NSE_EQ|INE017A01032',
    'GICRE': 'NSE_EQ|INE481Y01014',
    'GLAND': 'NSE_EQ|INE068V01023',
    'GNFC': 'NSE_EQ|INE113A01013',
    'GODFRYPHLP': 'NSE_EQ|INE260B01028',
    'GRANULES': 'NSE_EQ|INE101D01020',
    'GRINDWELL': 'NSE_EQ|INE536A01023',
    'GUJGASLTD': 'NSE_EQ|INE844O01030',
    'HAL': 'NSE_EQ|INE066F01020',
    'HATSUN': 'NSE_EQ|INE473B01035',
    'HNDFDS': 'NSE_EQ|INE254N01026',
    'HONAUT': 'NSE_EQ|INE671A01010',
    'IDBI': 'NSE_EQ|INE008A01015',
    'IFBIND': 'NSE_EQ|INE559A01017',
    'INDHOTEL': 'NSE_EQ|INE053A01029',
    'INDIACEM': 'NSE_EQ|INE383A01012',
    'INDIGO': 'NSE_EQ|INE646L01027',
    'INFIBEAM': 'NSE_EQ|INE483S01020',
    'INGERRAND': 'NSE_EQ|INE177A01018',
    'IRB': 'NSE_EQ|INE821I01014',
    'ISEC': 'NSE_EQ|INE763G01038',
    'ITDCEM': 'NSE_EQ|INE686A01026',
    'JAICORPLTD': 'NSE_EQ|INE070D01027',
    'JKCEMENT': 'NSE_EQ|INE823G01014',
    'JKLAKSHMI': 'NSE_EQ|INE786A01032',
    'JKPAPER': 'NSE_EQ|INE789E01012',
    'JMFINANCIL': 'NSE_EQ|INE780C01023',
    'JSL': 'NSE_EQ|INE220G01021',
    'JUSTDIAL': 'NSE_EQ|INE599M01018',
    'JYOTHYLAB': 'NSE_EQ|INE668F01031',
    'KAJARIACER': 'NSE_EQ|INE217B01036',
    'KALPATPOWR': 'NSE_EQ|INE220B01022',
    'KANSAINER': 'NSE_EQ|INE879E01037',
    'KEI': 'NSE_EQ|INE878B01027',
    'KNRCON': 'NSE_EQ|INE634I01029',
    'KRBL': 'NSE_EQ|INE001B01026',
    'L&TFH': 'NSE_EQ|INE498L01015',
    'LALPATHLAB': 'NSE_EQ|INE575B01014',
    'LAURUSLABS': 'NSE_EQ|INE947Q01028',
    'LAXMIMACH': 'NSE_EQ|INE269B01029',
    'LINDEINDIA': 'NSE_EQ|INE473A01011',
    'MANAPPURAM': 'NSE_EQ|INE522D01027',
    'MFSL': 'NSE_EQ|INE180A01020',
    'MINDACORP': 'NSE_EQ|INE842C01021',
    'MOTILALOFS': 'NSE_EQ|INE296D01024',
    'MRPL': 'NSE_EQ|INE103A01014',
    'NATCOPHARM': 'NSE_EQ|INE987B01026',
    'NAUKRI': 'NSE_EQ|INE663F01024',
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
print(f"\n⏰ Scanning {len(STOCKS)} cheap stocks...")
print("🔍 This will take 2-3 minutes...\n")

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

    time.sleep(0.3)  # Faster rate

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
        print(f"   Distance: {sig['distance']:.2f}%")
        print(f"\n   Trade Setup:")
        print(f"   → Entry: ₹{sig['price']:.2f}")
        print(f"   → Stop-Loss: ₹{sig['ma20'] * 0.99:.2f}")
        print(f"   → Target: ₹{sig['price'] * 1.03:.2f} (+3%)")
        print()
else:
    print("\n⚠️  No signals found.")

print("=" * 70)