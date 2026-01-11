import upstox_client

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTYxZGQ0ZDg0NTY1ODAzNGQ1N2ZiOTYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2ODAyMTMyNSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY4MDgyNDAwfQ.76dHYGD8FxoYMsd5MmAllBSo0tmWl4jBJZV5tTz_YCI"

configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN

api = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))

print("Testing LUPIN...")
try:
    resp = api.get_historical_candle_data1('NSE_EQ|INE326A01037', 'minutes', '5', '2025-12-31', '2025-12-01')
    print(f"✅ SUCCESS: LUPIN works! {len(resp.data.candles)} candles fetched")
except Exception as e:
    print(f"❌ FAILED: {str(e)[:200]}")

