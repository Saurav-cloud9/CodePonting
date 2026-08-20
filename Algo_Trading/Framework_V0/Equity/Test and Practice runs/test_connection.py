import requests

# Your access token from the previous step
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTMyODA4OTUwZjM4NzRkYmExNzExZTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NDkxNzM4NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY0OTcyMDAwfQ.bs9bB791bbO5q94pz_dDoGzhJhWPDOxqhlE-yCrOIc4"

# Test 1: Get your profile
url = "https://api.upstox.com/v2/user/profile"
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    profile = response.json()
    print("✅ Profile fetched successfully!")
    print(f"\nUser ID: {profile['data']['user_id']}")
    print(f"Name: {profile['data']['user_name']}")
    print(f"Email: {profile['data']['email']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)