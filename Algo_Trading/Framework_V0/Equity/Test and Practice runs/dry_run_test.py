import requests

# Your Upstox credentials
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTMyODA4OTUwZjM4NzRkYmExNzExZTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NDkxNzM4NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY0OTcyMDAwfQ.bs9bB791bbO5q94pz_dDoGzhJhWPDOxqhlE-yCrOIc4"


# Get current price using ISIN
def get_ltp(isin):
    """Get Last Traded Price using ISIN"""
    # Use the instrument_key format with ISIN
    url = f"https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_EQ%7C{isin}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)

    print(f"Response Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Data: {data}")

        # Extract price - find the key dynamically
        for key in data.get('data', {}).keys():
            return data['data'][key]['last_price']

    return None


# DRY RUN
if __name__ == "__main__":
    symbol_name = "YESBANK"
    isin = "INE528G01035"  # YES BANK ISIN
    quantity = 1

    print("=" * 50)
    print("🧪 DRY RUN - NO ACTUAL ORDERS WILL BE PLACED")
    print("=" * 50)

    print(f"\n📡 Fetching current price of {symbol_name} (ISIN: {isin})...")
    ltp = get_ltp(isin)

    if ltp:
        print(f"✅ Current Market Price: ₹{ltp}")

        # Calculate trade plan
        buy_price = ltp
        stoploss_trigger = round(buy_price * 0.98, 2)
        stoploss_limit = round(stoploss_trigger * 0.995, 2)
        max_loss = round((buy_price - stoploss_limit) * quantity, 2)

        print("\n" + "=" * 50)
        print("📊 SIMULATED TRADE PLAN:")
        print("=" * 50)
        print(f"Stock: {symbol_name}")
        print(f"ISIN: {isin}")
        print(f"Quantity: {quantity} share(s)")
        print(f"\n🔵 BUY ORDER:")
        print(f"   Type: LIMIT")
        print(f"   Price: ₹{buy_price}")
        print(f"   Total Cost: ₹{round(buy_price * quantity, 2)}")

        print(f"\n🛡️ STOP-LOSS ORDER:")
        print(f"   Type: SL (Stop-Loss)")
        print(f"   Trigger Price: ₹{stoploss_trigger}")
        print(f"   Limit Price: ₹{stoploss_limit}")
        print(f"   Protection: 2% below buy price")

        print(f"\n💰 RISK CALCULATION:")
        print(f"   Maximum Loss: ₹{max_loss}")
        print(f"   Loss Percentage: ~2%")

        print("\n" + "=" * 50)
        print("✅ DRY RUN COMPLETE!")
        print("=" * 50)

    else:
        print("❌ Markets might be closed or token expired")
        print("Markets are open: Mon-Fri 9:15 AM - 3:30 PM IST")