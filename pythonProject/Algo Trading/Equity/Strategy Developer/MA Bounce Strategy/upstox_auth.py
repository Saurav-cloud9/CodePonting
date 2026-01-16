import requests
import webbrowser
import urllib.parse

# NEW
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('UPSTOX_API_KEY')
API_SECRET = os.getenv('UPSTOX_API_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8000'


print("=" * 70)
print("UPSTOX AUTHENTICATION")
print("=" * 70)

# Step 1: Generate authorization URL
auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?client_id={API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"

print("\n1. Opening browser for authorization...")
print(f"\nIf browser doesn't open, copy this URL:")
print(f"{auth_url}\n")

# Open browser
webbrowser.open(auth_url)

print("2. After login, you'll be redirected to a URL")
print("3. Copy the ENTIRE URL from browser address bar")
print("4. Paste it below:\n")

# Get the redirected URL from user
redirect_response = input("Paste the full redirect URL here: ")

# Extract authorization code
parsed = urllib.parse.urlparse(redirect_response)
auth_code = urllib.parse.parse_qs(parsed.query)['code'][0]

print(f"\n✓ Authorization code extracted: {auth_code}")

# Step 2: Get access token
token_url = "https://api.upstox.com/v2/login/authorization/token"
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

data = {
    'code': auth_code,
    'client_id': API_KEY,
    'client_secret': API_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'authorization_code'
}

response = requests.post(token_url, headers=headers, data=data)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']

    print(f"\n✓ Access Token obtained!")
    print(f"\n{'=' * 70}")
    print("YOUR ACCESS TOKEN:")
    print(f"{'=' * 70}")
    print(f"{access_token}")
    print(f"{'=' * 70}")
    print("\nSAVE THIS TOKEN - You'll use it in your scanner!")
    print(f"{'=' * 70}")
else:
    print(f"\n❌ Error getting token: {response.text}")