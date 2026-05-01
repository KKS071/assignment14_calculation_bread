# File: tests/integration/test_api_calculations.py
# Purpose: Integration tests for all BREAD calculation endpoints (positive + negative).
import pytest


# ── Helper ────────────────────────────────────────────────────────────────────

def create_calc(client, auth_headers, type_="addition", inputs=None):
    inputs = inputs or [10, 5]
    resp = client.post("/calculations", json={"type": type_, "inputs": inputs}, headers=auth_headers)
    return resp


# ── Add (POST /calculations) ──────────────────────────────────────────────────

def test_create_addition(client, auth_headers):
    resp = create_calc(client, auth_headers, "addition", [3, 4])
    assert resp.status_code == 201
    data = resp.json()
    assert data["result"] == 7.0
    assert data["type"] == "addition"


def test_create_subtraction(client, auth_headers):
    resp = create_calc(client, auth_headers, "subtraction", [10, 3])
    assert resp.status_code == 201
    assert resp.json()["result"] == 7.0


def test_create_multiplication(client, auth_headers):
    resp = create_calc(client, auth_headers, "multiplication", [4, 5])
    assert resp.status_code == 201
    assert resp.json()["result"] == 20.0


def test_create_division(client, auth_headers):
    resp = create_calc(client, auth_headers, "division", [20, 4])
    assert resp.status_code == 201
    assert resp.json()["result"] == 5.0


def test_create_invalid_type(client, auth_headers):
    resp = client.post("/calculations", json={"type": "modulus", "inputs": [5, 2]}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_division_by_zero(client, auth_headers):
    resp = client.post("/calculations", json={"type": "division", "inputs": [10, 0]}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_one_input(client, auth_headers):
    resp = client.post("/calculations", json={"type": "addition", "inputs": [5]}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_no_auth():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app, raise_server_exceptions=False)
    resp = c.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
    assert resp.status_code == 401


# ── Browse (GET /calculations) ────────────────────────────────────────────────

def test_list_calculations_empty(client, auth_headers):
    resp = client.get("/calculations", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_calculations_returns_own_only(client, auth_headers, db_session):
    create_calc(client, auth_headers, "addition", [1, 2])
    create_calc(client, auth_headers, "subtraction", [10, 3])
    resp = client.get("/calculations", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_list_no_auth():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app, raise_server_exceptions=False)
    assert c.get("/calculations").status_code == 401


# ── Read (GET /calculations/{id}) ────────────────────────────────────────────

def test_read_calculation(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [6, 7]).json()
    resp = client.get(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_read_not_found(client, auth_headers):
    import uuid
    resp = client.get(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_read_invalid_id(client, auth_headers):
    resp = client.get("/calculations/not-a-uuid", headers=auth_headers)
    assert resp.status_code == 400


def test_read_other_users_calc(client, auth_headers, db_session):
    """Another user's calculation should return 404 for the current user."""
    from app.models.user import User
    from app.models.calculation import Calculation, Addition
    import uuid

    # Create a second user and their calculation directly in DB
    other_user = User(
        first_name="Other", last_name="User",
        email=f"other_{uuid.uuid4().hex[:6]}@test.com",
        username=f"other_{uuid.uuid4().hex[:6]}",
        password=User.hash_password("OtherPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other_user)
    db_session.flush()

    other_calc = Addition(user_id=other_user.id, inputs=[1, 2])
    other_calc.result = other_calc.get_result()
    db_session.add(other_calc)
    db_session.commit()

    resp = client.get(f"/calculations/{other_calc.id}", headers=auth_headers)
    assert resp.status_code == 404


# ── Edit (PUT /calculations/{id}) ────────────────────────────────────────────

def test_update_calculation_inputs(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [1, 2]).json()
    resp = client.put(
        f"/calculations/{created['id']}",
        json={"inputs": [10, 20]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 30.0


def test_update_calculation_type_and_inputs(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [10, 5]).json()
    resp = client.put(
        f"/calculations/{created['id']}",
        json={"type": "multiplication", "inputs": [3, 4]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 12.0


def test_update_not_found(client, auth_headers):
    import uuid
    resp = client.put(f"/calculations/{uuid.uuid4()}", json={"inputs": [1, 2]}, headers=auth_headers)
    assert resp.status_code == 404


def test_update_invalid_id(client, auth_headers):
    resp = client.put("/calculations/bad-id", json={"inputs": [1, 2]}, headers=auth_headers)
    assert resp.status_code == 400


def test_update_division_by_zero(client, auth_headers):
    created = create_calc(client, auth_headers, "division", [10, 2]).json()
    resp = client.put(
        f"/calculations/{created['id']}",
        json={"inputs": [10, 0]},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── Delete (DELETE /calculations/{id}) ───────────────────────────────────────

def test_delete_calculation(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [5, 5]).json()
    resp = client.delete(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    # Verify it's gone
    assert client.get(f"/calculations/{created['id']}", headers=auth_headers).status_code == 404


def test_delete_not_found(client, auth_headers):
    import uuid
    resp = client.delete(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_invalid_id(client, auth_headers):
    resp = client.delete("/calculations/bad-id", headers=auth_headers)
    assert resp.status_code == 400


def test_delete_other_users_calc(client, auth_headers, db_session):
    """Deleting another user's calc should return 404."""
    from app.models.user import User
    from app.models.calculation import Addition
    import uuid

    other_user = User(
        first_name="Del", last_name="Test",
        email=f"del_{uuid.uuid4().hex[:6]}@test.com",
        username=f"del_{uuid.uuid4().hex[:6]}",
        password=User.hash_password("DelPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other_user)
    db_session.flush()

    other_calc = Addition(user_id=other_user.id, inputs=[5, 5])
    other_calc.result = 10.0
    db_session.add(other_calc)
    db_session.commit()

    resp = client.delete(f"/calculations/{other_calc.id}", headers=auth_headers)
    assert resp.status_code == 404