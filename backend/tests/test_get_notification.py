import requests

BASE_URL = "http://localhost:8203/api"

TOKEN='TOKEN'
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

params = {
    "page": 1,
    "limit": 5,
    "unread_only": "false"
}

response = requests.get(f"{BASE_URL}/user/notifications", headers=headers, params=params)

print("Status:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Response Text:", response.text)