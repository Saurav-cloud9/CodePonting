import pandas as pd

stock = 'RELIANCE'
data = pd.read_csv(f'{stock}_3months.csv', skiprows=2)

# Clean up data
data.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume', 'MA20', 'MA50']
data['Date'] = pd.to_datetime(data['Date'])
data = data.dropna()
data.set_index('Date', inplace=True)

# Convert to numeric
data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['MA20'] = pd.to_numeric(data['MA20'], errors='coerce')
data['MA50'] = pd.to_numeric(data['MA50'], errors='coerce')
data = data.dropna()

# Backtest the MA crossover strategy
position = None  # None or 'LONG'
entry_price = 0
entry_date = None
trades = []

for i in range(1, len(data)):
    # Golden Cross - BUY signal
    if data['MA20'].iloc[i] > data['MA50'].iloc[i] and data['MA20'].iloc[i - 1] <= data['MA50'].iloc[i - 1]:
        if position is None:
            position = 'LONG'
            entry_price = data['Close'].iloc[i]
            entry_date = data.index[i]
            print(f"🟢 BUY signal on {entry_date.date()} at ₹{entry_price:.2f}")

    # Death Cross - SELL signal
    elif data['MA20'].iloc[i] < data['MA50'].iloc[i] and data['MA20'].iloc[i - 1] >= data['MA50'].iloc[i - 1]:
        if position == 'LONG':
            exit_price = data['Close'].iloc[i]
            exit_date = data.index[i]
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100
            trades.append({
                'Entry Date': entry_date.date(),
                'Entry Price': entry_price,
                'Exit Date': exit_date.date(),
                'Exit Price': exit_price,
                'P&L': pnl,
                'P&L %': pnl_pct
            })
            print(f"🔴 SELL signal on {exit_date.date()} at ₹{exit_price:.2f}")
            print(f"   Trade P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)\n")
            position = None

# If still holding at end
if position == 'LONG':
    exit_price = data['Close'].iloc[-1]
    exit_date = data.index[-1]
    pnl = exit_price - entry_price
    pnl_pct = (pnl / entry_price) * 100
    trades.append({
        'Entry Date': entry_date.date(),
        'Entry Price': entry_price,
        'Exit Date': exit_date.date(),
        'Exit Price': exit_price,
        'P&L': pnl,
        'P&L %': pnl_pct
    })
    print(f"📊 Position still open at ₹{exit_price:.2f}")
    print(f"   Unrealized P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)\n")

# Summary
print(f"\n{'=' * 60}")
print(f"💰 BACKTEST RESULTS: {stock} (MA Crossover Strategy)")
print(f"{'=' * 60}")
print(f"Period: {data.index[0].date()} to {data.index[-1].date()}")
print(f"Total Trades: {len(trades)}")

if trades:
    total_pnl = sum(t['P&L'] for t in trades)
    winning_trades = [t for t in trades if t['P&L'] > 0]
    losing_trades = [t for t in trades if t['P&L'] < 0]

    print(f"\nWinning Trades: {len(winning_trades)} ({len(winning_trades) / len(trades) * 100:.1f}%)")
    print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades) / len(trades) * 100:.1f}%)")
    print(f"\nTotal P&L: ₹{total_pnl:.2f}")
    print(f"Average P&L per trade: ₹{total_pnl / len(trades):.2f}")

    if winning_trades:
        avg_win = sum(t['P&L'] for t in winning_trades) / len(winning_trades)
        print(f"Average Win: ₹{avg_win:.2f}")
    if losing_trades:
        avg_loss = sum(t['P&L'] for t in losing_trades) / len(losing_trades)
        print(f"Average Loss: ₹{avg_loss:.2f}")

    print(f"\n{'=' * 60}")
    print("Individual Trades:")
    for i, trade in enumerate(trades, 1):
        status = "✅" if trade['P&L'] > 0 else "❌"
        print(
            f"{i}. {status} {trade['Entry Date']} (₹{trade['Entry Price']:.2f}) → {trade['Exit Date']} (₹{trade['Exit Price']:.2f})")
        print(f"   P&L: ₹{trade['P&L']:.2f} ({trade['P&L %']:.2f}%)")
else:
    print("\n⚠️ No complete trades in this period (trend never reversed)")
    print(f"Current trend: {'BULLISH' if data['MA20'].iloc[-1] > data['MA50'].iloc[-1] else 'BEARISH'}")

print(f"{'=' * 60}\n")