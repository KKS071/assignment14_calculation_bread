# File: tests/integration/test_auth_dependencies.py
# Purpose: Integration tests for get_current_user and get_current_active_user dependencies.
import uuid
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from app.auth.dependencies import get_current_user, get_current_active_user
from app.auth.jwt import create_token
from app.schemas.token import TokenType
from app.models.user import User


def make_mock_user(is_active=True):
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.is_active = is_active
    return user


def test_get_current_user_valid_token(db_session, test_user):
    token = create_token(str(test_user.id), TokenType.ACCESS)
    user = get_current_user(token=token, db=db_session)
    assert user.id == test_user.id


def test_get_current_user_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="bad.token.here", db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_user_unknown_user_id(db_session):
    token = create_token(str(uuid.uuid4()), TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_active_user_active(test_user):
    result = get_current_active_user(current_user=test_user)
    assert result == test_user


def test_get_current_active_user_inactive():
    inactive_user = make_mock_user(is_active=False)
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=inactive_user)
    assert exc_info.value.status_code == 400
    assert "Inactive" in exc_info.value.detail