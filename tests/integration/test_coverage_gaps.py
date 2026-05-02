# File: tests/integration/test_coverage_gaps.py
# Purpose: Targeted tests to hit every uncovered branch and reach 100% coverage.
import time
import uuid
import pytest
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth.jwt import create_token, decode_token
from app.schemas.token import TokenType
from app.models.calculation import Calculation


# ── models/calculation.py — non-list inputs for Subtraction, Multiplication, Division ──

def test_subtraction_non_list_inputs_raises():
    from app.models.calculation import Subtraction
    c = Subtraction(user_id=uuid.uuid4(), inputs="bad")
    with pytest.raises(ValueError, match="must be a list"):
        c.get_result()


def test_subtraction_one_input_raises():
    from app.models.calculation import Subtraction
    c = Subtraction(user_id=uuid.uuid4(), inputs=[10])
    with pytest.raises(ValueError, match="two"):
        c.get_result()


def test_multiplication_non_list_inputs_raises():
    from app.models.calculation import Multiplication
    c = Multiplication(user_id=uuid.uuid4(), inputs="bad")
    with pytest.raises(ValueError, match="must be a list"):
        c.get_result()


def test_multiplication_one_input_raises():
    from app.models.calculation import Multiplication
    c = Multiplication(user_id=uuid.uuid4(), inputs=[5])
    with pytest.raises(ValueError, match="two"):
        c.get_result()


def test_division_non_list_inputs_raises():
    from app.models.calculation import Division
    c = Division(user_id=uuid.uuid4(), inputs="bad")
    with pytest.raises(ValueError, match="must be a list"):
        c.get_result()


def test_base_calculation_get_result_raises():
    """AbstractCalculation.get_result() must raise NotImplementedError."""
    c = Calculation(user_id=uuid.uuid4(), inputs=[1, 2])
    with pytest.raises(NotImplementedError):
        c.get_result()


# ── schemas/calculation.py — CalculationUpdate coerce_inputs branches ─────────

def test_calc_update_valid_comma_string():
    """CalculationUpdate accepts comma-separated string — hits the isinstance(v,str) branch."""
    from app.schemas.calculation import CalculationUpdate
    u = CalculationUpdate(inputs="5, 10, 15")
    assert u.inputs == [5.0, 10.0, 15.0]


def test_calc_update_invalid_comma_string_raises():
    """Non-numeric comma string — hits the ValueError branch inside try/except."""
    from app.schemas.calculation import CalculationUpdate
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs="1, abc, 3")


def test_calc_update_non_list_non_string_raises():
    """Passing an integer — hits the 'not isinstance(v, list)' branch."""
    from app.schemas.calculation import CalculationUpdate
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=42)


# ── schemas/user.py — PasswordUpdate validators ───────────────────────────────

def test_password_update_mismatch_raises():
    """new_password != confirm_new_password — hits line 96."""
    from app.schemas.user import PasswordUpdate
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(
            current_password="OldPass1!",
            new_password="NewPass1!",
            confirm_new_password="Different1!",
        )
    assert "do not match" in str(exc_info.value)


def test_password_update_same_as_current_raises():
    """new_password == current_password — hits line 99."""
    from app.schemas.user import PasswordUpdate
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(
            current_password="SamePass1!",
            new_password="SamePass1!",
            confirm_new_password="SamePass1!",
        )
    assert "different" in str(exc_info.value)


# ── schemas/user.py — UserCreate password strength branches ──────────────────

def test_user_create_no_lowercase_raises():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(first_name="A", last_name="B", email="a@b.com",
                   username="abcde", password="NOLOWER1!", confirm_password="NOLOWER1!")
    assert "lowercase" in str(exc_info.value)


def test_user_create_no_digit_raises():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(first_name="A", last_name="B", email="a@b.com",
                   username="abcde", password="NoDigitHere!", confirm_password="NoDigitHere!")
    assert "digit" in str(exc_info.value)


# ── auth/jwt.py:77 — ExpiredSignatureError branch in decode_token ─────────────

def test_decode_expired_token_raises_401():
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


# ── auth/jwt.py — encode exception path ──────────────────────────────────────

def test_create_token_encode_error_raises_500():
    with patch("app.auth.jwt.jwt.encode", side_effect=Exception("enc fail")):
        with pytest.raises(HTTPException) as exc_info:
            create_token(str(uuid.uuid4()), TokenType.ACCESS)
        assert exc_info.value.status_code == 500


# ── auth/dependencies.py — token with no "sub" claim ─────────────────────────

def test_get_current_user_no_sub_raises_401(db_session):
    from app.auth.dependencies import get_current_user
    from app.core.config import get_settings
    from jose import jwt as jose_jwt

    cfg = get_settings()
    payload = {"type": "access", "exp": int(time.time()) + 3600, "jti": "abc"}
    token = jose_jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.ALGORITHM)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)
    assert exc_info.value.status_code == 401


# ── main.py:131,133 — login route expires_at branches ────────────────────────

def test_login_with_naive_expires_at(client, test_user):
    """Patch User.authenticate to return a naive (timezone-unaware) expires_at.
    This hits the 'if expires_at.tzinfo is None' branch (line 131)."""
    original = __import__("app.models.user", fromlist=["User"]).User.authenticate

    def patched_authenticate(db, username, password):
        result = original(db, username, password)
        if result:
            # Replace timezone-aware expires_at with a naive one
            result["expires_at"] = datetime.utcnow() + timedelta(minutes=30)
        return result

    with patch("app.main.User.authenticate", side_effect=patched_authenticate):
        resp = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "TestPass123!",
        })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_with_none_expires_at(client, test_user):
    """Patch User.authenticate to return expires_at=None.
    This hits the 'if not expires_at' branch (line 133)."""
    original = __import__("app.models.user", fromlist=["User"]).User.authenticate

    def patched_authenticate(db, username, password):
        result = original(db, username, password)
        if result:
            result["expires_at"] = None
        return result

    with patch("app.main.User.authenticate", side_effect=patched_authenticate):
        resp = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "TestPass123!",
        })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# ── main.py:208-210 — create_calculation ValueError from model ───────────────

def test_create_calculation_model_raises_value_error(client, auth_headers):
    """Mock Calculation.create to raise ValueError after schema validation passes.
    This hits the except ValueError block (lines 208-210) in create_calculation."""
    with patch("app.main.Calculation.create", side_effect=ValueError("model error")):
        resp = client.post(
            "/calculations",
            json={"type": "addition", "inputs": [1, 2]},
            headers=auth_headers,
        )
    assert resp.status_code == 400
    assert "model error" in resp.json()["detail"]


# ── main.py:403 — delete return None ─────────────────────────────────────────

def test_delete_returns_204_no_content(client, auth_headers):
    """Confirm DELETE returns 204 and no body — covers the return None line."""
    created = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [1, 2]},
        headers=auth_headers,
    ).json()
    resp = client.delete(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


# ── models/user.py — utcnow() via update() and create_refresh_token ──────────

def test_user_update_calls_utcnow(db_session):
    from app.models.user import User
    user = User(
        first_name="T", last_name="U",
        email=f"utc_{uuid.uuid4().hex[:8]}@x.com",
        username=f"utc_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("Pass1!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    user.update(first_name="Changed")
    db_session.commit()
    db_session.refresh(user)
    assert user.first_name == "Changed"


def test_user_create_refresh_token():
    from app.models.user import User
    token = User.create_refresh_token({"sub": str(uuid.uuid4())})
    assert isinstance(token, str) and len(token) > 20


# ── HTML routes — covered to ensure view/edit page routes are hit ─────────────

def test_view_page_renders(client):
    resp = client.get(f"/dashboard/view/{uuid.uuid4()}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_edit_page_renders(client):
    resp = client.get(f"/dashboard/edit/{uuid.uuid4()}")
    assert resp.status_code == 200


def test_register_duplicate_returns_400(client):
    payload = {
        "first_name": "Dup", "last_name": "User",
        "email": "dupcov@example.com", "username": "dupcov99",
        "password": "SecurePass1!", "confirm_password": "SecurePass1!",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    payload["username"] = "dupcov100"
    assert client.post("/auth/register", json=payload).status_code == 400
