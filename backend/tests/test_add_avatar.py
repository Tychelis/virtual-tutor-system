import requests

BASE_URL = "http://localhost:8203/api/avatar/add"

ADMIN_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1NDMxNzc2OCwianRpIjoiMjg4ZmRlYTUtMmVlZC00NzM2LWI1N2MtMDc4YmI5Y2RhNjQ3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjE1NTIyOTA3Mzg3QDE2My5jb20iLCJuYmYiOjE3NTQzMTc3NjgsImV4cCI6MTc1NDMzNTc2OCwicm9sZSI6InR1dG9yIn0.VT1_bKS161Nn_flQ0QfmbFkw6A3ZCCbi6WprcvwISHk'

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

data = {
    "name": "test_avatar_backend_12",
    "avatar_blur": "true",
    "support_clone": "true",
    "timbre": "",
    "tts_model": "sovits",
    "avatar_model": "MuseTalk",
    "description": "this a test avatar for backend"
}

files = {
    "prompt_face": ("test_face.mp4", open("/workspace/bowen/uploads/test_bowen.mp4", "rb"), "video/mp4"),
    "prompt_voice": ("test_voice.wav", open("/workspace/bowen/uploads/test_bowen.mp4", "rb"), "audio/wav")
}

response = requests.post(BASE_URL, headers=headers, data=data, files=files)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Failed to parse JSON:", e)
    print("Raw Response:", response.text)
