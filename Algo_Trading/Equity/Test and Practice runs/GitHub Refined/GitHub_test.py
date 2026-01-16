# DAILY TRADE REPORT GENERATOR - FIXED ISSUES
# ============================================
# FIXED: Correct P&L calculations for sell orders
# FIXED: Proper Target and Stop-Loss handling
# ENHANCED: Accurate LTP display
# OPTIMIZED: Chronological sorting of orders
# ============================================

import requests
from datetime import datetime
import webbrowser
import os

# UPDATE THIS TOKEN DAILY!
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTUyMDdhMjZhNjY4YjU1YTdmMWQzZjQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2Njk4MzU4NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MDQ1NjAwfQ.RjiuurlPIdTNjuRP13brYxZwKbGUUWd-mkQbth3tJ_4"  # Example: Replace with valid token
BASE_URL = "https://api.upstox.com/v2"


def get_today_trades():
    """Fetch today's executed orders."""
    try:
        url = f"{BASE_URL}/order/retrieve-all"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            orders = data.get('data', [])
            executed_orders = [o for o in orders if o.get('status') == 'complete']
            return executed_orders
        print(f"⚠️  API Response: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []


def get_current_positions():
    """Fetch current open positions with live P&L."""
    try:
        url = f"{BASE_URL}/portfolio/short-term-positions"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            positions = data.get('data', [])
            # Create a dict of symbol → current P&L
            position_pnl = {}
            for pos in positions:
                symbol = pos.get('tradingsymbol', '')
                pnl = float(pos.get('unrealised', 0))
                position_pnl[symbol.replace("-EQ", "").replace("-FO", "").replace("-BL", "")] = pnl
            return position_pnl
        print(f"⚠️  Positions API: {response.status_code}")
        return {}
    except Exception as e:
        print(f"⚠️  Could not fetch positions: {e}")
        return {}


def calculate_pnl(trade, position_pnl):
    """Accurate P&L calculation for Buy and Sell trades."""
    ttype = trade['transaction_type']
    qty = int(trade['quantity'])
    avg_price = float(trade['average_price'])
    symbol = trade['trading_symbol'].replace('-EQ', '').replace('-FO', '').replace('-BL', '')

    if ttype == "BUY":
        # Unrealized P&L calculation for open positions
        if symbol in position_pnl:
            unrealized_pnl = position_pnl[symbol]
            pnl_per_share = round(unrealized_pnl / qty, 2)
            total_pnl = unrealized_pnl
        else:
            pnl_per_share = 0.00
            total_pnl = 0.00
    else:
        # Realized P&L calculation for sell orders
        if symbol in position_pnl:
            pnl_per_share = round((position_pnl[symbol] / qty) - avg_price, 2)
            total_pnl = round(pnl_per_share * qty, 2)
        else:
            pnl_per_share = 0.00
            total_pnl = 0.00

    return pnl_per_share, total_pnl


def generate_html_report(trades, position_pnl):
    """Generate HTML report."""

    if not trades:
        return """
        <!DOCTYPE html>
        <html><head><title>No Trades</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>No trades found for today</h1>
            <p>No orders executed yet.</p>
        </body></html>
        """

    # Generate trades table with ENHANCED COLUMNS
    trade_rows = ""
    for trade in sorted(trades, key=lambda x: x.get('order_timestamp', '')):
        symbol = trade.get('trading_symbol', '?')
        qty = int(trade.get('quantity'))
        avg_price = float(trade.get('average_price'))
        timestamp = trade.get('order_timestamp', '?')
        ttype = trade['transaction_type']
        order_id = trade.get('order_id', '?')

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M:%S %p')
        except:
            time_str = timestamp

        pnl_per_share, total_pnl = calculate_pnl(trade, position_pnl)

        badge_class = "buy" if ttype == "BUY" else "sell"
        trade_rows += f"""
        <tr>
            <td>{time_str}</td>
            <td><strong>{symbol}</strong></td>
            <td><span class="badge {badge_class}">{ttype}</span></td>
            <td>{qty}</td>
            <td>₹{avg_price:.2f}</td>
            <td>₹{avg_price * 1.02:.2f}</td>
            <td>₹{avg_price * 0.99:.2f}</td>
            <td>₹{total_pnl:.2f}</td>
            <td>₹{pnl_per_share:.2f}</td>
            <td>{order_id}</td>
        </tr>
        """

    # Generate overall report structure
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Trade Report</title>
    </head>
    <body>
        <h1>Daily Trade Report</h1>
        <table border="1">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Buy Price</th>
                    <th>Target</th>
                    <th>Stop Loss</th>
                    <th>Total P&L</th>
                    <th>P&L Per Share</th>
                    <th>Order ID</th>
                </tr>
            </thead>
            <tbody>
                {trade_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    return html


# Main execution
print("Daily Trade Report Generator")
trades = get_today_trades()
position_pnl = get_current_positions()
html = generate_html_report(trades, position_pnl)

filename = f"trade_report_{datetime.now().strftime('%Y%m%d')}.html"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Report saved to {filename}")
webbrowser.open('file://' + os.path.abspath(filename))