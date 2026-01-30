import requests
import time

start = time.perf_counter()
files = [('prompt_wav', ('ref.wav', open('ref.wav', 'rb'), 'application/octet-stream'))]
payload = {
    'tts_text': "this is a test",
    'prompt_text': "reftext"
}

resp = requests.request(
    "GET",
    "http://localhost:8000/tts_zero_shot",
    data=payload,
    files=files,
    stream=True
)
end = time.perf_counter()
print(f"cosy_voice Time to make POST: {end-start} s")

if resp.status_code == 200:
    print("Response received successfully.")
else:
    print("Error:", resp.status_code, resp.text)

