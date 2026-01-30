import requests

BASE_URL = "http://localhost:8203/api/avatar/delete"


ADMIN_TOKEN='ADMIN_TOKEN'


headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

data = {
    "name": "test_avatar_backend"
}

response = requests.post(BASE_URL, headers=headers, data=data)

print("Status Code:", response.status_code)
content_type = response.headers.get("Content-Type", "")
print("Content-Type:", content_type)

try:
    resp_data = response.json()
    if resp_data.get("status") == "success":
        print("success")
    else:
        print("delete", resp_data)
except Exception as e:
    print("not json：", e)
    print("content：", response.text)
