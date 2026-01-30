import requests

BASE_URL = "http://localhost:8203/api"

ADMIN_TOKEN='ADMIN_TOKEN'



headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

def test_get_models():
    response = requests.get(f"{BASE_URL}/admin/models", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("model list:")
        for model in data["models"]:
            print(f"- {model['name']} ({model['type']}, {model['status']})")
    else:
        print(f"Fail: {response.status_code} {response.text}")

def test_get_knowledge():
    response = requests.get(f"{BASE_URL}/admin/knowledge", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("knowledge base list:")
        for item in data["knowledge"]:
            print(f"- {item['name']} ({item['type']}, {item['status']})")
    else:
        print(f"Fail: {response.status_code} {response.text}")

if __name__ == "__main__":
    test_get_models()
    test_get_knowledge()
