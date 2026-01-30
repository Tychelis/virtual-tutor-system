import requests

BASE_URL = "http://localhost:8203/api/tts/models"

ADMIN_TOKEN='ADMIN_TOKEN'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

response = requests.get(BASE_URL, headers=headers)

print("Status Code:", response.status_code)
content_type = response.headers.get("Content-Type", "")
print("Content-Type:", content_type)

try:
    data = response.json()
    if response.status_code == 200:
        print("success")
        for model_name, info in data.items():
            print(f"- {model_name} ({info.get('full_name')})")
            print(f"  clone: {info.get('clone')}, license: {info.get('license')}")
            print(f"  timbres: {info.get('timbres')}, cur_timbre: {info.get('cur_timbre')}")
    else:
        print("Fail", data)
except Exception as e:
    print("Not JSON：", e)
    print("content：", response.text)
