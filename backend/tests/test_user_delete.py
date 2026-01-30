import requests

BASE_URL = "http://localhost:8203/api"
EMAIL = "youremail"
PASSWORD = "yourpassword"

def login(email, password):
    resp = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": password
    })
    if resp.status_code == 200:
        token = resp.json()["token"]
        print("Login successful.")
        return token
    else:
        print("Login failed:", resp.status_code, resp.text)
        return None

def send_delete_verification_code(email):
    resp = requests.post(f"{BASE_URL}/send_verification", json={
        "email": email,
        "purpose": "delete_account"
    })
    print("Send verification code:", resp.status_code, resp.json())
    return resp.status_code == 200

def delete_account(token, code):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    resp = requests.delete(f"{BASE_URL}/user/delete_account", json={
        "code": code
    }, headers=headers)
    print("Delete Account:", resp.status_code)
    print(resp.json())

def main():
    token = login(EMAIL, PASSWORD)
    if not token:
        return

    if not send_delete_verification_code(EMAIL):
        return


    code = input("Please enter the verification code sent to your email: ")


    delete_account(token, code)

if __name__ == "__main__":
    main()
