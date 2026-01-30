import requests
import time

BASE_URL = "http://localhost:8203/api"

# 1. User login to get Token
# login_data = {
#     "email": "lu17waterloo@gmail.com",
#     "password": "123456"
# }
# res = requests.post(f"{BASE_URL}/login", json=login_data)
# if res.status_code != 200:
#     print("Login failed")
#     exit()
# token = res.json()["token"]
# print("Login successful, Token obtained")
token='token'

# 2. Check remaining time of token
headers = {"Authorization": f"Bearer {token}"}
print(headers)
status_res = requests.get(f"{BASE_URL}/token_status", headers=headers)
print(status_res.status_code)
# print("Response Text:", status_res.text)
if status_res.status_code == 200:
    print("Token remaining validity time:")
    print(status_res.json())
else:
    print("Unable to get token status")

# 3. Use this token to access protected endpoint `/chat`
chat_data = {"message": "hello from persistent test"}
chat_res = requests.post(f"{BASE_URL}/chat", headers=headers, data=chat_data)

if chat_res.status_code == 200:
    print("Successfully accessed chat endpoint, response:")
    print(chat_res.json())
else:
    print("Failed to access chat endpoint", chat_res.status_code)

# time.sleep(5)
# print('after 5 seconds')
#
# status_res = requests.get(f"{BASE_URL}/token_status", headers=headers)
# print(status_res.status_code)
# print("Response Text:", status_res.text)
# if status_res.status_code == 200:
#     print("Token remaining validity time:")
#     print(status_res.json())
# else:
#     print("Unable to get token status")
#
# # 3. Use this token to access protected endpoint `/chat`
# chat_data = {"message": "hello from persistent test"}
# chat_res = requests.post(f"{BASE_URL}/chat", headers=headers, data=chat_data)
#
# if chat_res.status_code == 200:
#     print("Successfully accessed chat endpoint, response:")
#     print(chat_res.json())
# else:
#     print("Failed to access chat endpoint", chat_res.status_code)

