
import os
import sys
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from auth import get_password_hash  # noqa: E402
from models import ScanShare  # noqa: E402

TEST_DB_URL = "sqlite:///./test_vulntracker.db"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(
    username="alice",
    email="alice@example.com",
    password="password123",
):
    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_scan(token, title, severity="high", component="test-service"):
    return client.post(
        "/scans",
        json={
            "title": title,
            "severity": severity,
            "affected_component": component,
        },
        headers=auth_headers(token),
    )


def create_share(token, scan_id, password=None):
    payload = {}
    if password is not None:
        payload["password"] = password

    return client.post(
        f"/scans/{scan_id}/share",
        json=payload,
        headers=auth_headers(token),
    )


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_user():
    resp = client.post(
        "/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "secret",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "bob"


def test_register_duplicate_username():
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret",
    }
    client.post("/auth/register", json=payload)
    resp = client.post(
        "/auth/register",
        json={**payload, "email": "bob2@example.com"},
    )
    assert resp.status_code == 400


def test_login_success():
    client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "pw",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"username": "alice", "password": "pw"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "pw",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_create_scan():
    token = register_and_login()
    resp = client.post(
        "/scans",
        json={
            "title": "Reflected XSS in search",
            "description": "User input is echoed without sanitisation",
            "severity": "high",
            "affected_component": "GET /search",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Reflected XSS in search"


def test_list_scans():
    token = register_and_login()
    create_scan(token, "Test finding", severity="low", component="misc")
    resp = client.get("/scans", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_scans():
    token = register_and_login()
    create_scan(
        token,
        "SQL Injection via login",
        severity="critical",
        component="POST /auth/login",
    )

    resp = client.get(
        "/scans/search?q=SQL",
        headers=auth_headers(token),
    )

    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    assert resp.json()["results"][0]["title"] == "SQL Injection via login"


def test_update_scan_status():
    token = register_and_login()
    scan_id = create_scan(
        token,
        "Open redirect",
        severity="medium",
        component="redirect handler",
    ).json()["id"]

    resp = client.patch(
        f"/scans/{scan_id}",
        json={"status": "in_progress"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_delete_scan():
    token = register_and_login()
    scan_id = create_scan(
        token,
        "Stale finding",
        severity="low",
        component="misc",
    ).json()["id"]

    resp = client.delete(
        f"/scans/{scan_id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Security regression tests
# ---------------------------------------------------------------------------

def test_user_cannot_read_another_users_scan():
    alice_token = register_and_login(
        username="alice",
        email="alice@example.com",
    )
    bob_token = register_and_login(
        username="bob",
        email="bob@example.com",
    )

    created = create_scan(
        alice_token,
        "Alice private finding",
        component="private-service",
    )
    assert created.status_code == 201

    scan_id = created.json()["id"]
    response = client.get(
        f"/scans/{scan_id}",
        headers=auth_headers(bob_token),
    )

    assert response.status_code == 404


def test_search_does_not_return_another_users_scans():
    alice_token = register_and_login(
        username="alice",
        email="alice@example.com",
    )
    bob_token = register_and_login(
        username="bob",
        email="bob@example.com",
    )

    created = create_scan(
        alice_token,
        "Private SQL finding",
        component="alice-private-service",
    )
    assert created.status_code == 201

    response = client.get(
        "/scans/search?q=SQL",
        headers=auth_headers(bob_token),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


# ---------------------------------------------------------------------------
# Shared report tests
# ---------------------------------------------------------------------------

def test_create_and_access_public_share_link():
    token = register_and_login()
    scan_response = create_scan(token, "Public share test")
    assert scan_response.status_code == 201
    scan_id = scan_response.json()["id"]

    share_response = create_share(token, scan_id)
    assert share_response.status_code == 201

    share_data = share_response.json()
    assert share_data["password_protected"] is False
    assert share_data["token"]
    assert share_data["share_url"].endswith(
        f"/share/{share_data['token']}"
    )

    public_response = client.get(f"/share/{share_data['token']}")
    assert public_response.status_code == 200
    assert public_response.json()["scan"]["id"] == scan_id
    assert public_response.json()["scan"]["title"] == "Public share test"


def test_password_protected_share_link():
    token = register_and_login()
    scan_response = create_scan(token, "Protected share test")
    scan_id = scan_response.json()["id"]

    share_response = create_share(token, scan_id, password="SharePass123!")
    assert share_response.status_code == 201

    share_data = share_response.json()
    assert share_data["password_protected"] is True
    share_token = share_data["token"]

    missing_password = client.get(f"/share/{share_token}")
    assert missing_password.status_code == 401

    wrong_password = client.get(
        f"/share/{share_token}",
        params={"password": "WrongPass123!"},
    )
    assert wrong_password.status_code == 401

    correct_password = client.get(
        f"/share/{share_token}",
        params={"password": "SharePass123!"},
    )
    assert correct_password.status_code == 200
    assert correct_password.json()["scan"]["id"] == scan_id


def test_user_cannot_share_another_users_scan():
    alice_token = register_and_login(
        username="alice",
        email="alice@example.com",
    )
    bob_token = register_and_login(
        username="bob",
        email="bob@example.com",
    )

    scan_response = create_scan(alice_token, "Alice private scan")
    assert scan_response.status_code == 201
    scan_id = scan_response.json()["id"]

    share_response = create_share(bob_token, scan_id)
    assert share_response.status_code == 404


def test_expired_share_link_is_rejected():
    token = register_and_login()
    scan_response = create_scan(token, "Expired share test")
    scan_id = scan_response.json()["id"]

    share_response = create_share(token, scan_id)
    assert share_response.status_code == 201
    share_token = share_response.json()["token"]

    db = TestingSessionLocal()
    try:
        share = (
            db.query(ScanShare)
            .filter(ScanShare.token == share_token)
            .first()
        )
        assert share is not None
        share.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    response = client.get(f"/share/{share_token}")
    assert response.status_code == 410


def test_invalid_share_token_is_rejected():
    response = client.get("/share/this-token-does-not-exist")
    assert response.status_code == 404
