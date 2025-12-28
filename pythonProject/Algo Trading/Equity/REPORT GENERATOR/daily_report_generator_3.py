"""
DAILY TRADE REPORT GENERATOR
============================================================
Fetches today's trades from Upstox and generates a beautiful HTML report.

SETUP:
1. Update ACCESS_TOKEN daily (expires at midnight)
2. Run anytime after 3:30 PM to get full day's trades
3. HTML report opens automatically in browser

NO COMPLEX FEATURES = NO DEBUGGING NEEDED!
"""

import requests
from datetime import datetime, date, timedelta
import webbrowser
import os

# ============================================
# CONFIGURATION - UPDATE DAILY!
# ============================================
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTRkY2ZmYzNlZDdhNDU2NmM3NGE0ODIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NjcwNzE5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY2Nzg2NDAwfQ.gvlbJFWY94keKrs6AABK4EITgTQ7sFXx-PPiDnoBCio"  # Update this daily!

BASE_URL = "https://api.upstox.com/v2"

# ============================================
# FETCH TRADES FROM UPSTOX
# ============================================

def get_trades_for_date(target_date):
    """Fetch all trades for a specific date"""
    try:
        url = f"{BASE_URL}/charges/historical-trades"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        params = {
            "start_date": target_date,
            "end_date": target_date,
            "page_number": 1,
            "page_size": 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                return data['data']  # trades are directly in the data array
        
        print(f"⚠️  API Response: {response.status_code}")
        print(f"   {response.text[:200]}")
        return []
        
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []

def calculate_pnl_by_stock(trades):
    """Calculate P&L for each stock"""
    stock_data = {}
    
    for trade in trades:
        symbol = trade.get('scrip_name', 'UNKNOWN')  # Changed from trading_symbol
        trade_type = trade.get('transaction_type', '')  # Changed from trade_type
        quantity = int(trade.get('quantity', 0))
        amount = float(trade.get('amount', 0))  # This is already total amount
        
        if symbol not in stock_data:
            stock_data[symbol] = {
                'buys': 0,
                'sells': 0,
                'buy_amount': 0,
                'sell_amount': 0,
                'trades': []
            }
        
        if trade_type == 'BUY':
            stock_data[symbol]['buys'] += 1
            stock_data[symbol]['buy_amount'] += amount
        else:
            stock_data[symbol]['sells'] += 1
            stock_data[symbol]['sell_amount'] += amount
        
        stock_data[symbol]['trades'].append(trade)
    
    # Calculate P&L for each stock
    for symbol in stock_data:
        pnl = stock_data[symbol]['sell_amount'] - stock_data[symbol]['buy_amount']
        stock_data[symbol]['pnl'] = pnl
    
    return stock_data

# ============================================
# GENERATE HTML REPORT
# ============================================

def generate_html_report(trades, report_date):
    """Generate beautiful HTML report"""
    
    if not trades:
        return f"""
        <!DOCTYPE html>
        <html><head><title>No Trades</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>No trades found for {report_date}</h1>
            <p>Either market was closed or no trades were executed.</p>
        </body></html>
        """
    
    stock_data = calculate_pnl_by_stock(trades)
    
    # Calculate totals
    total_buy = sum(s['buy_amount'] for s in stock_data.values())
    total_sell = sum(s['sell_amount'] for s in stock_data.values())
    net_pnl = total_sell - total_buy
    
    # Generate stock cards HTML
    stock_cards_html = ""
    for symbol, data in sorted(stock_data.items(), key=lambda x: x[1]['pnl'], reverse=True):
        pnl = data['pnl']
        card_class = "profit" if pnl >= 0 else "loss"
        pnl_class = "amount-positive" if pnl >= 0 else "amount-negative"
        
        stock_cards_html += f"""
        <div class="stock-card {card_class}">
            <h4>{symbol}</h4>
            <div class="stats">
                <span>Buys: {data['buys']}</span>
                <span>Sells: {data['sells']}</span>
            </div>
            <div class="pnl {pnl_class}">₹{pnl:+.2f}</div>
        </div>
        """
    
    # Generate trade rows HTML
    trade_rows_html = ""
    for trade in sorted(trades, key=lambda x: x.get('trade_date', '') + x.get('trade_time', ''), reverse=True):
        symbol = trade.get('scrip_name', 'UNKNOWN')
        trade_type = trade.get('transaction_type', '')
        quantity = trade.get('quantity', 0)
        amount = float(trade.get('amount', 0))
        price = amount / quantity if quantity > 0 else 0
        trade_date = trade.get('trade_date', 'N/A')
        trade_time = trade.get('trade_time', 'N/A')
        trade_id = trade.get('trade_id', 'N/A')
        
        badge_class = "buy" if trade_type == "BUY" else "sell"
        amount_class = "amount-positive" if trade_type == "BUY" else "amount-negative"
        
        trade_rows_html += f"""
        <tr>
            <td>{trade_date}</td>
            <td>{trade_time}</td>
            <td>{symbol}</td>
            <td><span class="badge {badge_class}">{trade_type}</span></td>
            <td>{quantity}</td>
            <td>₹{price:.2f}</td>
            <td class="{amount_class}">₹{amount:.2f}</td>
            <td>{trade_id}</td>
        </tr>
        """
    
    # Build complete HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Trade Report - {report_date}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px 40px;
                text-align: center;
            }}
            .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
            .header p {{ font-size: 16px; opacity: 0.9; }}
            .summary-cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                padding: 30px 40px;
                background: #f8f9fa;
            }}
            .card {{
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                border-left: 4px solid #667eea;
            }}
            .card h3 {{
                font-size: 14px;
                color: #6c757d;
                margin-bottom: 10px;
                text-transform: uppercase;
            }}
            .card .value {{
                font-size: 28px;
                font-weight: 700;
                color: #2c3e50;
            }}
            .card.profit .value {{ color: #27ae60; }}
            .card.loss .value {{ color: #e74c3c; }}
            .stock-summary {{
                padding: 40px;
                background: #f8f9fa;
            }}
            .stock-summary h2 {{
                margin-bottom: 20px;
                color: #2c3e50;
                font-size: 24px;
            }}
            .stock-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
            }}
            .stock-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                border-left: 4px solid #667eea;
            }}
            .stock-card.profit {{ border-left-color: #27ae60; }}
            .stock-card.loss {{ border-left-color: #e74c3c; }}
            .stock-card h4 {{
                font-size: 16px;
                margin-bottom: 12px;
                color: #2c3e50;
            }}
            .stock-card .stats {{
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                color: #6c757d;
                margin-bottom: 8px;
            }}
            .stock-card .pnl {{
                font-size: 20px;
                font-weight: 700;
                margin-top: 10px;
            }}
            .table-container {{
                padding: 40px;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }}
            thead {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            th {{
                padding: 15px 12px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 12px;
            }}
            tbody tr {{
                border-bottom: 1px solid #e9ecef;
                transition: all 0.3s;
            }}
            tbody tr:hover {{
                background: #f8f9fa;
            }}
            td {{
                padding: 15px 12px;
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
            .amount-positive {{ color: #27ae60; font-weight: 600; }}
            .amount-negative {{ color: #e74c3c; font-weight: 600; }}
            .footer {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💎 Daily Trade Report</h1>
                <p>Date: {report_date} | Generated: {datetime.now().strftime('%I:%M %p')}</p>
            </div>
            
            <div class="summary-cards">
                <div class="card">
                    <h3>Total Trades</h3>
                    <div class="value">{len(trades)}</div>
                </div>
                <div class="card">
                    <h3>Total Buy Amount</h3>
                    <div class="value">₹{total_buy:,.2f}</div>
                </div>
                <div class="card">
                    <h3>Total Sell Amount</h3>
                    <div class="value">₹{total_sell:,.2f}</div>
                </div>
                <div class="card {'profit' if net_pnl >= 0 else 'loss'}">
                    <h3>Net P&L</h3>
                    <div class="value">₹{net_pnl:+,.2f}</div>
                </div>
            </div>
            
            <div class="stock-summary">
                <h2>📊 Stock-wise Performance</h2>
                <div class="stock-grid">
                    {stock_cards_html}
                </div>
            </div>
            
            <div class="table-container">
                <h2 style="margin-bottom: 20px; color: #2c3e50;">📋 All Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Qty</th>
                            <th>Price</th>
                            <th>Amount</th>
                            <th>Trade ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trade_rows_html}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>💎 Generated by Daily Report Script | Automated Trading Reports</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Generate trade report with date selection"""
    
    print("=" * 60)
    print("💎 DAILY TRADE REPORT GENERATOR")
    print("=" * 60)
    
    # Check token
    if ACCESS_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("❌ ERROR: Please update ACCESS_TOKEN in the script!")
        print("   Get token from Upstox and paste it at line 18")
        input("\nPress Enter to exit...")
        return
    
    # Date selection menu
    print("\n📅 SELECT DATE RANGE:")
    print("  1. Today only")
    print("  2. Yesterday")
    print("  3. Last 7 days")
    print("  4. Last 30 days")
    print("  5. Custom date (single day)")
    print("  6. Custom date range")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    today = date.today()
    
    if choice == "1":
        start_date = today
        end_date = today
        report_title = f"Today ({today.strftime('%Y-%m-%d')})"
    elif choice == "2":
        start_date = today - timedelta(days=1)
        end_date = start_date
        report_title = f"Yesterday ({start_date.strftime('%Y-%m-%d')})"
    elif choice == "3":
        start_date = today - timedelta(days=7)
        end_date = today
        report_title = f"Last 7 Days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    elif choice == "4":
        start_date = today - timedelta(days=30)
        end_date = today
        report_title = f"Last 30 Days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    elif choice == "5":
        date_input = input("Enter date (YYYY-MM-DD): ").strip()
        try:
            start_date = datetime.strptime(date_input, '%Y-%m-%d').date()
            end_date = start_date
            report_title = f"{start_date.strftime('%Y-%m-%d')}"
        except:
            print("❌ Invalid date format!")
            input("\nPress Enter to exit...")
            return
    elif choice == "6":
        start_input = input("Enter start date (YYYY-MM-DD): ").strip()
        end_input = input("Enter end date (YYYY-MM-DD): ").strip()
        try:
            start_date = datetime.strptime(start_input, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_input, '%Y-%m-%d').date()
            report_title = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        except:
            print("❌ Invalid date format!")
            input("\nPress Enter to exit...")
            return
    else:
        print("❌ Invalid choice!")
        input("\nPress Enter to exit...")
        return
    
    print(f"\n📅 Fetching trades for: {report_title}")
    print("⏳ Please wait...")
    
    # Fetch trades for date range
    all_trades = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        trades = get_trades_for_date(date_str)
        if trades:
            all_trades.extend(trades)
            print(f"   ✅ {date_str}: {len(trades)} trades")
        else:
            print(f"   ⚠️  {date_str}: No trades")
        current_date += timedelta(days=1)
    
    if all_trades:
        print(f"\n✅ Total: {len(all_trades)} trades across all dates!")
    else:
        print("\n⚠️  No trades found in selected date range")
    
    # Generate report
    print("📝 Generating HTML report...")
    html_content = generate_html_report(all_trades, report_title)
    
    # Save report
    filename = f"trade_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report saved: {filename}")
    
    # Open in browser
    print("🌐 Opening report in browser...")
    webbrowser.open('file://' + os.path.abspath(filename))
    
    print("\n" + "=" * 60)
    print("✅ DONE! Report opened in your browser.")
    print("=" * 60)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
