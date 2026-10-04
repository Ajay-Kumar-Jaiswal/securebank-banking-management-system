import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User
from app.models.account import Account

# Use an in-memory SQLite database with StaticPool so all sessions share the same in-memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables for every test and yield a session."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Override get_db with test database session."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_customer(db_session):
    user = User(
        full_name="Alice Smith",
        email="alice@example.com",
        phone_number="9876543210",
        password_hash=hash_password("Password123"),
        address="123 Bank St",
        role="CUSTOMER",
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_customer_token(client, test_customer):
    res = client.post("/api/auth/login", json={"email": test_customer.email, "password": "Password123"})
    return res.json()["token"]


@pytest.fixture
def test_customer2(db_session):
    user = User(
        full_name="Bob Jones",
        email="bob@example.com",
        phone_number="9876543211",
        password_hash=hash_password("Password123"),
        address="456 Market St",
        role="CUSTOMER",
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_customer2_token(client, test_customer2):
    res = client.post("/api/auth/login", json={"email": test_customer2.email, "password": "Password123"})
    return res.json()["token"]


@pytest.fixture
def test_admin(db_session):
    user = User(
        full_name="Admin Boss",
        email="testadmin@example.com",
        phone_number="9999999999",
        password_hash=hash_password("TestAdmin#2026!"),
        address="HQ",
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_token(client, test_admin):
    res = client.post("/api/auth/login", json={"email": test_admin.email, "password": "TestAdmin#2026!"})
    return res.json()["token"]


@pytest.fixture
def test_admin2(db_session):
    user = User(
        full_name="Admin Second",
        email="testadmin2@example.com",
        phone_number="8888888888",
        password_hash=hash_password("TestAdmin#2026!"),
        address="HQ Branch",
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin2_token(client, test_admin2):
    res = client.post("/api/auth/login", json={"email": test_admin2.email, "password": "TestAdmin#2026!"})
    return res.json()["token"]


