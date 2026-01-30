import requests

BASE_URL = "http://localhost:8203/api/llm/activate"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "model": "mistral-nemo:12b-instruct-2407-fp16"
}

response = requests.post(BASE_URL, headers=headers, json=data)

print("Status Code:", response.status_code)
try:
    resp_data = response.json()
    if "message" in resp_data:
        print("success:", resp_data["message"])
    else:
        print("fail:", resp_data)
except Exception as e:
    print("NOT JSON：", e)
    print("content:", response.text)
