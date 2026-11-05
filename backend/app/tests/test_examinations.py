"""
Tests for examination endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_examforge_exams.db"
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


def _auth_header():
    client.post(
        "/api/auth/register",
        json={"email": "examuser@example.com", "name": "Exam User", "password": "exampassword"},
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": "examuser@example.com", "password": "exampassword"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_list_examinations_empty():
    headers = _auth_header()
    response = client.get("/api/examinations/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_examination_invalid_document():
    headers = _auth_header()
    response = client.post(
        "/api/examinations/",
        json={"document_id": 9999, "max_questions": 10},
        headers=headers,
    )
    assert response.status_code == 404


def test_get_nonexistent_examination():
    headers = _auth_header()
    response = client.get("/api/examinations/9999", headers=headers)
    assert response.status_code == 404


def test_examinations_require_auth():
    """Examination list must reject unauthenticated requests."""
    response = client.get("/api/examinations/")
    assert response.status_code == 403
