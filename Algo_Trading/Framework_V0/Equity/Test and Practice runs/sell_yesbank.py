import upstox_client

# Hardcode token (same as check_orders.py)
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

# Configure API client
configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 60)
print("SELL YESBANK - CLOSE TEST POSITION")
print("=" * 60)

try:
    user_api = upstox_client.UserApi(api_client)
    profile = user_api.get_profile(api_version='2.0')
    print(f"\n👤 Trading as: {profile.data.user_name}")

    # Order details
    instrument_key = "NSE_EQ|INE528G01035"  # YESBANK
    quantity = 1

    print(f"\n🎯 Sell Order Details:")
    print(f"   Stock: YESBANK")
    print(f"   Quantity: {quantity}")
    print(f"   Type: MARKET order (sells at current market price)")
    print(f"   Expected proceeds: ~₹22")

    # Confirm
    confirm = input("\n⚠️  Sell this share? (yes/no): ").strip().lower()

    if confirm == 'yes':
        order_api = upstox_client.OrderApi(api_client)

        order_request = upstox_client.PlaceOrderRequest(
            quantity=quantity,
            product="D",  # Delivery (selling from holdings)
            validity="DAY",
            price=0,  # Market order
            tag="bot_test_sell",
            instrument_token=instrument_key,
            order_type="MARKET",
            transaction_type="SELL",  # THIS IS THE KEY DIFFERENCE!
            disclosed_quantity=0,
            trigger_price=0,
            is_amo=False
        )

        order_response = order_api.place_order(
            body=order_request,
            api_version='2.0'
        )

        print(f"\n✅ SELL ORDER PLACED!")
        print(f"Order ID: {order_response.data.order_id}")
        print("\n🎉 Test cycle complete!")
        print("   BUY → HOLD → SELL ✅")
        print("\n👉 Check Upstox to see the executed sell order!")

    else:
        print("\n❌ Sell order cancelled.")

    print("\n" + "=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")