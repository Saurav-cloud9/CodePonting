import requests

ACCESS_TOKEN = "your_token_here"  # Your current token
BASE_URL = "https://api.upstox.com/v2"

# Get positions
url = f"{BASE_URL}/portfolio/short-term-positions"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
response = requests.get(url, headers=headers)
positions = response.json()['data']

# Exit each position
for pos in positions:
    if isinstance(pos, dict) and pos.get('quantity', 0) > 0:
        symbol = pos['tradingsymbol']
        qty = pos['quantity']
        instrument = pos['instrument_token']

        # Place SELL order
        sell_url = f"{BASE_URL}/order/place"
        payload = {
            "quantity": qty,
            "product": "I",
            "validity": "DAY",
            "price": 0,
            "instrument_token": instrument,
            "order_type": "MARKET",
            "transaction_type": "SELL"
        }

        requests.post(sell_url, headers=headers, json=payload)
        print(f"✅ Exited {symbol}")