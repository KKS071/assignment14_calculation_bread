# File: tests/unit/test_coverage_gaps.py
# Purpose: Targeted tests to reach 100% coverage on lines missed by other test files.
import uuid
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth.jwt import create_token, decode_token
from app.schemas.token import TokenType
from app.models.calculation import Calculation


# ── app/models/calculation.py line 73 ────────────────────────────────────────
# Calling get_result() on the abstract base Calculation (not a subclass) raises NotImplementedError

def test_base_calculation_get_result_raises():
    calc = Calculation(user_id=uuid.uuid4(), inputs=[1, 2])
    with pytest.raises(NotImplementedError):
        calc.get_result()


# ── app/schemas/user.py lines 35, 37 ─────────────────────────────────────────
# Password strength validators: no lowercase, no digit

def test_user_create_no_lowercase():
    from pydantic import ValidationError
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            first_name="A", last_name="B", email="a@b.com",
            username="abcde", password="NOLOWER1!", confirm_password="NOLOWER1!",
        )
    errors = str(exc_info.value)
    assert "lowercase" in errors


def test_user_create_no_digit():
    from pydantic import ValidationError
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            first_name="A", last_name="B", email="a@b.com",
            username="abcde", password="NoDigitHere!", confirm_password="NoDigitHere!",
        )
    errors = str(exc_info.value)
    assert "digit" in errors


# ── app/auth/dependencies.py line 30 ─────────────────────────────────────────
# get_current_user when the token payload has no "sub" field

def test_get_current_user_no_sub(db_session):
    from app.auth.dependencies import get_current_user
    from app.core.config import get_settings
    from jose import jwt
    import time

    settings = get_settings()
    # Craft a token with no "sub" claim
    payload = {"type": "access", "exp": int(time.time()) + 3600, "jti": "abc"}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)
    assert exc_info.value.status_code == 401


# ── app/auth/jwt.py line 77 ──────────────────────────────────────────────────
# decode_token with a genuinely expired token hitting the ExpiredSignatureError branch

def test_decode_expired_token_hits_expired_branch():
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS, expires_delta=timedelta(seconds=-10))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


# ── app/schemas/calculation.py line 61 ───────────────────────────────────────
# CalculationUpdate.normalize_type with a non-None invalid value

def test_calc_update_invalid_type_branch():
    from app.schemas.calculation import CalculationUpdate
    with pytest.raises(ValidationError):
        CalculationUpdate(type="squareroot")


# ── app/models/user.py line 40 ───────────────────────────────────────────────
# utcnow() is called on updated_at default — exercise via update()

def test_user_utcnow_called_on_update(db_session):
    from app.models.user import User
    user = User(
        first_name="T", last_name="U",
        email=f"utctest_{uuid.uuid4().hex[:8]}@x.com",
        username=f"utctest_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("Pass1!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    before = user.updated_at
    user.update(first_name="Changed")
    db_session.commit()
    db_session.refresh(user)
    assert user.first_name == "Changed"


# ── app/models/user.py line 136 ──────────────────────────────────────────────
# create_refresh_token class method

def test_user_create_refresh_token():
    from app.models.user import User
    token = User.create_refresh_token({"sub": str(uuid.uuid4())})
    assert isinstance(token, str)
    assert len(token) > 20


# ── app/main.py HTML routes (lines 112, 114) ─────────────────────────────────
# Already covered by test_api_routes — these tests ensure render with calc_id param

def test_view_page_with_real_uuid(client):
    calc_id = str(uuid.uuid4())
    resp = client.get(f"/dashboard/view/{calc_id}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_edit_page_with_real_uuid(client):
    calc_id = str(uuid.uuid4())
    resp = client.get(f"/dashboard/edit/{calc_id}")
    assert resp.status_code == 200


# ── app/main.py line 170-172 — register ValueError path ─────────────────────

def test_register_raises_value_error_returns_400(client):
    # First registration succeeds
    payload = {
        "first_name": "Dup", "last_name": "User",
        "email": "dup@example.com", "username": "dupuser",
        "password": "SecurePass1!", "confirm_password": "SecurePass1!",
    }
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    # Second with same email → triggers ValueError inside User.register → 400
    payload["username"] = "dupuser2"
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400
