import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PLANET_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLANET_CLIENT_SECRET")

TOKEN_URL = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
PROCESS_URL = "https://services.sentinel-hub.com/process/v1"

BBOX = [
    94.879,
    27.429,
    94.951,
    27.521
]

OUTPUT_FILE = "data/satellite/sentinel2_ner.tiff"


# ---------------------------------------------------------
# Get OAuth token
# ---------------------------------------------------------

token_response = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)

token_response.raise_for_status()

access_token = token_response.json()["access_token"]

print("OAuth token obtained successfully.")


# ---------------------------------------------------------
# Sentinel-2 request
# ---------------------------------------------------------

payload = {
    "input": {
        "bounds": {
            "bbox": BBOX,
            "properties": {
                "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
            }
        },
        "data": [
            {
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "maxCloudCoverage": 80
                }
            }
        ]
    },

    "output": {
        "width": 800,
        "height": 1000,
        "responses": [
            {
                "identifier": "default",
                "format": {
                    "type": "image/tiff"
                }
            }
        ]
    },

    "evalscript": """
    //VERSION=3

    function setup() {
        return {
            input: [
                "B04",
                "B08",
                "dataMask"
            ],
            output: {
                bands: 3,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {

        return [
            sample.B04,
            sample.B08,
            sample.dataMask
        ];

    }
    """
}


# ---------------------------------------------------------
# Send request
# ---------------------------------------------------------

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print("Requesting Sentinel-2 image...")
print(f"BBOX: {BBOX}")

response = requests.post(
    PROCESS_URL,
    headers=headers,
    json=payload
)


# ---------------------------------------------------------
# Check response
# ---------------------------------------------------------

print("HTTP status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Response size:", len(response.content), "bytes")

if response.status_code != 200:
    print()
    print("API response:")
    print(response.text[:5000])
    raise SystemExit


# ---------------------------------------------------------
# Save image
# ---------------------------------------------------------

os.makedirs("data/satellite", exist_ok=True)

with open(OUTPUT_FILE, "wb") as file:
    file.write(response.content)

print()
print("Sentinel-2 image downloaded successfully.")
print(f"Saved to: {OUTPUT_FILE}")