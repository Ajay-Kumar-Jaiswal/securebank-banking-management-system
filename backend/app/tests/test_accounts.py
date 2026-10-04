def test_create_account(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["accountType"] == "SAVINGS"
    assert data["balance"] == 0.0 or data["balance"] == "0.00"
    assert data["status"] == "ACTIVE"
    assert data["accountNumber"].startswith("AC")


def test_view_accounts(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    client.post("/api/accounts", json={"accountType": "CURRENT"}, headers=headers)

    res = client.get("/api/accounts", headers=headers)
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) == 2


def test_unauthorized_account_access(client, test_customer_token, test_customer2_token):
    # Customer 1 creates an account
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    create_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h1)
    acc_id = create_res.json()["accountId"]

    # Customer 2 attempts to view Customer 1's account
    h2 = {"Authorization": f"Bearer {test_customer2_token}"}
    res = client.get(f"/api/accounts/{acc_id}", headers=h2)
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"
