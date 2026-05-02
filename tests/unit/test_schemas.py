# File: tests/unit/test_schemas.py
# Purpose: Unit tests for Pydantic schemas — multi-value inputs, normalization, error cases.
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationBase, CalculationCreate, CalculationUpdate, CalculationResponse, CalculationType,
)
from app.schemas.user import UserCreate, UserUpdate, UserLogin, PasswordUpdate
from app.schemas.token import TokenType


# ── CalculationBase — multi-value inputs ──────────────────────────────────────

def test_two_inputs():
    c = CalculationBase(type="addition", inputs=[1.0, 2.0])
    assert c.inputs == [1.0, 2.0]

def test_three_inputs():
    c = CalculationBase(type="addition", inputs=[1, 2, 3])
    assert len(c.inputs) == 3

def test_many_inputs():
    c = CalculationBase(type="multiplication", inputs=[2, 3, 4, 5])
    assert c.inputs == [2.0, 3.0, 4.0, 5.0]

def test_comma_string_inputs():
    c = CalculationBase(type="addition", inputs="10, 5, 3")
    assert c.inputs == [10.0, 5.0, 3.0]

def test_comma_string_no_spaces():
    c = CalculationBase(type="subtraction", inputs="20,8")
    assert c.inputs == [20.0, 8.0]

def test_type_normalised_uppercase():
    c = CalculationBase(type="ADDITION", inputs=[1, 2])
    assert c.type == CalculationType.ADDITION

def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="square_root", inputs=[4])

def test_non_list_non_string_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=42)

def test_one_input_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=[1])

def test_empty_inputs_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=[])

def test_division_by_zero_second_element():
    with pytest.raises(ValidationError):
        CalculationBase(type="division", inputs=[10, 0])

def test_division_by_zero_third_element():
    with pytest.raises(ValidationError):
        CalculationBase(type="division", inputs=[10, 2, 0])

def test_division_first_zero_is_ok():
    # Dividing zero by something is fine
    c = CalculationBase(type="division", inputs=[0, 5])
    assert c.inputs[0] == 0.0

def test_non_numeric_string_in_comma_list():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs="1, abc, 3")


# ── CalculationCreate ─────────────────────────────────────────────────────────

def test_calc_create_valid():
    c = CalculationCreate(type="subtraction", inputs=[10, 3, 1], user_id=uuid4())
    assert len(c.inputs) == 3

def test_calc_create_missing_type():
    with pytest.raises(ValidationError):
        CalculationCreate(inputs=[1, 2], user_id=uuid4())


# ── CalculationUpdate ─────────────────────────────────────────────────────────

def test_update_all_none():
    u = CalculationUpdate()
    assert u.type is None and u.inputs is None

def test_update_type_only():
    u = CalculationUpdate(type="division")
    assert u.type == "division"

def test_update_inputs_multi():
    u = CalculationUpdate(inputs=[5, 3, 2])
    assert u.inputs == [5.0, 3.0, 2.0]

def test_update_inputs_comma_string():
    u = CalculationUpdate(inputs="7, 2, 1")
    assert u.inputs == [7.0, 2.0, 1.0]

def test_update_one_input_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=[5])

def test_update_invalid_type_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(type="modulus")


# ── CalculationResponse ───────────────────────────────────────────────────────

def test_response_valid():
    r = CalculationResponse(
        id=uuid4(), user_id=uuid4(), type="multiplication",
        inputs=[2, 3, 4], result=24.0,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    assert r.result == 24.0


# ── UserCreate ────────────────────────────────────────────────────────────────

def test_user_create_valid():
    u = UserCreate(
        first_name="Jane", last_name="Doe", email="jane@test.com",
        username="janed", password="Secure1!", confirm_password="Secure1!",
    )
    assert u.username == "janed"

def test_user_create_password_mismatch():
    with pytest.raises(ValidationError):
        UserCreate(first_name="J", last_name="D", email="j@t.com",
                   username="jd123", password="Secure1!", confirm_password="Different1!")

def test_user_create_no_uppercase():
    with pytest.raises(ValidationError):
        UserCreate(first_name="J", last_name="D", email="j@t.com",
                   username="jd123", password="nouppercase1!", confirm_password="nouppercase1!")

def test_user_create_no_lowercase():
    with pytest.raises(ValidationError):
        UserCreate(first_name="J", last_name="D", email="j@t.com",
                   username="jd123", password="NOLOWER1!", confirm_password="NOLOWER1!")

def test_user_create_no_digit():
    with pytest.raises(ValidationError):
        UserCreate(first_name="J", last_name="D", email="j@t.com",
                   username="jd123", password="NoDigitHere!", confirm_password="NoDigitHere!")

def test_user_create_no_special():
    with pytest.raises(ValidationError):
        UserCreate(first_name="J", last_name="D", email="j@t.com",
                   username="jd123", password="Secure1234", confirm_password="Secure1234")


# ── Token enums ───────────────────────────────────────────────────────────────

def test_token_type_values():
    assert TokenType.ACCESS.value  == "access"
    assert TokenType.REFRESH.value == "refresh"

def test_password_update_same_raises():
    with pytest.raises(ValidationError):
        PasswordUpdate(current_password="Same1Pass!", new_password="Same1Pass!", confirm_new_password="Same1Pass!")
