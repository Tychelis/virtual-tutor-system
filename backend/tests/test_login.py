import requests
import jwt

base = "http://localhost:8203/api"
email = ("your_email")
password = "your_password"

resp = requests.post(f"{base}/send_verification", json={
    "email": email,
    "purpose": "register"
})
print("Send Verification Code:", resp.status_code, resp.json())

if resp.status_code == 200:
    code = input("Please enter your verification code: ")

    resp = requests.post(f"{base}/register", json={
        "email": email,
        "password": password,
        "code": code
    })
    print("Register:", resp.status_code)
    print("Raw Response Text:", resp.text)
    print("Register:", resp.status_code, resp.json())

resp = requests.post(f"{base}/login", json={
    "email": email,
    "password": password
})
print(resp)
print("Login:", resp.status_code, resp.json())
token = resp.json()["token"]
print(token)
print(type(token))

payload = jwt.decode(token, options={"verify_signature": False})
print("Decoded Payload:")
print(payload)

print("\nUser Role:", payload.get("role"))
