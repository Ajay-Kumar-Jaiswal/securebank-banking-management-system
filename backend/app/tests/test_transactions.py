def test_deposit_success(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    acc_id = acc_res.json()["accountId"]

    res = client.post(
        "/api/transactions/deposit",
        json={"accountId": acc_id, "amount": "5000.50", "description": "Salary"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert float(data["amount"]) == 5000.50
    assert float(data["balanceAfter"]) == 5000.50
    assert data["transactionType"] == "DEPOSIT"
    assert data["status"] == "SUCCESS"


def test_deposit_invalid_amount(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    acc_id = acc_res.json()["accountId"]

    res = client.post(
        "/api/transactions/deposit",
        json={"accountId": acc_id, "amount": "-10.00"},
        headers=headers,
    )
    assert res.status_code == 422  # Pydantic validation error or 400


def test_deposit_unauthorized(client, test_customer_token, test_customer2_token):
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h1)
    acc_id = acc_res.json()["accountId"]

    h2 = {"Authorization": f"Bearer {test_customer2_token}"}
    res = client.post(
        "/api/transactions/deposit",
        json={"accountId": acc_id, "amount": "100.00"},
        headers=h2,
    )
    assert res.status_code == 403


def test_withdrawal_success_and_insufficient_funds(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    acc_id = acc_res.json()["accountId"]

    # Initial deposit
    client.post("/api/transactions/deposit", json={"accountId": acc_id, "amount": "1000.00"}, headers=headers)

    # Withdraw 400
    w_res = client.post("/api/transactions/withdraw", json={"accountId": acc_id, "amount": "400.00"}, headers=headers)
    assert w_res.status_code == 200
    assert float(w_res.json()["balanceAfter"]) == 600.00

    # Withdraw 700 (insufficient)
    fail_res = client.post("/api/transactions/withdraw", json={"accountId": acc_id, "amount": "700.00"}, headers=headers)
    assert fail_res.status_code == 400
    assert fail_res.json()["error"] == "INSUFFICIENT_BALANCE"


def test_withdrawal_unauthorized(client, test_customer_token, test_customer2_token):
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h1)
    acc_id = acc_res.json()["accountId"]
    client.post("/api/transactions/deposit", json={"accountId": acc_id, "amount": "100.00"}, headers=h1)

    h2 = {"Authorization": f"Bearer {test_customer2_token}"}
    res = client.post(
        "/api/transactions/withdraw",
        json={"accountId": acc_id, "amount": "50.00"},
        headers=h2,
    )
    assert res.status_code == 403


def test_transfer_success_and_failures(client, test_customer_token, test_customer2_token):
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    h2 = {"Authorization": f"Bearer {test_customer2_token}"}

    # Customer 1 account with 1000 balance
    acc1_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h1)
    acc1_id = acc1_res.json()["accountId"]
    acc1_num = acc1_res.json()["accountNumber"]
    client.post("/api/transactions/deposit", json={"accountId": acc1_id, "amount": "1000.00"}, headers=h1)

    # Customer 2 account
    acc2_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h2)
    acc2_num = acc2_res.json()["accountNumber"]

    # 1. Transfer to same account fails
    res_same = client.post(
        "/api/transactions/transfer",
        json={"fromAccountId": acc1_id, "toAccountNumber": acc1_num, "amount": "100.00"},
        headers=h1,
    )
    assert res_same.status_code == 400

    # 2. Transfer with insufficient funds fails
    res_no_funds = client.post(
        "/api/transactions/transfer",
        json={"fromAccountId": acc1_id, "toAccountNumber": acc2_num, "amount": "2000.00"},
        headers=h1,
    )
    assert res_no_funds.status_code == 400
    assert res_no_funds.json()["error"] == "INSUFFICIENT_BALANCE"

    # 3. Successful transfer of 350
    tx_res = client.post(
        "/api/transactions/transfer",
        json={"fromAccountId": acc1_id, "toAccountNumber": acc2_num, "amount": "350.00"},
        headers=h1,
    )
    assert tx_res.status_code == 200
    data = tx_res.json()
    assert float(data["balanceAfter"]) == 650.00

    # Check recipient's account balance
    acc2_detail = client.get(f"/api/accounts/{acc2_res.json()['accountId']}", headers=h2)
    assert float(acc2_detail.json()["balance"]) == 350.00


def test_transaction_history_and_filters(client, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=headers)
    acc_id = acc_res.json()["accountId"]

    client.post("/api/transactions/deposit", json={"accountId": acc_id, "amount": "500.00"}, headers=headers)
    client.post("/api/transactions/withdraw", json={"accountId": acc_id, "amount": "100.00"}, headers=headers)

    # Get all
    history = client.get(f"/api/transactions?accountId={acc_id}", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 2

    # Filter by DEPOSIT
    dep_only = client.get(f"/api/transactions?accountId={acc_id}&type=DEPOSIT", headers=headers)
    assert dep_only.status_code == 200
    assert len(dep_only.json()) == 1
    assert dep_only.json()[0]["transactionType"] == "DEPOSIT"
