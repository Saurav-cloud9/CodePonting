import requests

# Your API credentials
api_key = "18185106-6257-4a85-a84a-2ea314f91927"
api_secret = "15m0va42ni"
redirect_uri = "http://127.0.0.1:8000"

# Step 1: Generate login URL
print("Go to this URL and login:")
print(f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}")

# Get authorization code from user
auth_code = input("\nPaste the authorization code here: ")

# Step 2: Exchange code for access token
token_url = "https://api.upstox.com/v2/login/authorization/token"
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}
data = {
    'code': auth_code,
    'client_id': api_key,
    'client_secret': api_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code',
}

response = requests.post(token_url, headers=headers, data=data)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    print(f"\n✅ SUCCESS! Access Token: {access_token}")
    print("\nYou're now authenticated! Ready to trade!")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)