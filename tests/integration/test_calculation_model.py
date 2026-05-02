# File: tests/integration/test_calculation_model.py
# Purpose: Integration tests for Calculation model — multi-value BREAD ops against the test DB.
import uuid
import pytest
from app.models.calculation import Calculation, Addition, Subtraction, Multiplication, Division
from app.models.user import User


@pytest.fixture()
def db_user(db_session):
    user = User(
        first_name="Multi", last_name="Tester",
        email=f"multi_{uuid.uuid4().hex[:8]}@test.com",
        username=f"multi_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("Pass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_persist_addition_two(db_session, db_user):
    c = Addition(user_id=db_user.id, inputs=[4.0, 6.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit(); db_session.refresh(c)
    assert db_session.query(Calculation).filter_by(id=c.id).first().result == 10.0

def test_persist_addition_three(db_session, db_user):
    c = Addition(user_id=db_user.id, inputs=[1.0, 2.0, 3.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit()
    assert db_session.query(Calculation).filter_by(id=c.id).first().result == 6.0

def test_persist_subtraction_multi(db_session, db_user):
    c = Subtraction(user_id=db_user.id, inputs=[100.0, 30.0, 20.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit()
    assert db_session.query(Calculation).filter_by(id=c.id).first().result == 50.0

def test_persist_multiplication_multi(db_session, db_user):
    c = Multiplication(user_id=db_user.id, inputs=[2.0, 3.0, 4.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit()
    assert db_session.query(Calculation).filter_by(id=c.id).first().result == 24.0

def test_persist_division_multi(db_session, db_user):
    c = Division(user_id=db_user.id, inputs=[120.0, 2.0, 3.0, 4.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit()
    assert db_session.query(Calculation).filter_by(id=c.id).first().result == 5.0

def test_update_multi_inputs(db_session, db_user):
    c = Addition(user_id=db_user.id, inputs=[1.0, 2.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit()
    c.inputs = [10.0, 20.0, 30.0]
    c.result = c.get_result()
    db_session.commit(); db_session.refresh(c)
    assert c.result == 60.0

def test_delete_calc(db_session, db_user):
    c = Addition(user_id=db_user.id, inputs=[1.0, 1.0])
    c.result = 2.0
    db_session.add(c); db_session.commit()
    cid = c.id
    db_session.delete(c); db_session.commit()
    assert db_session.query(Calculation).filter_by(id=cid).first() is None

def test_filter_by_user(db_session, db_user):
    for i in range(3):
        c = Addition(user_id=db_user.id, inputs=[float(i), 1.0])
        c.result = c.get_result()
        db_session.add(c)
    db_session.commit()
    assert db_session.query(Calculation).filter_by(user_id=db_user.id).count() >= 3

def test_factory_multi(db_session, db_user):
    c = Calculation.create("multiplication", db_user.id, [5.0, 6.0, 2.0])
    c.result = c.get_result()
    db_session.add(c); db_session.commit(); db_session.refresh(c)
    assert c.result == 60.0

def test_division_zero_not_persisted(db_session, db_user):
    c = Division(user_id=db_user.id, inputs=[10.0, 0.0])
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        c.result = c.get_result()
    db_session.rollback()
