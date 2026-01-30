import requests

BASE_URL = "http://localhost:8203/api"

ADMIN_TOKEN='ADMIN_TOKEN'

def get_logs(operator_email=None, target_user_email=None, action=None, page=1, per_page=10):
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    params = {
        "page": page,
        "per_page": per_page
    }

    if operator_email:
        params["operator_email"] = operator_email
    if target_user_email:
        params["target_user_email"] = target_user_email
    if action:
        params["action"] = action

    response = requests.get(f"{BASE_URL}/admin/user-action-logs", headers=headers, params=params)

    print(f"Status Code: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"Total Logs: {data['total']}")
        for log in data['logs']:
            print("—" * 40)
            print(f"ID: {log['id']}")
            print(f"Operator: {log['operator_email']}")
            print(f"Action: {log['action']}")
            print(f"Target ID: {log['target_user_id']}")
            print(f"Target Email: {log['target_user_email']}")
            print(f"Details: {log['details']}")
            print(f"Reason: {log.get('reason', '')}")
            print(f"Timestamp: {log['timestamp']}")
    else:
        print("Error:", response.text)


if __name__ == "__main__":
    # get_logs(operator_email="lu17waterloo@gmail.com")

    # get_logs(target_user_email="newstudent@example.com")

    get_logs(operator_email="lu17waterloo@gmail.com", target_user_email="newstudent@example.com", action="delete")
