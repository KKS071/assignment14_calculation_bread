# File: tests/integration/test_api_auth.py
# Purpose: Integration tests for registration, login, and token endpoints.
import pytest


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    resp = client.post("/auth/register", json={
        "first_name": "Alice", "last_name": "Smith",
        "email": "alice.smith@test.com", "username": "alicesmith",
        "password": "SecurePass1!", "confirm_password": "SecurePass1!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alicesmith"
    assert "id" in data


def test_register_duplicate_email(client):
    payload = {
        "first_name": "Bob", "last_name": "Jones",
        "email": "bob.jones@test.com", "username": "bobjones",
        "password": "SecurePass1!", "confirm_password": "SecurePass1!",
    }
    client.post("/auth/register", json=payload)
    payload["username"] = "bobjones2"
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_register_duplicate_username(client):
    payload = {
        "first_name": "Carol", "last_name": "White",
        "email": "carol@test.com", "username": "carolw",
        "password": "SecurePass1!", "confirm_password": "SecurePass1!",
    }
    client.post("/auth/register", json=payload)
    payload["email"] = "carol2@test.com"
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_register_password_mismatch(client):
    resp = client.post("/auth/register", json={
        "first_name": "Dan", "last_name": "Brown",
        "email": "dan@test.com", "username": "danb",
        "password": "SecurePass1!", "confirm_password": "Different1!",
    })
    assert resp.status_code == 422


def test_register_weak_password(client):
    resp = client.post("/auth/register", json={
        "first_name": "Eve", "last_name": "Long",
        "email": "eve@test.com", "username": "evel",
        "password": "weakpass", "confirm_password": "weakpass",
    })
    assert resp.status_code == 422


# ── Login (JSON) ──────────────────────────────────────────────────────────────

def test_login_success(client, test_user):
    resp = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    resp = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "WrongPass99!",
    })
    assert resp.status_code == 401


def test_login_wrong_username(client):
    resp = client.post("/auth/login", json={"username": "nobody", "password": "TestPass123!"})
    assert resp.status_code == 401


def test_login_with_email(client, test_user):
    resp = client.post("/auth/login", json={
        "username": test_user.email,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200


# ── Login (form / Swagger) ────────────────────────────────────────────────────

def test_login_form_success(client, test_user):
    resp = client.post("/auth/token", data={
        "username": test_user.username,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_form_wrong_creds(client, test_user):
    resp = client.post("/auth/token", data={
        "username": test_user.username,
        "password": "bad",
    })
    assert resp.status_code == 401


# ── Protected route without token ────────────────────────────────────────────

def test_no_token_returns_401(client):
    resp = client.get("/calculations")
    assert resp.status_code == 401


def test_bad_token_returns_401(client):
    resp = client.get("/calculations", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401