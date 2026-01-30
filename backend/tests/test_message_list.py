import requests

BASE_URL = "http://localhost:8203/api"

token='token'


headers = {"Authorization": f"Bearer {token}"}
print("Headers:", headers)

session_id = 6

url = f"{BASE_URL}/message/list?session_id={session_id}"
response = requests.get(url, headers=headers)

print(f"\n=== Message List for Session {session_id} ===")
print(response.json())
# print("Status Code:", response.status_code)
#
# try:
#     messages = response.json()
#     if isinstance(messages, list):
#         for idx, msg in enumerate(messages, 1):
#             print(f"[{idx}] ({msg['created_at']}) {msg['role']}: {msg['content']}")
#         print(f"\nTotal messages: {len(messages)}")
#     else:
#         print("Response:", messages)
# except Exception as e:
#     print("Failed to parse response:")
#     print(response.text)
