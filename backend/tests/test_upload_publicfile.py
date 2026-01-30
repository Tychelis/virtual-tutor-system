import requests

token='token'

BASE_URL = "http://localhost:8203/api"

headers = {"Authorization": f"Bearer {token}"}

print("Requesting /public_files...")
response = requests.get(f"{BASE_URL}/public_files", headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)

