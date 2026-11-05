"""
Tests for document endpoints (upload, list, get, delete).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_examforge_docs.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables immediately
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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _register_and_login(email: str = "doctest@example.com") -> dict:
    """Register a user and return auth header dict."""
    client.post(
        "/api/auth/register",
        json={"email": email, "name": "Doc User", "password": "docpassword"},
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": email, "password": "docpassword"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_documents_empty():
    headers = _register_and_login()
    response = client.get("/api/documents/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_upload_non_pdf_rejected():
    headers = _register_and_login()
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"plain text", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 400


def test_get_nonexistent_document():
    headers = _register_and_login()
    response = client.get("/api/documents/9999", headers=headers)
    assert response.status_code == 404


def test_documents_require_auth():
    """Document list must reject unauthenticated requests."""
    response = client.get("/api/documents/")
    assert response.status_code in (401, 403)



