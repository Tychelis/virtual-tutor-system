import requests

BASE_URL = "http://localhost:8203/api"
LOGIN_URL = f"{BASE_URL}/login"
LOGOUT_URL = f"{BASE_URL}/logout"
#
# login_data = {
#     "email": "test@example.com",
#     "password": "yourpassword"
# }
#
# login_response = requests.post(LOGIN_URL, json=login_data)
# assert login_response.status_code == 200, "Login failed"
#
# token = login_response.json().get("token")
# print("Login token:", token)

token='token'

headers = {
    "Authorization": f"Bearer {token}"
}

logout_response = requests.post(LOGOUT_URL, headers=headers)
print("Logout status code:", logout_response.status_code)
print("Logout response:", logout_response.json())

