import requests

BASE_URL = "http://localhost:8203/api"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

params = {
    "page": 1,
    "limit": 10,
    "search": "",
    "role": "",
    "status": ""
}


response = requests.get(f"{BASE_URL}/admin/users", headers=headers, params=params)


print("Status Code:", response.status_code)
try:
    data = response.json()
    print("Total Users:", data.get("total"))
    print("Users on This Page:")
    for user in data.get("users", []):
        print(f"- {user} ")
except Exception as e:
    print("Failed to parse response:", e)
    print(response.text)
