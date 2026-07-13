import os
import re
import sys
import webbrowser
from pathlib import Path

from dotenv import load_dotenv
from kiteconnect import KiteConnect

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

API_KEY = os.getenv('KITE_API_KEY')
API_SECRET = os.getenv('KITE_API_SECRET')
print(f"Loading API Key from .env: {API_KEY[:6]}...")

print("=" * 70)
print("KITE CONNECT AUTHENTICATION")
print("=" * 70)

kite = KiteConnect(api_key=API_KEY)
login_url = kite.login_url()

if len(sys.argv) > 1:
    # Non-interactive mode: redirect URL/token passed as a CLI arg
    redirect_response = sys.argv[1].strip()
else:
    print("\n1. Opening browser for authorization...")
    print(f"\nIf browser doesn't open, copy this URL:")
    print(f"{login_url}\n")

    webbrowser.open(login_url)

    print("2. After login, the browser will redirect to https://127.0.0.1/...")
    print("   (it will show a connection error page — that's expected)")
    print("3. Copy the ENTIRE URL from the browser address bar")
    print("4. Paste it below:\n")

    redirect_response = input("Paste the full redirect URL (or just the request_token) here: ").strip()

match = re.search(r'request_token=([^&]+)', redirect_response)
request_token = match.group(1) if match else redirect_response

print(f"\n[OK] Request token extracted: {request_token}")

# Step 2: Exchange request_token for access_token
data = kite.generate_session(request_token, api_secret=API_SECRET)
access_token = data['access_token']

print(f"\n[OK] Access Token obtained!")
print(f"\n{'=' * 70}")
print("YOUR ACCESS TOKEN:")
print(f"{'=' * 70}")
print(f"{access_token}")
print(f"{'=' * 70}")

# Save access_token into .env so other scripts can load it via dotenv
env_lines = []
if env_path.exists():
    env_lines = env_path.read_text().splitlines()

env_lines = [line for line in env_lines if not line.startswith('KITE_ACCESS_TOKEN=')]
env_lines.append(f'KITE_ACCESS_TOKEN={access_token}')
env_path.write_text('\n'.join(env_lines) + '\n')

print(f"\nSaved to {env_path} as KITE_ACCESS_TOKEN.")
print("Re-run this script each morning — Kite tokens expire daily (~7:30am).")
print(f"{'=' * 70}")
