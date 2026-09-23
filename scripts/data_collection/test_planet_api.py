import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PLANET_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLANET_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Planet OAuth credentials were not found.")
    raise SystemExit

TOKEN_URL = (
    "https://services.sentinel-hub.com/"
    "auth/realms/main/protocol/openid-connect/token"
)

response = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)

print("HTTP Status:", response.status_code)

if response.status_code == 200:
    token_data = response.json()
    print("OAuth authentication successful!")
    print("Access token received:", bool(token_data.get("access_token")))
else:
    print("OAuth authentication failed.")
    print(response.text)