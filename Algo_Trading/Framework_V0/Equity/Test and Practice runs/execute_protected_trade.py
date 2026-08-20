import requests
import time

# Your access token
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTMyODA4OTUwZjM4NzRkYmExNzExZTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NDkxNzM4NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY0OTcyMDAwfQ.bs9bB791bbO5q94pz_dDoGzhJhWPDOxqhlE-yCrOIc4"

# Stock details
SYMBOL_NAME = "YESBANK"
ISIN = "INE528G01035"
INSTRUMENT_KEY = f"NSE_EQ|{ISIN}"


# Get current price
def get_ltp(isin):
    url = f"https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_EQ%7C{isin}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for key in data.get('data', {}).keys():
            return data['data'][key]['last_price']
    return None


# Place order
def place_order(instrument_key, transaction_type, quantity, order_type, price, trigger_price=0):
    url = "https://api.upstox.com/v2/order/place"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        "quantity": quantity,
        "product": "D",  # D = Delivery
        "validity": "DAY",
        "price": price,
        "tag": "algo_learning",
        "instrument_token": instrument_key,
        "order_type": order_type,
        "transaction_type": transaction_type,
        "disclosed_quantity": 0,
        "trigger_price": trigger_price,
        "is_amo": False
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 LIVE TRADING - STEP 1: STOP-LOSS PROTECTED TRADE")
    print("=" * 60)

    quantity = 1

    # Step 1: Get current price
    print(f"\n📡 Fetching live price of {SYMBOL_NAME}...")
    ltp = get_ltp(ISIN)

    if not ltp:
        print("❌ Could not fetch price. Aborting.")
        exit()

    print(f"✅ Current Price: ₹{ltp}")

    # Step 2: Calculate prices
    buy_price = ltp
    stoploss_trigger = round(buy_price * 0.98, 2)  # 2% below
    stoploss_limit = round(stoploss_trigger * 0.995, 2)  # 0.5% below trigger
    max_loss = round((buy_price - stoploss_limit) * quantity, 2)

    # Step 3: Show trade plan
    print("\n" + "=" * 60)
    print("📊 TRADE PLAN:")
    print("=" * 60)
    print(f"Stock: {SYMBOL_NAME}")
    print(f"Quantity: {quantity} share(s)")
    print(f"\n🔵 BUY ORDER:")
    print(f"   Price: ₹{buy_price}")
    print(f"   Cost: ₹{round(buy_price * quantity, 2)}")
    print(f"   Brokerage: ₹20")
    print(f"   Total: ₹{round(buy_price * quantity + 20, 2)}")

    print(f"\n🛡️ STOP-LOSS ORDER:")
    print(f"   Trigger: ₹{stoploss_trigger}")
    print(f"   Limit: ₹{stoploss_limit}")
    print(f"   Max Loss: ₹{max_loss}")

    print("\n" + "=" * 60)

    # Step 4: Confirm
    confirm = input("\n⚠️  REAL MONEY! Proceed with LIVE trade? (YES/no): ")

    if confirm.upper() != "YES":
        print("❌ Trade cancelled.")
        exit()

    # Step 5: Place BUY order
    print("\n🔵 Placing BUY order...")
    buy_response = place_order(
        instrument_key=INSTRUMENT_KEY,
        transaction_type="BUY",
        quantity=quantity,
        order_type="LIMIT",
        price=buy_price
    )

    print(f"Response: {buy_response}")

    if buy_response.get('status') != 'success':
        print("❌ BUY order failed!")
        print(f"Error: {buy_response}")
        exit()

    buy_order_id = buy_response['data']['order_id']
    print(f"✅ BUY order placed! Order ID: {buy_order_id}")

    # Step 6: Wait a moment for order to process
    print("\n⏳ Waiting 2 seconds for order to process...")
    time.sleep(2)

    # Step 7: Pl