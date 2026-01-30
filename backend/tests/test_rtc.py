import requests
forward_payload = {
    "sessionid": 123,
    "text": "Hello world",
    "answer": 'World Hello',
    "type": "echo",
    "interrupt": False
}
forward_response = requests.post(
    "http://localhost:8010/human",
    json=forward_payload,
    timeout=5
)
forward_response.raise_for_status()


print(forward_response.status_code)
