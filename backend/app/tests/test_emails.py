from app.models.email_log import EmailLog


def test_emails_triggered_and_logged(client, test_customer_token, test_customer2_token, db_session):
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    h2 = {"Authorization": f"Bearer {test_customer2_token}"}

    # 1. Register new user -> triggers welcome email
    reg_res = client.post(
        "/api/auth/register",
        json={
            "fullName": "Email Tester",
            "email": "tester@example.com",
            "phoneNumber": "9000000000",
            "password": "Password123",
        },
    )
    assert reg_res.status_code == 201

    # Check email log
    welcome_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "tester@example.com").all()
    assert len(welcome_logs) >= 1
    assert "Welcome to SecureBank" in welcome_logs[0].subject

    # 2. Account creation triggers account created email
    acc1_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h1)
    acc1_id = acc1_res.json()["accountId"]

    acc_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "alice@example.com").all()
    assert any("Your Bank Account Has Been Created" in l.subject for l in acc_logs)

    # 3. Deposit triggers deposit email
    client.post("/api/transactions/deposit", json={"accountId": acc1_id, "amount": "1000.00"}, headers=h1)
    dep_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "alice@example.com").all()
    assert any("Deposit Confirmation" in l.subject for l in dep_logs)

    # 4. Withdrawal triggers withdrawal email
    client.post("/api/transactions/withdraw", json={"accountId": acc1_id, "amount": "200.00"}, headers=h1)
    with_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "alice@example.com").all()
    assert any("Withdrawal Confirmation" in l.subject for l in with_logs)

    # 5. Transfer triggers emails for both sender and receiver
    acc2_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h2)
    acc2_num = acc2_res.json()["accountNumber"]

    client.post(
        "/api/transactions/transfer",
        json={"fromAccountId": acc1_id, "toAccountNumber": acc2_num, "amount": "300.00"},
        headers=h1,
    )

    sender_transfer_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "alice@example.com").all()
    assert any("Fund Transfer Sent" in l.subject for l in sender_transfer_logs)

    receiver_transfer_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "bob@example.com").all()
    assert any("Fund Transfer Received" in l.subject for l in receiver_transfer_logs)

    # 6. Closure request triggers closure received email
    # Empty balance first
    client.post("/api/transactions/withdraw", json={"accountId": acc1_id, "amount": "500.00"}, headers=h1)
    req_res = client.post(
        "/api/account-requests/closure",
        json={"accountId": acc1_id, "reason": "Closing test account", "confirmationCheckbox": True},
        headers=h1,
    )
    closure_logs = db_session.query(EmailLog).filter(EmailLog.recipient_email == "alice@example.com").all()
    assert any("Your account closure request has been received" in l.subject for l in closure_logs)
