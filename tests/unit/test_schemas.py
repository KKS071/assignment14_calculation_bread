# File: tests/unit/test_schemas.py
# Purpose: Unit tests for Pydantic schemas — validation, normalization, and error cases.
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationBase,
    CalculationCreate,
    CalculationUpdate,
    CalculationResponse,
    CalculationType,
)
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserUpdate, PasswordUpdate
from app.schemas.token import Token, TokenResponse, TokenType


# ── CalculationBase ───────────────────────────────────────────────────────────

def test_calc_base_valid():
    c = CalculationBase(type="addition", inputs=[1.0, 2.0])
    assert c.type == CalculationType.ADDITION


def test_calc_base_type_normalized_to_lowercase():
    c = CalculationBase(type="ADDITION", inputs=[1, 2])
    assert c.type == "addition"


def test_calc_base_invalid_type():
    with pytest.raises(ValidationError):
        CalculationBase(type="square_root", inputs=[4])


def test_calc_base_non_list_inputs():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs="1,2")


def test_calc_base_one_input():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=[1])


def test_calc_base_division_by_zero():
    with pytest.raises(ValidationError):
        CalculationBase(type="division", inputs=[10, 0])


def test_calc_base_division_zero_in_middle():
    with pytest.raises(ValidationError):
        CalculationBase(type="division", inputs=[10, 2, 0, 5])


# ── CalculationCreate ─────────────────────────────────────────────────────────

def test_calc_create_valid():
    c = CalculationCreate(type="subtraction", inputs=[10, 3], user_id=uuid4())
    assert c.inputs == [10.0, 3.0]


def test_calc_create_missing_type():
    with pytest.raises(ValidationError):
        CalculationCreate(inputs=[1, 2], user_id=uuid4())


def test_calc_create_missing_inputs():
    with pytest.raises(ValidationError):
        CalculationCreate(type="addition", user_id=uuid4())


# ── CalculationUpdate ─────────────────────────────────────────────────────────

def test_calc_update_valid():
    u = CalculationUpdate(inputs=[5.0, 2.5])
    assert u.inputs == [5.0, 2.5]


def test_calc_update_empty():
    u = CalculationUpdate()
    assert u.inputs is None
    assert u.type is None


def test_calc_update_with_type():
    u = CalculationUpdate(type="multiplication", inputs=[2, 3])
    assert u.type == "multiplication"


def test_calc_update_invalid_type():
    with pytest.raises(ValidationError):
        CalculationUpdate(type="bad")


def test_calc_update_one_input():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=[5])


# ── CalculationResponse ───────────────────────────────────────────────────────

def test_calc_response_valid():
    r = CalculationResponse(
        id=uuid4(), user_id=uuid4(), type="addition",
        inputs=[1, 2], result=3.0,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    assert r.result == 3.0


# ── UserCreate ────────────────────────────────────────────────────────────────

def test_user_create_valid():
    u = UserCreate(
        first_name="Jane", last_name="Doe", email="jane@test.com",
        username="janed", password="Secure1!", confirm_password="Secure1!",
    )
    assert u.username == "janed"


def test_user_create_password_mismatch():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="J", last_name="D", email="j@t.com",
            username="jd123", password="Secure1!", confirm_password="Different1!",
        )


def test_user_create_weak_password_no_upper():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="J", last_name="D", email="j@t.com",
            username="jd123", password="secure1!noup", confirm_password="secure1!noup",
        )


def test_user_create_weak_password_no_special():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="J", last_name="D", email="j@t.com",
            username="jd123", password="Secure1234", confirm_password="Secure1234",
        )


# ── UserLogin ─────────────────────────────────────────────────────────────────

def test_user_login_valid():
    l = UserLogin(username="johndoe", password="SecurePass1!")
    assert l.username == "johndoe"


# ── UserUpdate ────────────────────────────────────────────────────────────────

def test_user_update_partial():
    u = UserUpdate(first_name="NewName")
    assert u.first_name == "NewName"
    assert u.last_name is None


# ── PasswordUpdate ────────────────────────────────────────────────────────────

def test_password_update_valid():
    p = PasswordUpdate(
        current_password="OldPass1!", new_password="NewPass1!",
        confirm_new_password="NewPass1!",
    )
    assert p.new_password == "NewPass1!"


def test_password_update_mismatch():
    with pytest.raises(ValidationError):
        PasswordUpdate(
            current_password="OldPass1!", new_password="NewPass1!",
            confirm_new_password="Different1!",
        )


def test_password_update_same_as_current():
    with pytest.raises(ValidationError):
        PasswordUpdate(
            current_password="Same1Pass!", new_password="Same1Pass!",
            confirm_new_password="Same1Pass!",
        )


# ── Token schemas ─────────────────────────────────────────────────────────────

def test_token_type_enum():
    assert TokenType.ACCESS.value == "access"
    assert TokenType.REFRESH.value == "refresh"