from unittest.mock import patch
from app.models.user import User
from app.models.audit_log import AuditLog
from app.scripts.reactivate_admin import reactivate_admin
from app.scripts.create_admin import prompt_admin_creation


def test_admin_access_control(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # Customer tries to access admin dashboard -> 403
    c_res = client.get("/api/admin/dashboard", headers=cust_h)
    assert c_res.status_code == 403
    assert c_res.json()["message"] == "Insufficient permissions."

    # Customer tries to access admin management -> 403
    c_admins_res = client.get("/api/admin/administrators", headers=cust_h)
    assert c_admins_res.status_code == 403
    assert c_admins_res.json()["message"] == "Insufficient permissions."

    # Admin accesses dashboard -> 200
    a_res = client.get("/api/admin/dashboard", headers=admin_h)
    assert a_res.status_code == 200
    stats = a_res.json()
    assert "totalCustomers" in stats
    assert "totalAccounts" in stats


def test_admin_login_active_and_deactivated(client, test_admin, db_session):
    # 1. Admin can log in when ACTIVE
    login_active = client.post("/api/auth/login", json={"email": test_admin.email, "password": "TestAdmin#2026!"})
    assert login_active.status_code == 200
    assert login_active.json()["status"] == "ACTIVE"
    token = login_active.json()["token"]

    # 2. Set status to DEACTIVATED directly
    test_admin.status = "DEACTIVATED"
    db_session.commit()

    # Deactivated admin cannot log in
    login_deact = client.post("/api/auth/login", json={"email": test_admin.email, "password": "TestAdmin#2026!"})
    assert login_deact.status_code == 403
    assert login_deact.json()["message"] == "Account has been deactivated."

    # Deactivated admin's existing token is rejected on authenticated endpoints
    me_res = client.get("/api/users/profile", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 403
    assert me_res.json()["message"] == "Account has been deactivated."


def test_admin_cannot_deactivate_self(client, test_admin, test_admin2, test_admin_token):
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # When multiple active admins exist, self-deactivation returns "You cannot deactivate your own administrator account."
    # Attempt self-deactivation via customers endpoint
    self_res1 = client.put(
        f"/api/admin/customers/{test_admin.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin_h,
    )
    assert self_res1.status_code == 400
    assert self_res1.json()["message"] == "You cannot deactivate your own administrator account."

    # Attempt self-deactivation via administrators endpoint
    self_res2 = client.put(
        f"/api/admin/administrators/{test_admin.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin_h,
    )
    assert self_res2.status_code == 400
    assert self_res2.json()["message"] == "You cannot deactivate your own administrator account."

    # Verify ADMIN_SELF_DEACTIVATION_BLOCKED audit log was recorded
    audit_res = client.get("/api/admin/audit-logs?action=ADMIN_SELF_DEACTIVATION_BLOCKED", headers=admin_h)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 1


def test_last_active_admin_protection(client, test_admin, test_admin2, test_admin_token):
    admin1_h = {"Authorization": f"Bearer {test_admin_token}"}

    # Both test_admin and test_admin2 are ACTIVE (active_admins = 2)
    # Admin 1 deactivates Admin 2 -> SUCCESS
    deact_res = client.put(
        f"/api/admin/administrators/{test_admin2.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin1_h,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["status"] == "DEACTIVATED"

    # Now only 1 active admin remains (test_admin).
    # Attempting to deactivate the last active admin must be strictly rejected with the lockout error:
    res_last = client.put(
        f"/api/admin/administrators/{test_admin.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin1_h,
    )
    assert res_last.status_code == 400
    assert res_last.json()["message"] == "Cannot deactivate the last active administrator. Create or activate another administrator first."

    # Same check via customers endpoint
    res_last_cust = client.put(
        f"/api/admin/customers/{test_admin.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin1_h,
    )
    assert res_last_cust.status_code == 400
    assert res_last_cust.json()["message"] == "Cannot deactivate the last active administrator. Create or activate another administrator first."


def test_admin_management_lifecycle_and_audit(client, test_admin, test_admin2, test_admin_token):
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # List administrators
    list_res = client.get("/api/admin/administrators", headers=admin_h)
    assert list_res.status_code == 200
    admin_ids = [a["userId"] for a in list_res.json()]
    assert test_admin.id in admin_ids
    assert test_admin2.id in admin_ids

    # 1. Admin 1 deactivates Admin 2
    deact_res = client.put(
        f"/api/admin/administrators/{test_admin2.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin_h,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["status"] == "DEACTIVATED"

    # Verify audit log for ADMIN_DEACTIVATED
    audit_deact = client.get("/api/admin/audit-logs?action=ADMIN_DEACTIVATED", headers=admin_h)
    assert audit_deact.status_code == 200
    assert any(str(test_admin2.id) == log["entityId"] for log in audit_deact.json())

    # 2. Deactivating an already deactivated admin returns proper message
    repeat_deact = client.put(
        f"/api/admin/administrators/{test_admin2.id}/status",
        json={"status": "DEACTIVATED"},
        headers=admin_h,
    )
    assert repeat_deact.status_code == 400
    assert repeat_deact.json()["message"] == "Administrator is already deactivated."

    # 3. Admin 1 reactivates Admin 2
    react_res = client.put(
        f"/api/admin/administrators/{test_admin2.id}/status",
        json={"status": "ACTIVE"},
        headers=admin_h,
    )
    assert react_res.status_code == 200
    assert react_res.json()["status"] == "ACTIVE"

    # Verify audit log for ADMIN_ACTIVATED
    audit_react = client.get("/api/admin/audit-logs?action=ADMIN_ACTIVATED", headers=admin_h)
    assert audit_react.status_code == 200
    assert any(str(test_admin2.id) == log["entityId"] for log in audit_react.json())

    # 4. Activating an already active admin returns proper message
    repeat_act = client.put(
        f"/api/admin/administrators/{test_admin2.id}/status",
        json={"status": "ACTIVE"},
        headers=admin_h,
    )
    assert repeat_act.status_code == 400
    assert repeat_act.json()["message"] == "Administrator is already active."


def test_registration_role_protection(client):
    # Attempting to register with role=ADMIN must be rejected
    res = client.post("/api/auth/register", json={
        "fullName": "Fake Admin",
        "email": "fake.admin@example.com",
        "phoneNumber": "9123456789",
        "password": "Password123",
        "role": "ADMIN",
    })
    assert res.status_code == 400
    assert "Registration with ADMIN role is not permitted" in str(res.json())

    # Normal registration succeeds and always creates role=CUSTOMER
    res_normal = client.post("/api/auth/register", json={
        "fullName": "Real Customer",
        "email": "real.customer@example.com",
        "phoneNumber": "9123456788",
        "password": "Password123",
    })
    assert res_normal.status_code == 201

    login = client.post("/api/auth/login", json={"email": "real.customer@example.com", "password": "Password123"})
    assert login.status_code == 200
    assert login.json()["role"] == "CUSTOMER"


def test_admin_customer_management(client, test_customer, test_admin_token):
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    # List customers
    list_res = client.get("/api/admin/customers", headers=admin_h)
    assert list_res.status_code == 200
    assert any(c["email"] == test_customer.email for c in list_res.json())

    # Get customer details
    detail_res = client.get(f"/api/admin/customers/{test_customer.id}", headers=admin_h)
    assert detail_res.status_code == 200
    assert detail_res.json()["customer"]["email"] == test_customer.email

    # Suspend customer
    sus_res = client.put(
        f"/api/admin/customers/{test_customer.id}/status",
        json={"status": "SUSPENDED"},
        headers=admin_h,
    )
    assert sus_res.status_code == 200
    assert sus_res.json()["status"] == "SUSPENDED"

    # Suspended customer cannot login
    login_res = client.post("/api/auth/login", json={"email": test_customer.email, "password": "Password123"})
    assert login_res.status_code == 403

    # Reactivate customer
    react_res = client.put(
        f"/api/admin/customers/{test_customer.id}/status",
        json={"status": "ACTIVE"},
        headers=admin_h,
    )
    assert react_res.status_code == 200
    assert react_res.json()["status"] == "ACTIVE"


def test_admin_account_management_and_audit_logs(client, test_customer_token, test_admin_token):
    cust_h = {"Authorization": f"Bearer {test_customer_token}"}
    admin_h = {"Authorization": f"Bearer {test_admin_token}"}

    acc_res = client.post("/api/accounts", json={"accountType": "SAVINGS"}, headers=cust_h)
    acc_id = acc_res.json()["accountId"]

    # Admin suspends account
    sus_res = client.put(f"/api/admin/accounts/{acc_id}/status", json={"status": "SUSPENDED"}, headers=admin_h)
    assert sus_res.status_code == 200
    assert sus_res.json()["status"] == "SUSPENDED"

    # Customer tries to deposit to suspended account -> fails
    dep_res = client.post(
        "/api/transactions/deposit",
        json={"accountId": acc_id, "amount": "100.00"},
        headers=cust_h,
    )
    assert dep_res.status_code == 400

    # Admin views audit logs
    audit_res = client.get("/api/admin/audit-logs", headers=admin_h)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) > 0


def test_reactivate_admin_cli_script(db_session, test_admin, test_customer):
    # 1. Nonexistent email fails
    assert not reactivate_admin("nobody@nowhere.com", db=db_session)

    # 2. Non-admin fails
    assert not reactivate_admin(test_customer.email, db=db_session)

    # 3. Already active admin returns True
    assert reactivate_admin(test_admin.email, db=db_session)

    # 4. Deactivated admin is successfully restored
    test_admin.status = "DEACTIVATED"
    db_session.commit()
    assert test_admin.status == "DEACTIVATED"

    success = reactivate_admin(test_admin.email, db=db_session)
    assert success is True
    db_session.refresh(test_admin)
    assert test_admin.status == "ACTIVE"
    assert test_admin.role == "ADMIN"

    # Verify audit log entry was written
    log = db_session.query(AuditLog).filter_by(
        action="ADMIN_ACTIVATED",
        entity_id=str(test_admin.id),
    ).order_by(AuditLog.id.desc()).first()
    assert log is not None
    assert "CLI recovery script" in log.description


def test_interactive_create_admin_script(client, db_session):
    # 1. Test validation failure on empty username
    with patch("builtins.input", side_effect=[""]):
        assert prompt_admin_creation(db=db_session) is False

    # 2. Test validation failure on invalid email
    with patch("builtins.input", side_effect=["ValidUser", "invalid-email-format"]):
        assert prompt_admin_creation(db=db_session) is False

    # 3. Test validation failure on mismatched passwords
    with patch("builtins.input", side_effect=["MySuperAdmin", "mysuperadmin@custombank.com"]):
        with patch("getpass.getpass", side_effect=["SecurePassword1!", "DifferentPassword2@"]):
            assert prompt_admin_creation(db=db_session) is False

    # 4. Test successful interactive admin creation
    with patch("builtins.input", side_effect=["CustomAdminName", "customadmin@custombank.com"]):
        with patch("getpass.getpass", side_effect=["SuperSecretAdmin99#", "SuperSecretAdmin99#"]):
            success = prompt_admin_creation(db=db_session)
            assert success is True

    # 5. Verify user created in database has role ADMIN and status ACTIVE
    user = db_session.query(User).filter_by(email="customadmin@custombank.com").first()
    assert user is not None
    assert user.full_name == "CustomAdminName"
    assert user.role == "ADMIN"
    assert user.status == "ACTIVE"

    # 6. Verify password was securely hashed (not plaintext)
    assert user.password_hash != "SuperSecretAdmin99#"
    assert len(user.password_hash) > 20

    # 7. Verify admin can log in via existing login endpoint and receives ADMIN role
    login_res = client.post("/api/auth/login", json={
        "email": "customadmin@custombank.com",
        "password": "SuperSecretAdmin99#",
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["role"] == "ADMIN"
    assert login_data["email"] == "customadmin@custombank.com"
    token = login_data["token"]

    # 8. Verify the new admin can access the Admin Dashboard
    dash_res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert dash_res.status_code == 200
    assert "totalCustomers" in dash_res.json()
