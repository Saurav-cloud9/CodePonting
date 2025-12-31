# Complete minimal code to draw your perfect trading dashboard table 🎉💹

RED = '\033[91m'              # Bright red for borders
BLUE = '\033[38;5;33m'        # Your sweet-spot brighter blue
WHITE = '\033[97m'            # Bright white for data rows
RESET = '\033[0m'             # Reset colors

# Dummy example values (replace with your real ones)
line1 = "MA Bounce Bot v0.5 - LIVE TRADING"
line2 = "03:58:07 PM | WAITING               | Next scan: ..."
line3 = "TODAY: Signals:  0 | Trades:  0 | Win:  0 | Loss:  0 | P&L: ₹+0.00"
line4 = "POSITIONS: 0 active"

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

# Optional: add your "Market closed" message below
print(f"{RED}Market closed. Bot stopping.{RESET}")