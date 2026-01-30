import requests

BASE_URL = "http://localhost:8203/api"
ENDPOINT = "/admin/users"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

new_user_data = {
    "email": "newstudent@example.com",
    "password": "123456",
    "username": "Oblivionis",
    "role": "student",
    "full_name": "Togawa Sakiko",
    "phone": "13800000000",
    "bio": "Polite and refined.",
    "avatar_url": "/static/avatars/default.jpg"
}

response = requests.post(f"{BASE_URL}{ENDPOINT}", json=new_user_data, headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Raw Response:", response.text)
