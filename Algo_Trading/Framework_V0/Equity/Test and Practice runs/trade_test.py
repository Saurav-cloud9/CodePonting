import upstox_client

# Load your saved token
with open('upstox_token.txt', 'r') as f:
    access_token = f.read().strip()

# Configure API client
configuration = upstox_client.Configuration()
configuration.access_token = access_token

api_client = upstox_client.ApiClient(configuration)

print("=" * 60)
print("UPSTOX BOT - FIRST TEST TRADE")
print("=" * 60)

try:
    # Get profile
    user_api = upstox_client.UserApi(api_client)
    profile = user_api.get_profile(api_version='2.0')
    print(f"\n👤 Trading as: {profile.data.user_name}")

    # Prepare order details
    instrument_key = "NSE_EQ|INE528G01035"  # YESBANK
    quantity = 1

    print(f"\n🎯 Test Order Details:")
    print(f"   Stock: YESBANK")
    print(f"   Quantity: {quantity}")
    print(f"   Type: MARKET order (buys at current market price)")
    print(f"   Estimated cost: ~₹23")

    # Ask for confirmation
    confirm = input("\n⚠️  Place this order? (yes/no): ").strip().lower()

    if confirm == 'yes':
        # Place the order
        order_api = upstox_client.OrderApi(api_client)

        order_request = upstox_client.PlaceOrderRequest(
            quantity=quantity,
            product="D",  # Delivery
            validity="DAY",
            price=0,  # Market order
            tag="bot_test",
            instrument_token=instrument_key,
            order_type="MARKET",
            transaction_type="BUY",
            disclosed_quantity=0,
            trigger_price=0,
            is_amo=False
        )

        order_response = order_api.place_order(
            body=order_request,
            api_version='2.0'
        )

        print(f"\n✅ ORDER PLACED!")
        print(f"Order ID: {order_response.data.order_id}")
        print("\n🎉 CONGRATULATIONS! Your bot just placed its first trade!")
        print("\n👉 Check your Upstox Orders page to see it!")

    else:
        print("\n❌ Order cancelled. No trade executed.")

    print("\n" + "=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"\nFull error details: {type(e).__name__}")