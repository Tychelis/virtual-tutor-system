import requests

BASE_URL = "http://localhost:8203/api"

TOKEN='TOKEN'

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 要标记为已读的通知 ID
notification_id = 1

response = requests.put(
    f"{BASE_URL}/user/notifications/{notification_id}/read",
    headers=headers
)

print("Status:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Text:", response.text)