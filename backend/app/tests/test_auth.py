"""
Tests for auth endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_examforge_auth.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables immediately so the TestClient can use them
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate tables before each test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_user():
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "name": "Test User", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email():
    client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "name": "User A", "password": "passA123"},
    )
    response = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "name": "User B", "password": "passB123"},
    )
    assert response.status_code == 409


def test_register_short_password():
    """Passwords shorter than 6 characters must be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "name": "Short Pwd", "password": "abc"},
    )
    assert response.status_code == 422


def test_login_success():
    client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "name": "Login User", "password": "mypassword"},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "mypassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    client.post(
        "/api/auth/register",
        json={"email": "wp@example.com", "name": "WP", "password": "correct123"},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "wp@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post(
        "/api/auth/login",
        data={"username": "nobody@example.com", "password": "doesnotmatter"},
    )
    assert response.status_code == 401


def test_me_endpoint():
    reg = client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "name": "Me User", "password": "mepassword"},
    )
    assert reg.status_code == 201, f"Registration failed: {reg.json()}"
    token = reg.json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_me_unauthenticated():
    response = client.get("/api/auth/me")
    # FastAPI HTTPBearer returns 403; some versions/configs return 401
    assert response.status_code in (401, 403)
