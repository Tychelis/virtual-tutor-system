import requests

BASE_URL = "http://localhost:8203/api"

token='token'


file_name = "test_0727.pdf"
headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.delete(f"{BASE_URL}/upload/{file_name}", headers=headers)
print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)
