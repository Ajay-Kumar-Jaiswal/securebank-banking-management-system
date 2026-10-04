def test_beneficiary_lifecycle(client, test_customer_token, test_customer2_token):
    h1 = {"Authorization": f"Bearer {test_customer_token}"}
    h2 = {"Authorization": f"Bearer {test_customer2_token}"}

    # Customer 2 creates an account
    acc2_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=h2)
    acc2_num = acc2_res.json()["accountNumber"]

    # 1. Add invalid beneficiary fails
    res_invalid = client.post(
        "/api/beneficiaries",
        json={"name": "Ghost", "accountNumber": "AC9999999999", "bankName": "SecureBank", "ifscCode": "SEC0001"},
        headers=h1,
    )
    assert res_invalid.status_code == 404

    # 2. Add valid beneficiary succeeds
    res_add = client.post(
        "/api/beneficiaries",
        json={"name": "Bob Payee", "accountNumber": acc2_num, "bankName": "SecureBank", "ifscCode": "SEC0001"},
        headers=h1,
    )
    assert res_add.status_code == 201
    b_id = res_add.json()["beneficiaryId"]

    # 3. List beneficiaries
    list_res = client.get("/api/beneficiaries", headers=h1)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 4. Update beneficiary
    up_res = client.put(
        f"/api/beneficiaries/{b_id}",
        json={"name": "Bob Robert Jones", "accountNumber": acc2_num, "bankName": "SecureBank", "ifscCode": "SEC0002"},
        headers=h1,
    )
    assert up_res.status_code == 200
    assert up_res.json()["name"] == "Bob Robert Jones"

    # 5. Delete beneficiary
    del_res = client.delete(f"/api/beneficiaries/{b_id}", headers=h1)
    assert del_res.status_code == 204

    # 6. Verify empty list
    list_res2 = client.get("/api/beneficiaries", headers=h1)
    assert len(list_res2.json()) == 0
