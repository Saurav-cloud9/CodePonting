import pandas as pd
import matplotlib.pyplot as plt

stock = 'RELIANCE'
data = pd.read_csv(f'{stock}_3months.csv', skiprows=2)

# Clean data
data.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume', 'MA20', 'MA50']
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Convert to numeric
data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['MA20'] = pd.to_numeric(data['MA20'], errors='coerce')
data['MA50'] = pd.to_numeric(data['MA50'], errors='coerce')
data = data.dropna()

print(f"Analyzing {stock} - MA Bounce Strategy")
print(f"Period: {data.index[0].date()} to {data.index[-1].date()}\n")

# Calculate additional needed data
data['Prev_Close'] = data['Close'].shift(1)
data['Distance_to_MA20'] = ((data['Close'] - data['MA20']) / data['MA20']) * 100  # % distance

# Backtest the MA Bounce strategy
position = None
entry_price = 0
entry_date = None
trades = []

for i in range(1, len(data)):
    current_date = data.index[i]
    current_price = data['Close'].iloc[i]
    prev_close = data['Prev_Close'].iloc[i]
    ma20 = data['MA20'].iloc[i]
    ma50 = data['MA50'].iloc[i]
    distance = data['Distance_to_MA20'].iloc[i]

    # Skip if not enough data
    if pd.isna(prev_close):
        continue

    # ENTRY LOGIC
    if position is None:
        # Check all 3 conditions:
        # 1. Uptrend (MA20 > MA50)
        # 2. Price within 2% of MA20
        # 3. Price rising (bounce confirmation)

        if ma20 > ma50 and abs(distance) <= 2 and current_price > prev_close:
            position = 'LONG'
            entry_price = current_price
            entry_date = current_date
            print(f"🟢 BUY Signal: {current_date.date()}")
            print(f"   Entry Price: ₹{entry_price:.2f}")
            print(f"   Distance to MA20: {distance:.2f}%")
            print(f"   MA20: ₹{ma20:.2f}, MA50: ₹{ma50:.2f}\n")

    # EXIT LOGIC
    elif position == 'LONG':
        # Exit if price closes below MA20 (support broken)
        if current_price < ma20:
            exit_price = current_price
            exit_date = current_date
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100

            trades.append({
                'Entry Date': entry_date.date(),
                'Entry Price': entry_price,
                'Exit Date': exit_date.date(),
                'Exit Price': exit_price,
                'Exit Reason': 'Stop-Loss (Below MA20)',
                'P&L': pnl,
                'P&L %': pnl_pct
            })

            print(f"🔴 SELL Signal (Stop-Loss): {exit_date.date()}")
            print(f"   Exit Price: ₹{exit_price:.2f}")
            print(f"   P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)\n")

            position = None

        # Exit if +3% profit target hit
        elif current_price >= entry_price * 1.03:
            exit_price = current_price
            exit_date = current_date
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100

            trades.append({
                'Entry Date': entry_date.date(),
                'Entry Price': entry_price,
                'Exit Date': exit_date.date(),
                'Exit Price': exit_price,
                'Exit Reason': 'Target Hit (+3%)',
                'P&L': pnl,
                'P&L %': pnl_pct
            })

            print(f"🎯 SELL Signal (Target): {exit_date.date()}")
            print(f"   Exit Price: ₹{exit_price:.2f}")
            print(f"   P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)\n")

            position = None

# If still holding at end
if position == 'LONG':
    exit_price = data['Close'].iloc[-1]
    exit_date = data.index[-1]
    pnl = exit_price - entry_price
    pnl_pct = (pnl / entry_price) * 100

    print(f"📊 Position Still Open: {exit_date.date()}")
    print(f"   Current Price: ₹{exit_price:.2f}")
    print(f"   Unrealized P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)\n")

    trades.append({
        'Entry Date': entry_date.date(),
        'Entry Price': entry_price,
        'Exit Date': exit_date.date(),
        'Exit Price': exit_price,
        'Exit Reason': 'Still Holding',
        'P&L': pnl,
        'P&L %': pnl_pct
    })

# Results Summary
print(f"\n{'=' * 70}")
print(f"💰 BACKTEST RESULTS: {stock} (MA Bounce Strategy)")
print(f"{'=' * 70}")

if trades:
    total_pnl = sum(t['P&L'] for t in trades)
    winning_trades = [t for t in trades if t['P&L'] > 0]
    losing_trades = [t for t in trades if t['P&L'] < 0]

    print(f"Total Trades: {len(trades)}")
    print(f"Winning Trades: {len(winning_trades)} ({len(winning_trades) / len(trades) * 100:.1f}%)")
    print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades) / len(trades) * 100:.1f}%)")
    print(f"\nTotal P&L: ₹{total_pnl:.2f}")
    print(f"Average P&L per trade: ₹{total_pnl / len(trades):.2f}")

    if winning_trades:
        avg_win = sum(t['P&L'] for t in winning_trades) / len(winning_trades)
        print(f"Average Win: ₹{avg_win:.2f}")
    if losing_trades:
        avg_loss = sum(t['P&L'] for t in losing_trades) / len(losing_trades)
        print(f"Average Loss: ₹{avg_loss:.2f}")

    print(f"\n{'=' * 70}")
else:
    print("No trades triggered in this period")

print(f"{'=' * 70}\n")

# Visualization of Entry/Exit Points
plt.figure(figsize=(16, 8))
plt.plot(data.index, data['Close'], label='Price', linewidth=2, color='blue')
plt.plot(data.index, data['MA20'], label='MA20', linestyle='--', alpha=0.7, color='orange')
plt.plot(data.index, data['MA50'], label='MA50', linestyle='--', alpha=0.7, color='red')

# Mark all trades
for trade in trades:
    entry_date = pd.to_datetime(trade['Entry Date'])
    exit_date = pd.to_datetime(trade['Exit Date'])

    # Entry marker (green triangle pointing UP)
    plt.scatter(entry_date, trade['Entry Price'], color='green', s=200, marker='^',
                label='BUY Signal' if trade == trades[0] else '', zorder=5)

    # Exit marker (if not still holding)
    if trade['Exit Reason'] != 'Still Holding':
        exit_color = 'red' if trade['P&L'] < 0 else 'blue'
        plt.scatter(exit_date, trade['Exit Price'], color=exit_color, s=200, marker='v',
                    label='SELL Signal' if trade == trades[0] else '', zorder=5)
    else:
        # Draw a small circle for current position
        plt.scatter(exit_date, trade['Exit Price'], color='gold', s=150, marker='o',
                    label='Still Holding', zorder=5)

plt.title(f'{stock} - MA Bounce Strategy (Entry/Exit Points)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Price (₹)', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()