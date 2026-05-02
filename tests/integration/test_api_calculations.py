# File: tests/integration/test_api_calculations.py
# Purpose: Integration tests for all BREAD calculation endpoints — positive + negative scenarios,
#          including multi-value inputs (more than 2 numbers).
import uuid
import pytest


# ── Helper ────────────────────────────────────────────────────────────────────

def post_calc(client, headers, type_="addition", inputs=None):
    inputs = inputs or [10, 5]
    return client.post("/calculations", json={"type": type_, "inputs": inputs}, headers=headers)


# ── Add — POST /calculations ──────────────────────────────────────────────────

def test_add_addition_two_values(client, auth_headers):
    r = post_calc(client, auth_headers, "addition", [3, 4])
    assert r.status_code == 201
    assert r.json()["result"] == 7.0

def test_add_addition_three_values(client, auth_headers):
    r = post_calc(client, auth_headers, "addition", [1, 2, 3])
    assert r.status_code == 201
    assert r.json()["result"] == 6.0

def test_add_addition_five_values(client, auth_headers):
    r = post_calc(client, auth_headers, "addition", [10, 20, 30, 40, 50])
    assert r.status_code == 201
    assert r.json()["result"] == 150.0

def test_add_subtraction_multi(client, auth_headers):
    r = post_calc(client, auth_headers, "subtraction", [100, 30, 20])
    assert r.status_code == 201
    assert r.json()["result"] == 50.0

def test_add_multiplication_multi(client, auth_headers):
    r = post_calc(client, auth_headers, "multiplication", [2, 3, 4])
    assert r.status_code == 201
    assert r.json()["result"] == 24.0

def test_add_division_multi(client, auth_headers):
    r = post_calc(client, auth_headers, "division", [120, 2, 3, 4])
    assert r.status_code == 201
    assert r.json()["result"] == 5.0

def test_add_invalid_type(client, auth_headers):
    r = client.post("/calculations", json={"type": "modulus", "inputs": [5, 2]}, headers=auth_headers)
    assert r.status_code == 422

def test_add_division_by_zero(client, auth_headers):
    r = client.post("/calculations", json={"type": "division", "inputs": [10, 0]}, headers=auth_headers)
    assert r.status_code == 422

def test_add_division_by_zero_third_element(client, auth_headers):
    r = client.post("/calculations", json={"type": "division", "inputs": [10, 2, 0]}, headers=auth_headers)
    assert r.status_code == 422

def test_add_one_input_rejected(client, auth_headers):
    r = client.post("/calculations", json={"type": "addition", "inputs": [5]}, headers=auth_headers)
    assert r.status_code == 422

def test_add_no_inputs_rejected(client, auth_headers):
    r = client.post("/calculations", json={"type": "addition", "inputs": []}, headers=auth_headers)
    assert r.status_code == 422

def test_add_non_list_inputs_rejected(client, auth_headers):
    r = client.post("/calculations", json={"type": "addition", "inputs": "bad"}, headers=auth_headers)
    assert r.status_code == 422

def test_add_no_auth():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
    assert r.status_code == 401

def test_add_returns_all_fields(client, auth_headers):
    r = post_calc(client, auth_headers, "addition", [1, 2])
    d = r.json()
    for field in ("id", "user_id", "type", "inputs", "result", "created_at", "updated_at"):
        assert field in d


# ── Browse — GET /calculations ────────────────────────────────────────────────

def test_browse_empty(client, auth_headers):
    r = client.get("/calculations", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_browse_returns_own_calcs(client, auth_headers):
    post_calc(client, auth_headers, "addition", [1, 2])
    post_calc(client, auth_headers, "subtraction", [10, 3])
    r = client.get("/calculations", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 2

def test_browse_no_auth():
    from fastapi.testclient import TestClient
    from app.main import app
    r = TestClient(app, raise_server_exceptions=False).get("/calculations")
    assert r.status_code == 401

def test_browse_newest_first(client, auth_headers):
    post_calc(client, auth_headers, "addition",    [1, 1])
    post_calc(client, auth_headers, "subtraction", [2, 1])
    items = client.get("/calculations", headers=auth_headers).json()
    # created_at strings are ISO — last added should be first
    assert items[0]["created_at"] >= items[-1]["created_at"]


# ── Read — GET /calculations/{id} ────────────────────────────────────────────

def test_read_returns_correct_calc(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [6, 7]).json()
    r = client.get(f"/calculations/{created['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]
    assert r.json()["result"] == 13.0

def test_read_not_found(client, auth_headers):
    r = client.get(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404

def test_read_invalid_uuid(client, auth_headers):
    r = client.get("/calculations/not-a-uuid", headers=auth_headers)
    assert r.status_code == 400

def test_read_other_user_calc_returns_404(client, auth_headers, db_session):
    from app.models.user import User
    from app.models.calculation import Addition
    other = User(
        first_name="X", last_name="Y",
        email=f"x_{uuid.uuid4().hex[:6]}@t.com",
        username=f"x_{uuid.uuid4().hex[:6]}",
        password=User.hash_password("Pass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other); db_session.flush()
    c = Addition(user_id=other.id, inputs=[1, 2])
    c.result = 3.0
    db_session.add(c); db_session.commit()
    r = client.get(f"/calculations/{c.id}", headers=auth_headers)
    assert r.status_code == 404


# ── Edit — PUT /calculations/{id} ────────────────────────────────────────────

def test_edit_inputs(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [1, 2]).json()
    r = client.put(f"/calculations/{created['id']}", json={"inputs": [10, 20]}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["result"] == 30.0

def test_edit_multi_value_inputs(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [1, 2]).json()
    r = client.put(f"/calculations/{created['id']}", json={"inputs": [5, 5, 5, 5]}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["result"] == 20.0

def test_edit_type_and_inputs(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [10, 5]).json()
    r = client.put(f"/calculations/{created['id']}",
                   json={"type": "multiplication", "inputs": [2, 3, 4]}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["result"] == 24.0

def test_edit_type_only_keeps_inputs(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [5, 5]).json()
    r = client.put(f"/calculations/{created['id']}",
                   json={"type": "subtraction"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["result"] == 0.0   # 5 - 5

def test_edit_not_found(client, auth_headers):
    r = client.put(f"/calculations/{uuid.uuid4()}", json={"inputs": [1, 2]}, headers=auth_headers)
    assert r.status_code == 404

def test_edit_invalid_uuid(client, auth_headers):
    r = client.put("/calculations/bad-id", json={"inputs": [1, 2]}, headers=auth_headers)
    assert r.status_code == 400

def test_edit_division_by_zero_rejected(client, auth_headers):
    created = post_calc(client, auth_headers, "division", [10, 2]).json()
    r = client.put(f"/calculations/{created['id']}", json={"inputs": [10, 0]}, headers=auth_headers)
    assert r.status_code == 400


# ── Delete — DELETE /calculations/{id} ───────────────────────────────────────

def test_delete_removes_calc(client, auth_headers):
    created = post_calc(client, auth_headers, "addition", [5, 5]).json()
    r = client.delete(f"/calculations/{created['id']}", headers=auth_headers)
    assert r.status_code == 204
    assert client.get(f"/calculations/{created['id']}", headers=auth_headers).status_code == 404

def test_delete_does_not_affect_other_calcs(client, auth_headers):
    c1 = post_calc(client, auth_headers, "addition", [1, 1]).json()
    c2 = post_calc(client, auth_headers, "addition", [2, 2]).json()
    client.delete(f"/calculations/{c1['id']}", headers=auth_headers)
    assert client.get(f"/calculations/{c2['id']}", headers=auth_headers).status_code == 200

def test_delete_not_found(client, auth_headers):
    r = client.delete(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404

def test_delete_invalid_uuid(client, auth_headers):
    r = client.delete("/calculations/bad-id", headers=auth_headers)
    assert r.status_code == 400

def test_delete_other_user_calc_returns_404(client, auth_headers, db_session):
    from app.models.user import User
    from app.models.calculation import Addition
    other = User(
        first_name="D", last_name="T",
        email=f"d_{uuid.uuid4().hex[:6]}@t.com",
        username=f"d_{uuid.uuid4().hex[:6]}",
        password=User.hash_password("Pass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other); db_session.flush()
    c = Addition(user_id=other.id, inputs=[5, 5])
    c.result = 10.0
    db_session.add(c); db_session.commit()
    r = client.delete(f"/calculations/{c.id}", headers=auth_headers)
    assert r.status_code == 404
