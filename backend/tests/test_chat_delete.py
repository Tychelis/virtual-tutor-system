import requests

BASE_URL = "http://localhost:8203/api"

token='token'

session_id_to_delete = 3

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.delete(f"{BASE_URL}/chat/{session_id_to_delete}", headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Raw Response:", response.text)
