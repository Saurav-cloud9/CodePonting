import upstox_client
from datetime import datetime, timedelta



# Hardcode token temporarily
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTM3YzBmOTQ1MjY4MzczOTgyZWRiZGYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NTI2MTU2MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY1MzE3NjAwfQ.2pt8ubJgMwpekm2VdkACbGw6IK9NCfjKUPF7G2Bgr6A"

# Configure
configuration = upstox_client.Configuration()
configuration.access_token = access_token
api_client = upstox_client.ApiClient(configuration)

print("=" * 60)
print("CHECKING YOUR RECENT ORDERS")
print("=" * 60)

try:
    order_api = upstox_client.OrderApi(api_client)

    # Get order history (not just today)
    order_history = order_api.get_order_book(api_version='2.0')

    if len(order_history.data) == 0:
        print("\n📋 No orders found today")
        print("\n💡 Checking holdings instead (stocks you own)...\n")

        # Check holdings (positions you own)
        portfolio_api = upstox_client.PortfolioApi(api_client)
        holdings = portfolio_api.get_holdings(api_version='2.0')

        if len(holdings.data) > 0:
            print(f"📊 You currently hold {len(holdings.data)} positions:\n")
            for holding in holdings.data:
                print(f"Stock: {holding.trading_symbol}")
                print(f"  Quantity: {holding.quantity}")
                print(f"  Avg Price: ₹{holding.average_price}")
                print(f"  Current Price: ₹{holding.last_price}")
                print(f"  P&L: ₹{holding.pnl} ({holding.day_change_percentage:.2f}%)")
                print("-" * 60)
        else:
            print("No holdings found either.")
    else:
        print(f"\n📋 Total Orders: {len(order_history.data)}\n")

        for order in order_history.data:
            print(f"Order ID: {order.order_id}")
            print(f"  Stock: {order.trading_symbol}")
            print(f"  Type: {order.transaction_type}")
            print(f"  Quantity: {order.quantity}")
            print(f"  Status: {order.status}")
            print(f"  Price: ₹{order.average_price if order.average_price else 'Pending'}")
            print(f"  Tag: {order.tag if order.tag else 'N/A'}")
            print("-" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")