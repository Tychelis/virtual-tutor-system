import requests
import os
import sys

BASE_URL = "http://localhost:8203/api"

token='token'


headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(headers)

session_id = 3

url = f"{BASE_URL}/chat/{session_id}/favorite"
payload = {"is_favorite": True}
response = requests.post(url, headers=headers, json=payload)

print(f"\n=== Set Favorite Session {session_id} ===")
print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Raw Response:", response.text)

url = f"{BASE_URL}/chat/history"
response = requests.get(url, headers=headers)

print(f"\n=== Session List ===")
print("Status Code:", response.status_code)
try:
    sessions = response.json()
    for s in sessions:
        fav = "True" if s.get("is_favorite") else " "
        print(f"{fav} Session {s['id']} - {s['title']} - {s['updated_at']}")
    fav_count = sum(1 for s in sessions if s.get("is_favorite"))
    print(f"\nFavorite count: {fav_count}")
except Exception:
    print("Failed to parse session list response.")
