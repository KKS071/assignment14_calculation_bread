# File: tests/integration/test_calculation_model.py
# Purpose: Integration tests for Calculation model BREAD ops against the real test DB.
import uuid
import pytest

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)
from app.models.user import User


@pytest.fixture()
def db_user(db_session):
    user = User(
        first_name="Calc", last_name="Tester",
        email=f"calc_{uuid.uuid4().hex[:8]}@test.com",
        username=f"calctester_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("Pass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_and_persist_addition(db_session, db_user):
    calc = Addition(user_id=db_user.id, inputs=[4.0, 6.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)

    found = db_session.query(Calculation).filter_by(id=calc.id).first()
    assert found is not None
    assert found.result == 10.0
    assert found.type == "addition"


def test_create_and_persist_subtraction(db_session, db_user):
    calc = Subtraction(user_id=db_user.id, inputs=[20.0, 8.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()

    found = db_session.query(Calculation).filter_by(id=calc.id).first()
    assert found.result == 12.0


def test_create_and_persist_multiplication(db_session, db_user):
    calc = Multiplication(user_id=db_user.id, inputs=[3.0, 7.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()

    found = db_session.query(Calculation).filter_by(id=calc.id).first()
    assert found.result == 21.0


def test_create_and_persist_division(db_session, db_user):
    calc = Division(user_id=db_user.id, inputs=[100.0, 4.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()

    found = db_session.query(Calculation).filter_by(id=calc.id).first()
    assert found.result == 25.0


def test_update_calc_inputs(db_session, db_user):
    calc = Addition(user_id=db_user.id, inputs=[1.0, 2.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()

    calc.inputs = [10.0, 20.0]
    calc.result = calc.get_result()
    db_session.commit()
    db_session.refresh(calc)
    assert calc.result == 30.0


def test_delete_calc(db_session, db_user):
    calc = Addition(user_id=db_user.id, inputs=[1.0, 1.0])
    calc.result = 2.0
    db_session.add(calc)
    db_session.commit()
    calc_id = calc.id

    db_session.delete(calc)
    db_session.commit()
    assert db_session.query(Calculation).filter_by(id=calc_id).first() is None


def test_filter_by_user(db_session, db_user):
    for i in range(3):
        c = Addition(user_id=db_user.id, inputs=[float(i), 1.0])
        c.result = c.get_result()
        db_session.add(c)
    db_session.commit()

    results = db_session.query(Calculation).filter_by(user_id=db_user.id).all()
    assert len(results) >= 3


def test_factory_with_db_user(db_session, db_user):
    calc = Calculation.create("multiplication", db_user.id, [5.0, 6.0])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)
    assert calc.result == 30.0
    assert calc.type == "multiplication"


def test_division_by_zero_not_persisted(db_session, db_user):
    calc = Division(user_id=db_user.id, inputs=[10.0, 0.0])
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.result = calc.get_result()
    # Nothing should have been committed
    db_session.rollback()