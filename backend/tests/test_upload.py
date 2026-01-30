# test_upload_file.py
import requests
import os
import mimetypes

BASE_URL = "http://localhost:8203/api"

token='token'


file_path = "../uploads/test_20250727.pdf"
file_type = "document"

headers = {
    "Authorization": f"Bearer {token}"
}

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

filename = os.path.basename(file_path)
mime_type, _ = mimetypes.guess_type(file_path)

with open(file_path, "rb") as f:
    files = {
        "file": (filename, f, mime_type),
    }
    data = {
        "type": file_type
    }

    response = requests.post(f"{BASE_URL}/upload", headers=headers, files=files, data=data)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text:", response.text)
