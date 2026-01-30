import requests

BASE_URL = "http://localhost:8203/api/avatar/start"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

data = {
    "avatar_name": "test_avatar"
}


response = requests.post(BASE_URL, headers=headers, data=data)


print("Status Code:", response.status_code)
try:
    resp_data = response.json()
    if resp_data.get("status") == "success":
        print("success")
    else:
        print("Fail：", resp_data)
except Exception as e:
    print("Not json：", e)
    print("content", response.text)
