import json
import base64

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJFRTY4MTkiLCJqdGkiOiI2OTMyODA4OTUwZjM4NzRkYmExNzExZTkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2NDkxNzM4NSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY0OTcyMDAwfQ.bs9bB791bbO5q94pz_dDoGzhJhWPDOxqhlE-yCrOIc4"

# Split the token
parts = token.split('.')
payload = parts[1]

# Add padding if needed (Base64 requires it)
padding = len(payload) % 4
if padding:
    payload += '=' * (4 - padding)

# Decode from Base64
decoded = base64.b64decode(payload)

# Convert to JSON
data = json.loads(decoded)

# Pretty print
print(json.dumps(data, indent=2))

# Convert expiry timestamp to readable time
import datetime
exp_time = datetime.datetime.fromtimestamp(data['exp'])
print(f"\nToken expires at: {exp_time}")