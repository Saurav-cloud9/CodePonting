import upstox_client

configuration = upstox_client.Configuration()
configuration.access_token = "YOUR_TOKEN"

# Try searching for NIFTY
api = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
# Test different keys
test_keys = [
    'NSE_INDEX|Nifty 50',
    'NSE_INDEX|NIFTY 50',
    'NSE_INDEX|Nifty50',
    'NSE_INDEX|NIFTY50'
]

for key in test_keys:
    try:
        response = api.get_full_market_quote(key, 'v2')
        print(f"✅ WORKS: {key}")
        break
    except:
        print(f"❌ FAILED: {key}")