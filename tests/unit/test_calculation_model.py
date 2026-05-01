# File: tests/unit/test_calculation_model.py
# Purpose: Unit tests for Calculation model logic (factory, get_result, edge cases).
import uuid
import pytest

from app.models.calculation import (
    Addition,
    Calculation,
    Division,
    Multiplication,
    Subtraction,
)


def uid():
    return uuid.uuid4()


# ── Addition ──────────────────────────────────────────────────────────────────

def test_addition_basic():
    assert Addition(user_id=uid(), inputs=[1, 2, 3]).get_result() == 6


def test_addition_floats():
    assert Addition(user_id=uid(), inputs=[1.5, 2.5]).get_result() == 4.0


def test_addition_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Addition(user_id=uid(), inputs="bad").get_result()


def test_addition_one_input_raises():
    with pytest.raises(ValueError, match="at least two"):
        Addition(user_id=uid(), inputs=[5]).get_result()


# ── Subtraction ───────────────────────────────────────────────────────────────

def test_subtraction_basic():
    assert Subtraction(user_id=uid(), inputs=[20, 5, 3]).get_result() == 12


def test_subtraction_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Subtraction(user_id=uid(), inputs=42).get_result()


def test_subtraction_one_input_raises():
    with pytest.raises(ValueError, match="at least two"):
        Subtraction(user_id=uid(), inputs=[10]).get_result()


# ── Multiplication ────────────────────────────────────────────────────────────

def test_multiplication_basic():
    assert Multiplication(user_id=uid(), inputs=[2, 3, 4]).get_result() == 24


def test_multiplication_with_zero():
    assert Multiplication(user_id=uid(), inputs=[5, 0]).get_result() == 0


def test_multiplication_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Multiplication(user_id=uid(), inputs=None).get_result()


def test_multiplication_one_input_raises():
    with pytest.raises(ValueError, match="at least two"):
        Multiplication(user_id=uid(), inputs=[7]).get_result()


# ── Division ──────────────────────────────────────────────────────────────────

def test_division_basic():
    assert Division(user_id=uid(), inputs=[100, 2, 5]).get_result() == 10.0


def test_division_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        Division(user_id=uid(), inputs=[50, 0, 5]).get_result()


def test_division_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Division(user_id=uid(), inputs="x").get_result()


def test_division_one_input_raises():
    with pytest.raises(ValueError, match="at least two"):
        Division(user_id=uid(), inputs=[10]).get_result()


# ── Factory ───────────────────────────────────────────────────────────────────

def test_factory_addition():
    c = Calculation.create("addition", uid(), [1, 2])
    assert isinstance(c, Addition)


def test_factory_subtraction():
    c = Calculation.create("subtraction", uid(), [10, 4])
    assert isinstance(c, Subtraction)
    assert c.get_result() == 6


def test_factory_multiplication():
    c = Calculation.create("multiplication", uid(), [3, 4])
    assert isinstance(c, Multiplication)


def test_factory_division():
    c = Calculation.create("division", uid(), [10, 2])
    assert isinstance(c, Division)


def test_factory_case_insensitive():
    c = Calculation.create("ADDITION", uid(), [1, 2])
    assert isinstance(c, Addition)


def test_factory_invalid_type_raises():
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create("modulus", uid(), [10, 3])


def test_calc_repr():
    c = Addition(user_id=uid(), inputs=[1, 2])
    assert "addition" in repr(c).lower() or "Calculation" in repr(c)