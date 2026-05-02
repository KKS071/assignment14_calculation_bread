# File: tests/integration/test_user_model.py
# Purpose: Integration tests for User model methods (register, authenticate, tokens).
import pytest
import uuid

from app.models.user import User


def test_register_and_retrieve(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()
    db_session.refresh(user)

    found = db_session.query(User).filter_by(email=fake_user_data["email"]).first()
    assert found is not None
    assert found.username == fake_user_data["username"]


def test_register_duplicate_raises(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    with pytest.raises(ValueError, match="already exists"):
        User.register(db_session, fake_user_data)


def test_register_short_password(db_session, fake_user_data):
    fake_user_data["password"] = "abc"
    with pytest.raises(ValueError, match="at least 6 characters"):
        User.register(db_session, fake_user_data)


def test_register_no_password(db_session, fake_user_data):
    fake_user_data.pop("password", None)
    with pytest.raises(ValueError, match="at least 6 characters"):
        User.register(db_session, fake_user_data)


def test_authenticate_success(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    assert result is not None
    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_authenticate_wrong_password(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["username"], "WrongPass")
    assert result is None


def test_authenticate_with_email(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["email"], "TestPass123")
    assert result is not None


def test_authenticate_unknown_user(db_session):
    result = User.authenticate(db_session, "nobody@nowhere.com", "pass")
    assert result is None


def test_last_login_updated_on_auth(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()
    assert user.last_login is None

    User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    db_session.refresh(user)
    assert user.last_login is not None


def test_token_create_and_verify(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    token = User.create_access_token({"sub": str(user.id)})
    decoded_id = User.verify_token(token)
    assert decoded_id == user.id


def test_verify_invalid_token():
    result = User.verify_token("invalid.token.value")
    assert result is None


def test_user_str_repr(test_user):
    s = str(test_user)
    assert test_user.first_name in s
    assert test_user.email in s


def test_user_update_method(db_session, test_user):
    original_email = test_user.email
    test_user.update(first_name="Updated")
    db_session.commit()
    db_session.refresh(test_user)
    assert test_user.first_name == "Updated"


def test_hash_password_differs_from_plain():
    hashed = User.hash_password("MyPass1!")
    assert hashed != "MyPass1!"


def test_verify_password_correct():
    hashed = User.hash_password("MyPass1!")
    user = User(
        first_name="A", last_name="B", email="a@b.com",
        username="ab", password=hashed,
    )
    assert user.verify_password("MyPass1!")


def test_verify_password_incorrect():
    hashed = User.hash_password("MyPass1!")
    user = User(
        first_name="A", last_name="B", email="a@b.com",
        username="ab", password=hashed,
    )
    assert not user.verify_password("WrongPass1!")


def test_hashed_password_property(test_user):
    assert test_user.hashed_password == test_user.password
