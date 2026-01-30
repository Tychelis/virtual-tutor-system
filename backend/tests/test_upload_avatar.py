import requests
import os

BASE_URL = "http://localhost:8203/api"
AVATAR_FILE = "test.jpg"

token='token'

headers = {
    "Authorization": f"Bearer {token}"
}

if not os.path.exists(AVATAR_FILE):
    print(f"Avatar file not found: {AVATAR_FILE}")
    exit(1)

files = {
    "avatar": open(AVATAR_FILE, "rb")
}

response = requests.post(f"{BASE_URL}/user/avatar", headers=headers, files=files)

print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Response (non-JSON):", response.text)

files["avatar"].close()
