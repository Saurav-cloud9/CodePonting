def draw_dashboard_header():
    """Draw live dashboard header"""
    now = datetime.now()
    time_str = now.strftime("%I:%M:%S %p")

    # Next scan countdown
    next_scan = "..."
    if dashboard_metrics["last_scan"]:
        elapsed = (now - dashboard_metrics["last_scan"]).total_seconds()
        remaining = max(0, 60 - int(elapsed))
        next_scan = f"{remaining}s"

    strategy = dashboard_metrics["current_strategy"]
    num_positions = len(dashboard_metrics["positions"])
    total_pnl = dashboard_metrics["pnl"]
    pnl_color = "\033[92m" if total_pnl >= 0 else "\033[91m"  # Green/red for P&L

    RED = '\033[91m'              # Bright red for borders
    BLUE = '\033[38;5;33m'        # Your sweet-spot brighter blue
    WHITE = '\033[97m'            # Bright white for data rows
    RESET = '\033[0m'             # Reset colors

    # LIVE values (no more dummies!)
    line1 = "MA Bounce Bot v0.5 - LIVE TRADING"
    line2 = f"{time_str} | {strategy:<20} | Next scan: {next_scan}"
    line3 = f"TODAY: Signals: {dashboard_metrics['signals_today']:2d} | Trades: {dashboard_metrics['trades_today']:2d} | Win: {dashboard_metrics['wins']:2d} | Loss: {dashboard_metrics['losses']:2d} | P&L: {pnl_color}₹{total_pnl:+.2f}{RESET}"
    line4 = f"POSITIONS: {num_positions} active"

    inner_width = 74

    header = f"""{RED}╔══════════════════════════════════════════════════════════════════════════╗{RESET}
{RED}║{RESET}{BLUE}{line1:<{inner_width}}{RESET}{RED}║{RESET}
{RED}║{RESET}{BLUE}{line2:<{inner_width}}{RESET}{RED}║{RESET}
{RED}╠══════════════════════════════════════════════════════════════════════════╣{RESET}
{RED}║{RESET}{WHITE}{line3:<{inner_width}}{RESET}{RED}║{RESET}
{RED}║{RESET}{WHITE}{line4:<{inner_width}}{RESET}{RED}║{RESET}
{RED}╚══════════════════════════════════════════════════════════════════════════╝{RESET}
"""

    print(header)

    # Clean extra positions display (optional, below the box)
    if dashboard_metrics["positions"]:
        for symbol, pos in dashboard_metrics["positions"].items():
            if pos.get('entry', 0) <= 0:
                continue
            current = pos.get('current', pos['entry'])
            pnl_pct = ((current - pos['entry']) / pos['entry']) * 100 if pos['entry'] > 0 else 0
            pnl_sign = "+" if pnl_pct >= 0 else ""
            status = "\033[92m[T]\033[0m" if pnl_pct >= pos['target_pct'] else ("\033[91m[SL]\033[0m" if pnl_pct <= -pos['sl_pct'] else "   ")
            pos_line = f"  └─ {symbol:10s} {pos['qty']:2d}@₹{pos['entry']:.2f} → ₹{current:.2f} ({pnl_sign}{pnl_pct:+.2f}%) {status}"
            print(f"{RED}║{RESET}{WHITE}{pos_line:<{inner_width}}{RESET}{RED}║{RESET}")
        print(f"{RED}╚══════════════════════════════════════════════════════════════════════════╝{RESET}")

    # Only print market closed message when actually closed
    if strategy == "MARKET_CLOSED":
        print(f"{RED}Market closed. Bot stopping.{RESET}")