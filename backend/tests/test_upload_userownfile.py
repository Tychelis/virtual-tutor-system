import requests

BASE_URL = "http://localhost:8203/api"

token='token'

headers = {"Authorization": f"Bearer {token}"}

print("Requesting /user_files...")
response = requests.get(f"{BASE_URL}/user_files", headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)
