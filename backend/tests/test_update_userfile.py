import requests

BASE_URL = "http://localhost:8203/api"

token='token'

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "username": "new_username",
    "full_name": "Lin Jian",
    "phone": "13800138000",
    "bio": "League of Legend s15 FMVP",
    "avatar": "/workspace/bowen/static/avatars/default.jpg"
}

response = requests.post(f"{BASE_URL}//user/profile", headers=headers, json=data)

print(f"Status Code: {response.status_code}")
try:
    print("Response:", response.json())
except Exception as e:
    print("Failed to parse response:", response.text)
