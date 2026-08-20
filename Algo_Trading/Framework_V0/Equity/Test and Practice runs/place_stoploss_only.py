import requests

access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTMyODA4OTUwZjM4NzRkYmExNzExZTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NDkxNzM4NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY0OTcyMDAwfQ.bs9bB791bbO5q94pz_dDoGzhJhWPDOxqhlE-yCrOIc4"

ISIN = "INE528G01035"
INSTRUMENT_KEY = f"NSE_EQ|{ISIN}"

# Place stop-loss order
url = "https://api.upstox.com/v2/order/place"
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

data = {
    "quantity": 1,
    "product": "D",
    "validity": "DAY",
    "price": 22.02,  # Limit price
    "tag": "emergency_stoploss",
    "instrument_token": INSTRUMENT_KEY,
    "order_type": "SL",
    "transaction_type": "SELL",
    "disclosed_quantity": 0,
    "trigger_price": 22.13,  # Trigger price
    "is_amo": False
}

print("🛡️ Placing STOP-LOSS order...")
response = requests.post(url, headers=headers, json=data)
print(response.json())