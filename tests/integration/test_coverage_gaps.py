# File: tests/integration/test_coverage_gaps.py
# Purpose: Targeted tests to reach 100% coverage on lines missed by the main test files.
import uuid
import time
import pytest
from datetime import timedelta
from unittest.mock import patch
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth.jwt import create_token, decode_token
from app.schemas.token import TokenType
from app.models.calculation import Calculation


# ── Calculation base — NotImplementedError ────────────────────────────────────

def test_base_calc_get_result_raises_not_implemented():
    calc = Calculation(user_id=uuid.uuid4(), inputs=[1, 2])
    with pytest.raises(NotImplementedError):
        calc.get_result()


# ── UserCreate — no lowercase / no digit validators ───────────────────────────

def test_user_create_no_lowercase():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(first_name="A", last_name="B", email="a@b.com",
                   username="abcde", password="NOLOWER1!", confirm_password="NOLOWER1!")
    assert "lowercase" in str(exc_info.value)


def test_user_create_no_digit():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(first_name="A", last_name="B", email="a@b.com",
                   username="abcde", password="NoDigitHere!", confirm_password="NoDigitHere!")
    assert "digit" in str(exc_info.value)


# ── JWT dependency — token with no "sub" claim ────────────────────────────────

def test_get_current_user_no_sub(db_session):
    from app.auth.dependencies import get_current_user
    from app.core.config import get_settings
    from jose import jwt as jose_jwt

    settings = get_settings()
    payload = {"type": "access", "exp": int(time.time()) + 3600, "jti": "abc"}
    token = jose_jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)
    assert exc_info.value.status_code == 401


# ── JWT decode — ExpiredSignatureError branch ─────────────────────────────────

def test_decode_expired_token():
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


# ── JWT create — encode exception → HTTP 500 ─────────────────────────────────

def test_create_token_encode_error_raises_http():
    with patch("app.auth.jwt.jwt.encode", side_effect=Exception("fail")):
        with pytest.raises(HTTPException) as exc_info:
            create_token(str(uuid.uuid4()), TokenType.ACCESS)
        assert exc_info.value.status_code == 500


# ── CalculationUpdate — invalid non-None type ─────────────────────────────────

def test_calc_update_invalid_type():
    from app.schemas.calculation import CalculationUpdate
    with pytest.raises(ValidationError):
        CalculationUpdate(type="squareroot")


# ── User.utcnow and update() method ──────────────────────────────────────────

def test_user_update_method_changes_name(db_session):
    from app.models.user import User
    user = User(
        first_name="T", last_name="U",
        email=f"utc_{uuid.uuid4().hex[:8]}@x.com",
        username=f"utc_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("Pass1!"),
        is_active=True,
    )
    db_session.add(user); db_session.commit()
    user.update(first_name="Changed")
    db_session.commit(); db_session.refresh(user)
    assert user.first_name == "Changed"


# ── User.create_refresh_token ─────────────────────────────────────────────────

def test_user_create_refresh_token():
    from app.models.user import User
    token = User.create_refresh_token({"sub": str(uuid.uuid4())})
    assert isinstance(token, str) and len(token) > 20


# ── HTML route — view/edit pages with real UUID param ────────────────────────

def test_view_page_with_uuid_param(client):
    resp = client.get(f"/dashboard/view/{uuid.uuid4()}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_edit_page_with_uuid_param(client):
    resp = client.get(f"/dashboard/edit/{uuid.uuid4()}")
    assert resp.status_code == 200


# ── Register route — ValueError → 400 ────────────────────────────────────────

def test_register_duplicate_returns_400(client):
    payload = {"first_name": "Dup", "last_name": "User", "email": "dup@example.com",
               "username": "dupuser99", "password": "SecurePass1!", "confirm_password": "SecurePass1!"}
    assert client.post("/auth/register", json=payload).status_code == 201
    payload["username"] = "dupuser100"
    assert client.post("/auth/register", json=payload).status_code == 400


# ── Multi-value schema — comma string coercion ───────────────────────────────

def test_calc_base_comma_string_three_values():
    from app.schemas.calculation import CalculationBase
    c = CalculationBase(type="addition", inputs="1, 2, 3")
    assert c.inputs == [1.0, 2.0, 3.0]


def test_calc_update_comma_string_inputs():
    from app.schemas.calculation import CalculationUpdate
    u = CalculationUpdate(inputs="5, 10, 15")
    assert u.inputs == [5.0, 10.0, 15.0]


def test_calc_base_invalid_comma_string():
    from app.schemas.calculation import CalculationBase
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs="1, abc, 3")
