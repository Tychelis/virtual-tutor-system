import requests
import jwt

base = "http://localhost:8203/api"
email = "youremail"
old_password = "old password"
new_password = "new password"

resp = requests.post(f"{base}/login", json={
    "email": email,
    "password": old_password
})
print("Login with old password:", resp.status_code)
if resp.status_code != 200:
    print("Login failed, can't proceed.")
    exit(1)

token = resp.json()["token"]
print("Old Token:", token)

resp = requests.post(f"{base}/send_verification", json={
    "email": email,
    "purpose": "update_password"
})
print("Send Verification Code:", resp.status_code, resp.json())

if resp.status_code == 200:
    code = input("Please enter your verification code: ")

    resp = requests.post(f"{base}/update_password", json={
        "code": code,
        "new_password": new_password
    }, headers={
        "Authorization": f"Bearer {token}"
    })

    print("Update Password:", resp.status_code, resp.json())
    if resp.status_code != 200:
        print("Password update failed.")
        exit(1)

    resp = requests.post(f"{base}/login", json={
        "email": email,
        "password": new_password
    })
    print("Login with new password:", resp.status_code)
    print("Response:", resp.json())

    if resp.status_code == 200:
        new_token = resp.json()["token"]
        print("New Token:", new_token)

        payload = jwt.decode(new_token, options={"verify_signature": False})
        print("Decoded Payload:", payload)
        print("User Role:", payload.get("role"))
    else:
        print("Login with new password failed.")
else:
    print("Failed to send verification code.")
