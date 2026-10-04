import pytest
from fastapi.testclient import TestClient
from app.schemas.validators import validate_phone_number, PHONE_VALIDATION_ERROR_MSG
from app.schemas.auth import RegisterRequest
from app.schemas.user import UpdateProfileRequest
from pydantic import ValidationError

VALID_PHONE_NUMBERS = [
    "9876543210",
    "9123456789",
    "8765432109",
    "7890123456",
    "6789012345",
]

INVALID_PHONE_NUMBERS = [
    "1234567890",      # Starts with 1
    "987654321",       # 9 digits (too short)
    "98765432101",     # 11 digits (too long)
    "98765abc10",      # Contains letters
    "98765-43210",     # Contains hyphens
    "+919876543210",   # Country code prefix
    "98765 43210",     # Contains spaces
    "abcdefghij",      # All letters
    "!@#$%^&*()",      # Special characters
    "",                # Empty string
    "   ",             # Whitespace
    "0987654321",      # Starts with 0
    "5987654321",      # Starts with 5
]


@pytest.mark.parametrize("phone", VALID_PHONE_NUMBERS)
def test_validate_phone_number_valid(phone):
    result = validate_phone_number(phone)
    assert result == phone.strip()


@pytest.mark.parametrize("phone", INVALID_PHONE_NUMBERS)
def test_validate_phone_number_invalid(phone):
    with pytest.raises(ValueError) as exc_info:
        validate_phone_number(phone)
    assert str(exc_info.value) == PHONE_VALIDATION_ERROR_MSG


@pytest.mark.parametrize("phone", VALID_PHONE_NUMBERS)
def test_register_request_schema_valid(phone):
    req = RegisterRequest(
        fullName="Valid User",
        email="valid.phone@example.com",
        phoneNumber=phone,
        password="Password123!"
    )
    assert req.phoneNumber == phone


@pytest.mark.parametrize("phone", INVALID_PHONE_NUMBERS)
def test_register_request_schema_invalid(phone):
    with pytest.raises(ValidationError):
        RegisterRequest(
            fullName="Invalid User",
            email="invalid.phone@example.com",
            phoneNumber=phone,
            password="Password123!"
        )


@pytest.mark.parametrize("phone", VALID_PHONE_NUMBERS)
def test_update_profile_schema_valid(phone):
    req = UpdateProfileRequest(phoneNumber=phone)
    assert req.phoneNumber == phone


@pytest.mark.parametrize("phone", INVALID_PHONE_NUMBERS)
def test_update_profile_schema_invalid(phone):
    with pytest.raises(ValidationError):
        UpdateProfileRequest(phoneNumber=phone)


def test_registration_with_valid_phone(client: TestClient):
    payload = {
        "fullName": "Phone Valid User",
        "email": "phone_valid@example.com",
        "phoneNumber": "9876543210",
        "password": "Password123!",
        "address": "123 Valid St"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "userId" in data
    assert data["email"] == "phone_valid@example.com"


@pytest.mark.parametrize("phone", [
    "1234567890",
    "987654321",
    "98765432101",
    "98765abc10",
    "98765-43210",
    "+919876543210",
    "98765 43210",
    "abcdefghij",
    "!@#$%^&*()",
])
def test_registration_with_invalid_phone_returns_422(client: TestClient, phone: str):
    payload = {
        "fullName": "Phone Invalid User",
        "email": f"phone_inv_{abs(hash(phone))}@example.com",
        "phoneNumber": phone,
        "password": "Password123!",
        "address": "123 Invalid St"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "VALIDATION_ERROR"
    details_str = " ".join(data.get("details", []))
    assert "phoneNumber" in details_str or "phone_number" in details_str
    assert "10 digits" in details_str


def test_profile_update_with_valid_phone(client: TestClient, test_customer_token: str):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    payload = {
        "fullName": "Updated Customer",
        "phoneNumber": "9123456789",
        "address": "Updated Address 456"
    }
    res = client.put("/api/users/profile", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["phoneNumber"] == "9123456789"


@pytest.mark.parametrize("phone", [
    "1234567890",
    "987654321",
    "98765432101",
    "98765abc10",
    "98765-43210",
    "+919876543210",
    "98765 43210",
    "abcdefghij",
    "!@#$%^&*()",
])
def test_profile_update_with_invalid_phone_returns_422(client: TestClient, test_customer_token: str, phone: str):
    headers = {"Authorization": f"Bearer {test_customer_token}"}
    payload = {
        "phoneNumber": phone
    }
    res = client.put("/api/users/profile", json=payload, headers=headers)
    assert res.status_code == 422
    data = res.json()
    assert data["error"] == "VALIDATION_ERROR"
    details_str = " ".join(data.get("details", []))
    assert "phoneNumber" in details_str or "phone_number" in details_str
