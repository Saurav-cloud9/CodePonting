"""
DAILY TRADE REPORT GENERATOR - WITH ORDER TIMELINE
============================================================
FIXED: Shows today's orders correctly + Added Order Timeline tab
"""

import requests
from datetime import datetime
import webbrowser
import os

# UPDATE THIS TOKEN DAILY!
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTUyMDdhMjZhNjY4YjU1YTdmMWQzZjQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2Njk4MzU4NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY3MDQ1NjAwfQ.RjiuurlPIdTNjuRP13brYxZwKbGUUWd-mkQbth3tJ_4"
BASE_URL = "https://api.upstox.com/v2"

def get_today_trades():
    """Fetch today's orders/trades"""
    try:
        url = f"{BASE_URL}/order/trades"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        
        print(f"⚠️  API Response: {response.status_code}")
        print(f"   {response.text[:200]}")
        return []
        
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []

def generate_html_report(trades):
    """Generate HTML report with tabs"""
    
    if not trades:
        return """
        <!DOCTYPE html>
        <html><head><title>No Trades</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>No trades found for today</h1>
            <p>No orders executed yet.</p>
        </body></html>
        """
    
    # Calculate summary
    total_trades = len(trades)
    buy_trades = [t for t in trades if t.get('transaction_type') == 'BUY']
    sell_trades = [t for t in trades if t.get('transaction_type') == 'SELL']
    
    buy_amount = sum(float(t.get('price', 0)) * int(t.get('quantity', 0)) for t in buy_trades)
    sell_amount = sum(float(t.get('price', 0)) * int(t.get('quantity', 0)) for t in sell_trades)
    net_pnl = sell_amount - buy_amount
    
    # Generate timeline HTML
    timeline_html = ""
    for trade in sorted(trades, key=lambda x: x.get('order_timestamp', '')):
        symbol = trade.get('trading_symbol', '?')
        ttype = trade.get('transaction_type', '?')
        qty = trade.get('quantity', 0)
        price = float(trade.get('price', 0))
        timestamp = trade.get('order_timestamp', '?')
        order_id = trade.get('order_id', '?')
        
        # Parse timestamp
        try:
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%I:%M:%S %p')
            else:
                time_str = timestamp
        except:
            time_str = timestamp
        
        badge_class = "buy" if ttype == "BUY" else "sell"
        amount = price * qty
        
        timeline_html += f"""
        <div class="timeline-item">
            <div class="timeline-marker {badge_class}"></div>
            <div class="timeline-content">
                <div class="timeline-time">{time_str}</div>
                <div class="timeline-details">
                    <span class="badge {badge_class}">{ttype}</span>
                    <strong>{symbol}</strong> × {qty} @ ₹{price:.2f} = <strong>₹{amount:.2f}</strong>
                    <div class="timeline-order-id">Order ID: {order_id}</div>
                </div>
            </div>
        </div>
        """
    
    # Generate trades table
    trade_rows = ""
    for trade in sorted(trades, key=lambda x: x.get('order_timestamp', '')):
        symbol = trade.get('trading_symbol', '?')
        ttype = trade.get('transaction_type', '?')
        qty = trade.get('quantity', 0)
        price = float(trade.get('price', 0))
        timestamp = trade.get('order_timestamp', '?')
        order_id = trade.get('order_id', '?')
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M:%S %p')
        except:
            time_str = timestamp
        
        badge_class = "buy" if ttype == "BUY" else "sell"
        amount = price * qty
        
        trade_rows += f"""
        <tr>
            <td>{time_str}</td>
            <td>{symbol}</td>
            <td><span class="badge {badge_class}">{ttype}</span></td>
            <td>{qty}</td>
            <td>₹{price:.2f}</td>
            <td>₹{amount:.2f}</td>
            <td style="font-size: 11px;">{order_id}</td>
        </tr>
        """
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trade Report - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
                background: #f8f9fa;
            }}
            .summary-card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}
            .summary-card h3 {{ font-size: 14px; color: #6c757d; margin-bottom: 10px; }}
            .summary-card .value {{ font-size: 24px; font-weight: 700; color: #2c3e50; }}
            .summary-card.profit .value {{ color: #27ae60; }}
            .summary-card.loss .value {{ color: #e74c3c; }}
            
            .tabs {{
                display: flex;
                background: #f8f9fa;
                padding: 0 30px;
                border-bottom: 2px solid #dee2e6;
            }}
            .tab {{
                padding: 15px 30px;
                cursor: pointer;
                font-weight: 600;
                color: #6c757d;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
            }}
            .tab:hover {{ color: #2c3e50; }}
            .tab.active {{
                color: #667eea;
                border-bottom-color: #667eea;
            }}
            
            .tab-content {{
                display: none;
                padding: 30px;
            }}
            .tab-content.active {{ display: block; }}
            
            /* Timeline styles */
            .timeline {{
                position: relative;
                padding-left: 40px;
            }}
            .timeline::before {{
                content: '';
                position: absolute;
                left: 10px;
                top: 0;
                bottom: 0;
                width: 2px;
                background: #dee2e6;
            }}
            .timeline-item {{
                position: relative;
                margin-bottom: 30px;
                display: flex;
                align-items: flex-start;
            }}
            .timeline-marker {{
                position: absolute;
                left: -33px;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }}
            .timeline-marker.buy {{ background: #27ae60; }}
            .timeline-marker.sell {{ background: #e74c3c; }}
            .timeline-content {{
                background: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                flex: 1;
            }}
            .timeline-time {{
                font-size: 12px;
                color: #6c757d;
                margin-bottom: 5px;
            }}
            .timeline-details {{ font-size: 14px; }}
            .timeline-order-id {{
                font-size: 11px;
                color: #6c757d;
                margin-top: 5px;
            }}
            
            /* Table styles */
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            thead {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            th {{
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
            tbody tr {{
                border-bottom: 1px solid #e9ecef;
            }}
            tbody tr:hover {{ background: #f8f9fa; }}
            td {{
                padding: 12px;
                color: #495057;
            }}
            
            .badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            }}
            .badge.buy {{
                background: #d4edda;
                color: #155724;
            }}
            .badge.sell {{
                background: #f8d7da;
                color: #721c24;
            }}
        </style>
        <script>
            function showTab(tabName) {{
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(tabName).classList.add('active');
                document.querySelector(`[onclick="showTab('${{tabName}}')"]`).classList.add('active');
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💎 Today's Trade Report</h1>
                <p>{datetime.now().strftime('%B %d, %Y')} | Generated: {datetime.now().strftime('%I:%M %p')}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>Total Trades</h3>
                    <div class="value">{total_trades}</div>
                </div>
                <div class="summary-card">
                    <h3>Buy Amount</h3>
                    <div class="value">₹{buy_amount:,.2f}</div>
                </div>
                <div class="summary-card">
                    <h3>Sell Amount</h3>
                    <div class="value">₹{sell_amount:,.2f}</div>
                </div>
                <div class="summary-card {'profit' if net_pnl >= 0 else 'loss'}">
                    <h3>Net P&L</h3>
                    <div class="value">₹{net_pnl:+,.2f}</div>
                </div>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('timeline')">📅 Order Timeline</div>
                <div class="tab" onclick="showTab('trades')">📋 All Trades</div>
            </div>
            
            <div id="timeline" class="tab-content active">
                <h2 style="margin-bottom: 30px; color: #2c3e50;">📅 Order Timeline</h2>
                <div class="timeline">
                    {timeline_html}
                </div>
            </div>
            
            <div id="trades" class="tab-content">
                <h2 style="margin-bottom: 20px; color: #2c3e50;">📋 All Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Qty</th>
                            <th>Price</th>
                            <th>Amount</th>
                            <th>Order ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trade_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# Main execution
print("=" * 60)
print("💎 DAILY TRADE REPORT GENERATOR")
print("=" * 60)

# Token check prompt
print("\n⚠️  IMPORTANT: Access tokens expire daily!")
print("   Current token in script expires: 3:30 PM today")
print()
token_check = input("Have you updated ACCESS_TOKEN for today? (yes/no): ").strip().lower()

if token_check not in ['yes', 'y']:
    print("\n❌ Please update ACCESS_TOKEN first!")
    print("   1. Get new token from Upstox")
    print("   2. Update ACCESS_TOKEN variable in script (line 18)")
    print("   3. Run script again")
    input("\nPress Enter to exit...")
    exit()

print("\n📅 Fetching today's trades...")
trades = get_today_trades()

if trades:
    print(f"✅ Found {len(trades)} trades!")
    
    print("📝 Generating HTML report...")
    html = generate_html_report(trades)
    
    filename = f"trade_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report saved: {filename}")
    print("🌐 Opening in browser...")
    webbrowser.open('file://' + os.path.abspath(filename))
    
    print("\n✅ DONE!")
else:
    print("⚠️  No trades found for today")
    print("   If you have trades in Upstox but none showing here:")
    print("   → Your ACCESS_TOKEN might be expired")
    print("   → Update token and run again")

print("=" * 60)
input("\nPress Enter to exit...")
