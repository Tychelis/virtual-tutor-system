import requests

BASE_URL = "http://localhost:8203/api"
ENDPOINT = "/user/profile"

token='token'


headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Error parsing response:", response.text)
