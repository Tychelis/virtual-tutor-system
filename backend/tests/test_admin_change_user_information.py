import requests

API_BASE = "http://localhost:8203/api"

ADMIN_TOKEN='ADMIN_TOKEN'

USER_ID = 3

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    # "email": "updated_user@example.com",
    # "username": "Lacus Oblivionis",
    "username": "Oblivionis",
    # "full_name": "Updated Fullname",
    # "phone": "1234567890",
    # "bio": "Updated bio about the user.",
    # "avatar_url": "/static/avatars/user_2_avatar.jpg",
    # "role": "Tutor",
    # "status": "Active"
}

response = requests.put(
    f"{API_BASE}/admin/users/{USER_ID}",
    headers=headers,
    json=payload
)

print("Status:", response.status_code)
print("Response:", response.json())
