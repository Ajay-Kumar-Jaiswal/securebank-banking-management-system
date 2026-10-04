import os
import requests
import json

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")


def main():
    print("Testing Live API...")
    # Health / Docs check
    try:
        r = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        print(f"Swagger Docs: {r.status_code}")
    except Exception as e:
        print(f"Server not running: {e}")
        return

    # Admin Login verification using environment variables
    admin_email = os.getenv("ADMIN_TEST_EMAIL")
    admin_password = os.getenv("ADMIN_TEST_PASSWORD")

    if admin_email and admin_password:
        print(f"Testing Admin login for '{admin_email}'...")
        admin_login = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": admin_email, "password": admin_password},
        )
        print(f"Admin login status: {admin_login.status_code}")
        if admin_login.status_code == 200:
            token = admin_login.json().get("accessToken") or admin_login.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}

            # Dashboard metrics
            metrics = requests.get(f"{BASE_URL}/admin/dashboard", headers=headers)
            print(f"Admin metrics: {metrics.status_code}")
            if metrics.status_code == 200:
                print(json.dumps(metrics.json(), indent=2))

            # Closure / Account requests
            closures = requests.get(f"{BASE_URL}/admin/closure-requests", headers=headers)
            count = len(closures.json()) if closures.status_code == 200 else "N/A"
            print(f"Admin account requests: {closures.status_code}, count: {count}")

            # Audit logs
            audit = requests.get(f"{BASE_URL}/admin/audit-logs", headers=headers)
            audit_count = len(audit.json()) if audit.status_code == 200 else "N/A"
            print(f"Admin audit logs: {audit.status_code}, count: {audit_count}")
        else:
            print(f"Admin login failed: {admin_login.text}")
    else:
        print("Skipping admin tests: Set ADMIN_TEST_EMAIL and ADMIN_TEST_PASSWORD to verify admin endpoints.")

    # Customer Login verification using environment variables
    customer_email = os.getenv("CUSTOMER_TEST_EMAIL")
    customer_password = os.getenv("CUSTOMER_TEST_PASSWORD")

    if customer_email and customer_password:
        print(f"Testing Customer login for '{customer_email}'...")
        user_login = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": customer_email, "password": customer_password},
        )
        print(f"Customer login status: {user_login.status_code}")
        if user_login.status_code == 200:
            u_token = user_login.json().get("accessToken") or user_login.json().get("token")
            u_headers = {"Authorization": f"Bearer {u_token}"}
            accs = requests.get(f"{BASE_URL}/accounts", headers=u_headers)
            accs_count = len(accs.json()) if accs.status_code == 200 else "N/A"
            print(f"Customer accounts count: {accs_count}")
        else:
            print(f"Customer login failed: {user_login.text}")
    else:
        print("Skipping customer tests: Set CUSTOMER_TEST_EMAIL and CUSTOMER_TEST_PASSWORD to verify customer endpoints.")


if __name__ == "__main__":
    main()
