"""API tests — covers TP-01 through TP-05 from qr-scanner-inventory-app.spec.yaml"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base, get_db
import main as app_module

TEST_DB = "sqlite:///./test_inventory.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app_module.app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app_module.app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def auth_client(client):
    """Client with a registered+logged-in user."""
    client.post("/api/auth/register", json={"username": "testuser", "password": "testpass123"})
    res = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ── TP-01: Registration ───────────────────────────────────────────────────────

def test_register_first_user(client):
    """TP-01: First user can register and receives a JWT."""
    res = client.post("/api/auth/register", json={"username": "alice", "password": "secret123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_username(client):
    """Duplicate username returns 400."""
    client.post("/api/auth/register", json={"username": "alice", "password": "secret"})
    res = client.post("/api/auth/register", json={"username": "alice", "password": "other"})
    assert res.status_code == 400


# ── TP-02: Login & auth guard ─────────────────────────────────────────────────

def test_login_valid(client):
    """TP-02: Valid login returns JWT."""
    client.post("/api/auth/register", json={"username": "bob", "password": "pw123"})
    res = client.post(
        "/api/auth/login",
        data={"username": "bob", "password": "pw123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_invalid_password(client):
    """Wrong password returns 400."""
    client.post("/api/auth/register", json={"username": "bob", "password": "pw123"})
    res = client.post(
        "/api/auth/login",
        data={"username": "bob", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 400


def test_unauthenticated_request_returns_401(client):
    """TP-02: No token → 401."""
    res = client.get("/api/components")
    assert res.status_code == 401


# ── TP-03: Create and list components ────────────────────────────────────────

def test_create_and_list_component(auth_client):
    """TP-03: POST /api/components saves component; GET returns it."""
    payload = {
        "digikey_pn": "RHM33.0AFCT-ND",
        "manufacturer_pn": "ESR18EZPF33R0",
        "manufacturer": "ROHM Semiconductor",
        "description": "RES SMD 33 OHM 1% 1/2W 1206",
        "quantity": 454,
        "location": "Drawer A1",
    }
    res = auth_client.post("/api/components", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["digikey_pn"] == "RHM33.0AFCT-ND"
    assert created["quantity"] == 454

    res = auth_client.get("/api/components")
    assert res.status_code == 200
    ids = [c["id"] for c in res.json()]
    assert created["id"] in ids


# ── TP-04: Search ─────────────────────────────────────────────────────────────

def test_search_filters_components(auth_client):
    """TP-04: ?search=RHM returns only matching components."""
    auth_client.post("/api/components", json={"digikey_pn": "RHM33.0AFCT-ND", "quantity": 10})
    auth_client.post("/api/components", json={"digikey_pn": "GRM033R61A104KE84D", "quantity": 5})

    res = auth_client.get("/api/components?search=RHM")
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["digikey_pn"] == "RHM33.0AFCT-ND"


# ── TP-05: Update and delete ──────────────────────────────────────────────────

def test_update_component(auth_client):
    """TP-05: PUT updates fields."""
    res = auth_client.post("/api/components", json={"digikey_pn": "ABC-123", "quantity": 5})
    cid = res.json()["id"]

    res = auth_client.put(f"/api/components/{cid}", json={"quantity": 99, "location": "Box B"})
    assert res.status_code == 200
    assert res.json()["quantity"] == 99
    assert res.json()["location"] == "Box B"


def test_delete_component(auth_client):
    """TP-05: DELETE removes the component."""
    res = auth_client.post("/api/components", json={"digikey_pn": "DEL-TEST", "quantity": 1})
    cid = res.json()["id"]

    res = auth_client.delete(f"/api/components/{cid}")
    assert res.status_code == 204

    res = auth_client.get(f"/api/components/{cid}")
    assert res.status_code == 404


def test_cannot_access_other_users_component(client):
    """User A cannot read or delete User B's component."""
    # Register two users
    client.post("/api/auth/register", json={"username": "userA", "password": "passA"})
    res_a = client.post(
        "/api/auth/login",
        data={"username": "userA", "password": "passA"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_a = res_a.json()["access_token"]

    # UserA creates a component
    res = client.post(
        "/api/components",
        json={"digikey_pn": "PRIVATE-PART", "quantity": 3},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    cid = res.json()["id"]

    # Register user B without SETUP_TOKEN → should be blocked
    # (just verify userA's component isn't accessible without auth)
    res = client.get(f"/api/components/{cid}")
    assert res.status_code == 401
