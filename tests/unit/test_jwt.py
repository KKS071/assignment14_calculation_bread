# File: tests/unit/test_jwt.py
# Purpose: Unit tests for JWT utility functions (hash, verify, create, decode).
import pytest
from datetime import timedelta
from unittest.mock import patch

from fastapi import HTTPException

from app.auth.jwt import (
    verify_password,
    get_password_hash,
    create_token,
    decode_token,
)
from app.schemas.token import TokenType


def test_hash_and_verify():
    hashed = get_password_hash("MySecret1!")
    assert verify_password("MySecret1!", hashed)
    assert not verify_password("WrongPass1!", hashed)


def test_hash_is_not_plain():
    hashed = get_password_hash("Plain1!")
    assert hashed != "Plain1!"


def test_create_access_token_returns_string():
    import uuid
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS)
    assert isinstance(token, str)
    assert len(token) > 20


def test_create_refresh_token_returns_string():
    import uuid
    token = create_token(str(uuid.uuid4()), TokenType.REFRESH)
    assert isinstance(token, str)


def test_create_token_with_uuid_object():
    import uuid
    uid = uuid.uuid4()
    token = create_token(uid, TokenType.ACCESS)
    assert isinstance(token, str)


def test_create_token_with_custom_expiry():
    import uuid
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS, expires_delta=timedelta(seconds=60))
    assert token is not None


def test_decode_access_token_valid():
    import uuid
    uid = str(uuid.uuid4())
    token = create_token(uid, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == uid
    assert payload["type"] == "access"


def test_decode_refresh_token_valid():
    import uuid
    uid = str(uuid.uuid4())
    token = create_token(uid, TokenType.REFRESH)
    payload = decode_token(token, TokenType.REFRESH)
    assert payload["sub"] == uid
    assert payload["type"] == "refresh"


def test_decode_wrong_token_type_raises():
    import uuid
    uid = str(uuid.uuid4())
    access_token = create_token(uid, TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(access_token, TokenType.REFRESH)
    assert exc_info.value.status_code == 401


def test_decode_invalid_token_raises():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.real.token", TokenType.ACCESS)
    assert exc_info.value.status_code == 401


def test_decode_expired_token_raises():
    import uuid
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, TokenType.ACCESS)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_create_token_exception_raises_http():
    import uuid
    with patch("app.auth.jwt.jwt.encode", side_effect=Exception("encode fail")):
        with pytest.raises(HTTPException) as exc_info:
            create_token(str(uuid.uuid4()), TokenType.ACCESS)
        assert exc_info.value.status_code == 500
