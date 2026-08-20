import upstox_client
import webbrowser

# Your API credentials
API_KEY = "18185106-6257-4a85-a84a-2ea314f91927"
API_SECRET = "15m0va42ni"
REDIRECT_URI = "http://127.0.0.1:8000"

print("=" * 60)
print("UPSTOX TRADING BOT - AUTHENTICATION")
print("=" * 60)

# Step 1: Create configuration
configuration = upstox_client.Configuration()

# Generate login URL
login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"

print("\n🔐 Opening browser for login...")
print(f"Login URL: {login_url}\n")

# Open browser
webbrowser.open(login_url)

# Step 2: Get authorization code
print("⏳ After login, copy the FULL redirect URL from browser")
print("Example: http://127.0.0.1:8000/?code=XXXXXX\n")
redirect_url = input("Paste redirect URL here: ").strip()

# Extract code
if '?code=' in redirect_url:
    auth_code = redirect_url.split('?code=')[1].split('&')[0]
    print(f"\n✅ Got authorization code: {auth_code[:10]}...")

    # Step 3: Exchange code for access token
    try:
        api_instance = upstox_client.LoginApi()

        api_response = api_instance.token(
            api_version='2.0',
            code=auth_code,
            client_id=API_KEY,
            client_secret=API_SECRET,
            redirect_uri=REDIRECT_URI,
            grant_type='authorization_code'
        )

        access_token = api_response.access_token

        print(f"\n🎉 SUCCESS! Authentication complete!")
        print(f"Access Token (COPY THIS): {access_token}")

        # Save token
        with open('upstox_token.txt', 'w') as f:
            f.write(access_token)

        print("\n💾 Token saved to 'upstox_token.txt'")

        # Test connection - get profile
        configuration.access_token = access_token
        user_api = upstox_client.UserApi(upstox_client.ApiClient(configuration))
        profile = user_api.get_profile(api_version='2.0')

        print(f"\n👤 Logged in as: {profile.data.user_name}")
        print(f"📧 Email: {profile.data.email}")

        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE! Ready to trade!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n❌ Invalid URL. Should contain '?code='")