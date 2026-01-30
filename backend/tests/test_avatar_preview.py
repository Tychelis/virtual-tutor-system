import requests


BASE_URL = "http://localhost:8203/api/avatar"
ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

data = {
    "avatar_name": "avator_1"
}

response = requests.post(f"{BASE_URL}/preview", headers=headers, data=data)
data = response.json()
print(data)
print("Status Code:", response.status_code)
content_type = response.headers.get("Content-Type", "")
print("Content-Type:", content_type)

if response.status_code == 200 and content_type.startswith("image/"):
    print("success")
else:
    print("fail")
    try:
        print("content：", response.json())
    except Exception:
        print("orginal_content：", response.text)

