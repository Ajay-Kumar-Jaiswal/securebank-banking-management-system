def test_account_closure_flow(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # 1. Customer creates account
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=cust_h)
    acc_id = acc_res.json()["accountId"]

    # 2. Deposit money so balance > 0
    client.post("/api/transactions/deposit", json={"accountId": acc_id, "amount": "500.00"}, headers=cust_h)

    # 3. Attempt closure with balance > 0 -> should fail
    fail_res = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Moving out of country", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert fail_res.status_code == 400
    assert "Please withdraw or transfer your remaining balance" in fail_res.json()["message"]

    # 4. Withdraw all money so balance is 0.00
    client.post("/api/transactions/withdraw", json={"accountId": acc_id, "amount": "500.00"}, headers=cust_h)

    # 5. Submit closure request now -> succeeds
    req_res = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Relocating abroad", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert req_res.status_code == 201
    closure_req_id = req_res.json()["id"]
    assert req_res.json()["status"] == "PENDING"

    # 6. Duplicate pending request fails
    dup_res = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Duplicate attempt", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["message"]

    # 7. Customer sees their request
    my_reqs = client.get("/api/account-requests/my", headers=cust_h)
    assert my_reqs.status_code == 200
    assert len(my_reqs.json()) == 1

    # 8. Admin sees the pending request
    admin_reqs = client.get("/api/admin/closure-requests?status=PENDING", headers=admin_h)
    assert admin_reqs.status_code == 200
    assert len(admin_reqs.json()) >= 1

    # 9. Admin approves request
    appr_res = client.post(
        f"/api/admin/closure-requests/{closure_req_id}/approve",
        json={"adminNotes": "Account verified with zero balance, approved."},
        headers=admin_h,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"

    # 10. Verify account status is now CLOSED
    acc_check = client.get(f"/api/accounts/{acc_id}", headers=cust_h)
    assert acc_check.json()["status"] == "CLOSED"

    # 11. Closed account cannot do transactions
    tx_fail = client.post(
        "/api/transactions/deposit",
        json={"accountId": acc_id, "amount": "100.00"},
        headers=cust_h,
    )
    assert tx_fail.status_code == 400


def test_account_closure_rejection_flow(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # Customer creates account with 0 balance
    acc_res = client.post("/api/accounts", json={"accountType": "CURRENT"}, headers=cust_h)
    acc_id = acc_res.json()["accountId"]

    # Submit closure request
    req_res = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Not using it anymore", "confirmationCheckbox": True},
        headers=cust_h,
    )
    req_id = req_res.json()["id"]

    # Admin rejects
    rej_res = client.post(
        f"/api/admin/closure-requests/{req_id}/reject",
        json={"adminNotes": "Account needs KYC verification before closure."},
        headers=admin_h,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # Account remains ACTIVE
    acc_check = client.get(f"/api/accounts/{acc_id}", headers=cust_h)
    assert acc_check.json()["status"] == "ACTIVE"


def test_account_reopen_flow(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # 1. Customer creates account
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=cust_h)
    acc_id = acc_res.json()["accountId"]

    # 2. Cannot request reopen on an ACTIVE account
    fail_reopen = client.post(
        "/api/account-requests/reopen",
        json={"accountId": acc_id, "reason": "Accidental closure", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert fail_reopen.status_code == 400
    assert "Only CLOSED accounts can be requested to reopen" in fail_reopen.json()["message"]

    # 3. Close the account via closure request
    close_req = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Closing for now", "confirmationCheckbox": True},
        headers=cust_h,
    )
    close_id = close_req.json()["id"]
    client.post(
        f"/api/admin/account-requests/{close_id}/approve",
        json={"adminNotes": "Approved closure"},
        headers=admin_h,
    )

    # 4. Verify account is CLOSED
    acc_check = client.get(f"/api/accounts/{acc_id}", headers=cust_h)
    assert acc_check.json()["status"] == "CLOSED"

    # 5. Cannot request closure on an already CLOSED account
    fail_close = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc_id, "reason": "Close again", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert fail_close.status_code == 400
    assert "Only ACTIVE accounts can be requested for closure" in fail_close.json()["message"]

    # 6. Submit valid reopen request
    reopen_res = client.post(
        "/api/account-requests/reopen",
        json={"accountId": acc_id, "reason": "Need to resume banking operations", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert reopen_res.status_code == 201
    assert reopen_res.json()["status"] == "PENDING"
    assert reopen_res.json()["requestType"] == "REOPEN"
    reopen_id = reopen_res.json()["id"]

    # 7. Duplicate reopen request fails
    dup_reopen = client.post(
        "/api/account-requests/reopen",
        json={"accountId": acc_id, "reason": "Duplicate reopen", "confirmationCheckbox": True},
        headers=cust_h,
    )
    assert dup_reopen.status_code == 400
    assert "already exists" in dup_reopen.json()["message"]

    # 8. Admin filters by request_type=REOPEN
    admin_reopens = client.get("/api/admin/account-requests?request_type=REOPEN", headers=admin_h)
    assert admin_reopens.status_code == 200
    assert any(r["id"] == reopen_id for r in admin_reopens.json())

    # 9. Admin rejects first
    rej_res = client.post(
        f"/api/admin/account-requests/{reopen_id}/reject",
        json={"adminNotes": "Identity re-verification required first."},
        headers=admin_h,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # Account remains CLOSED after rejection
    acc_check = client.get(f"/api/accounts/{acc_id}", headers=cust_h)
    assert acc_check.json()["status"] == "CLOSED"

    # 10. Customer submits another reopen request
    reopen_res2 = client.post(
        "/api/account-requests/reopen",
        json={"accountId": acc_id, "reason": "KYC submitted, please reopen", "confirmationCheckbox": True},
        headers=cust_h,
    )
    reopen_id2 = reopen_res2.json()["id"]

    # 11. Admin approves reopen
    appr_res = client.post(
        f"/api/admin/account-requests/{reopen_id2}/approve",
        json={"adminNotes": "KYC verified. Account reopened."},
        headers=admin_h,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"

    # 12. Account is now ACTIVE again
    acc_check = client.get(f"/api/accounts/{acc_id}", headers=cust_h)
    assert acc_check.json()["status"] == "ACTIVE"


def test_customer_details_endpoint_payload(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # Create account and transaction
    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=cust_h)
    acc_id = acc_res.json()["accountId"]
    client.post("/api/transactions/deposit", json={"accountId": acc_id, "amount": "250.00"}, headers=cust_h)

    # Fetch customer ID from profile
    prof = client.get("/api/auth/me", headers=cust_h).json()
    customer_id = prof["userId"]

    # Fetch details as admin
    det_res = client.get(f"/api/admin/customers/{customer_id}", headers=admin_h)
    assert det_res.status_code == 200
    data = det_res.json()

    # Verify both customer and user keys are populated
    assert "customer" in data
    assert "user" in data
    assert data["customer"]["userId"] == customer_id
    assert data["user"]["userId"] == customer_id

    # Verify accounts and transactions
    assert len(data["accounts"]) >= 1
    assert data["totalTransactionsCount"] >= 1
    assert len(data["recentTransactions"]) >= 1

    # Verify closureRequests / accountRequests are present and not None
    assert "closureRequests" in data
    assert "accountRequests" in data
    assert isinstance(data["closureRequests"], list)

