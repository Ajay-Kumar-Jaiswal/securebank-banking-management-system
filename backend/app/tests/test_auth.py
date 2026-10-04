def test_registration_success(client):
    res = client.post(
        "/api/auth/register",
        json={
            "fullName": "Charlie Brown",
            "email": "charlie@example.com",
            "phoneNumber": "9123456789",
            "password": "Password123",
            "address": "789 Pine St",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "userId" in data
    assert data["email"] == "charlie@example.com"


def test_registration_duplicate_email(client, test_customer):
    res = client.post(
        "/api/auth/register",
        json={
            "fullName": "Imposter",
            "email": test_customer.email,
            "phoneNumber": "9998887776",
            "password": "Password123",
            "address": "Nowhere",
        },
    )
    assert res.status_code == 409
    assert res.json()["error"] == "DUPLICATE_EMAIL"


def test_login_success(client, test_customer):
    res = client.post(
        "/api/auth/login",
        json={"email": test_customer.email, "password": "Password123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["email"] == test_customer.email
    assert data["role"] == "CUSTOMER"


def test_login_invalid_password(client, test_customer):
    res = client.post(
        "/api/auth/login",
        json={"email": test_customer.email, "password": "WrongPassword"},
    )
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_user(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "Password123"},
    )
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_CREDENTIALS"


def test_profile_update_and_password_change(client, test_customer, test_customer_token):
    headers = {"Authorization": f"Bearer {test_customer_token}"}

    # Get profile
    res = client.get("/api/users/profile", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == test_customer.email

    # Update profile
    res = client.put(
        "/api/users/profile",
        json={"fullName": "Alice Smith Updated", "phoneNumber": "9998887777", "address": "New Address"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["fullName"] == "Alice Smith Updated"

    # Change password
    res = client.post(
        "/api/users/change-password",
        json={"currentPassword": "Password123", "newPassword": "NewPassword456"},
        headers=headers,
    )
    assert res.status_code == 200

    # Old password should now fail
    res = client.post("/api/auth/login", json={"email": test_customer.email, "password": "Password123"})
    assert res.status_code == 401

    # New password should succeed
    res = client.post("/api/auth/login", json={"email": test_customer.email, "password": "NewPassword456"})
    assert res.status_code == 200
