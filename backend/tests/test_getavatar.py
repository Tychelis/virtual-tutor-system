import requests

BASE_URL = "http://localhost:8203/api/avatar/list"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

payload = {

}

response = requests.get(f"http://localhost:8203/api/avatar/list", headers=headers, json=payload)
data = response.json()
first_key =list (data.keys())[0]
print(first_key)

print("Status Code:", response.status_code)
try:
    data = response.json()
    print("Response:", data)
except Exception as e:
    print("Failed to parse response:", e)
    print(response.text)
