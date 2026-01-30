import requests

BASE_URL = "http://localhost:8203/api"

token='token'

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Headers:", headers)

title = "My New Test Session"

url = f"{BASE_URL}/chat/new"
payload = {"title": title}
response = requests.post(url, headers=headers, json=payload)

print("\n=== Create Session ===")
print("Status Code:", response.status_code)
try:
    result = response.json()
    print("Response JSON:", result)
    session_id = result.get("session_id")
    if session_id:
        print(f"New session created with ID: {session_id}")
except Exception:
    print("Failed to parse response:")
    print(response.text)
