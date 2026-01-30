import requests
import os


BASE_URL = "http://localhost:8203/api"



token='token'



headers = {"Authorization": f"Bearer {token}"}
print(headers)


image_path = "test.jpg"
audio_path = "test.m4a"
doc_path   = "test.pdf"
text_msg   = "check the file i uploaded,what is paul?"
# text_msg   = "tell me something about you"


files = {}
# print(os.getcwd())
# if os.path.exists(image_path):
#     files["image"] = open(image_path, "rb")
#
# if os.path.exists(audio_path):
#     files["audio"] = open(audio_path, "rb")
#
# if os.path.exists(doc_path):
#     files["document"] = open(doc_path, "rb")

data = {
    "message": text_msg
}

response = requests.post(f"{BASE_URL}/chat", headers=headers, files=files, data=data)
print(response)
print(response.json())



for f in files.values():
    f.close()

print("Response:")
try:
    print(response.json())
except Exception:
    print(response.text)


uploads_dir = "../uploads"

for key in ["image", "audio", "document"]:
    if key in response.json():
        filename = response.json()[key].replace("Received: ", "").strip()
        saved_path = os.path.join(uploads_dir, filename)
        print(f"Checking if file '{saved_path}' was actually saved...")
        if os.path.exists(saved_path):
            print(f"File exists: {saved_path}")
            try:
                if filename.endswith((".txt", ".pdf", ".docx")):
                    with open(saved_path, "rb") as f:
                        print(f"First 100 bytes:\n{f.read(100)}")
                elif filename.endswith((".jpg", ".png", ".wav", ".mp3")):
                    size = os.path.getsize(saved_path)
                    print(f"Binary file saved, size = {size} bytes")
            except Exception as e:
                print(f"Error reading file: {e}")
        else:
            print(f"File NOT found: {saved_path}")

