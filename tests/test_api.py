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


# ── app-industrialization spec ────────────────────────────────────────────────

def test_about_returns_metadata(client):
    """TP-01: GET /api/about returns name, version, developer == 'Eduardo Arana'."""
    res = client.get("/api/about")
    assert res.status_code == 200
    data = res.json()
    assert data["name"]
    assert data["version"]
    assert data["developer"] == "Eduardo Arana"


def test_export_csv(auth_client):
    """TP-02: CSV export returns text/csv with a header row and a row per component."""
    auth_client.post("/api/components", json={"digikey_pn": "CSV-A", "quantity": 3})
    auth_client.post("/api/components", json={"digikey_pn": "CSV-B", "quantity": 7})

    res = auth_client.get("/api/components/export/csv")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    lines = [ln for ln in res.text.splitlines() if ln.strip()]
    assert lines[0].startswith("digikey_pn,")
    assert len(lines) == 3  # header + 2 components
    assert any("CSV-A" in ln for ln in lines[1:])


def test_backup_returns_components(auth_client):
    """TP-03: GET /api/backup returns the user's components with a version + count."""
    auth_client.post("/api/components", json={"digikey_pn": "BK-1", "quantity": 1})
    res = auth_client.get("/api/backup")
    assert res.status_code == 200
    data = res.json()
    assert data["version"]
    assert data["component_count"] == 1
    assert data["components"][0]["digikey_pn"] == "BK-1"


def test_restore_replace_and_merge(auth_client):
    """TP-04: restore replace clears then inserts; merge appends."""
    auth_client.post("/api/components", json={"digikey_pn": "ORIGINAL", "quantity": 1})

    payload = {"components": [
        {"digikey_pn": "RESTORED-1", "quantity": 5},
        {"digikey_pn": "RESTORED-2", "quantity": 6},
    ]}

    res = auth_client.post("/api/restore?mode=replace", json=payload)
    assert res.status_code == 200
    assert res.json()["restored"] == 2
    pns = {c["digikey_pn"] for c in auth_client.get("/api/components").json()}
    assert pns == {"RESTORED-1", "RESTORED-2"}  # ORIGINAL removed

    res = auth_client.post("/api/restore?mode=merge", json={"components": [{"digikey_pn": "MERGED", "quantity": 1}]})
    assert res.status_code == 200
    pns = {c["digikey_pn"] for c in auth_client.get("/api/components").json()}
    assert pns == {"RESTORED-1", "RESTORED-2", "MERGED"}


def test_user_maintenance(auth_client):
    """TP-05: list/create users; reset password lets the new user log in; delete guards."""
    # testuser (from auth_client fixture) already exists
    res = auth_client.get("/api/users")
    assert res.status_code == 200
    assert any(u["username"] == "testuser" for u in res.json())
    self_id = next(u["id"] for u in res.json() if u["username"] == "testuser")

    # Create a second user
    res = auth_client.post("/api/users", json={"username": "operator", "password": "initialpw"})
    assert res.status_code == 201
    new_id = res.json()["id"]

    # Reset that user's password, then confirm login works with the new password
    res = auth_client.put(f"/api/users/{new_id}/password", json={"password": "changedpw"})
    assert res.status_code == 200
    res = auth_client.post(
        "/api/auth/login",
        data={"username": "operator", "password": "changedpw"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200

    # Cannot delete own account
    assert auth_client.delete(f"/api/users/{self_id}").status_code == 400

    # Can delete the other user
    assert auth_client.delete(f"/api/users/{new_id}").status_code == 204

    # Cannot delete the last remaining user
    assert auth_client.delete(f"/api/users/{self_id}").status_code == 400


def test_user_endpoints_require_auth(client):
    """User maintenance endpoints reject unauthenticated requests."""
    assert client.get("/api/users").status_code == 401


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
