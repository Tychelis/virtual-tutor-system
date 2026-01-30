import requests

API_URL = "http://localhost:8203/api/admin/users/{}"

ADMIN_TOKEN='ADMIN_TOKEN'

USER_ID_TO_DELETE = 3

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

def test_delete_user():
    url = API_URL.format(USER_ID_TO_DELETE)
    response = requests.delete(url, headers=headers)

    print(f"Status Code: {response.status_code}")
    print("Response JSON:", response.json())

if __name__ == "__main__":
    test_delete_user()
