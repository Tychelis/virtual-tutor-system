import requests

BASE_URL = "http://localhost:8203/api"

token='token'

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(f"{BASE_URL}/chat/history", headers=headers)

print("Status:", response.status_code)
print("Response:", response.json())