# File: tests/conftest.py
# Purpose: Shared fixtures for all tests — DB engine, sessions, test client, and helpers.
import uuid
import logging
from contextlib import contextmanager

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.calculation import Calculation

faker = Faker()
settings = get_settings()
logger = logging.getLogger(__name__)

# Use the TEST_DATABASE_URL if provided, otherwise fall back to the main DB URL.
TEST_DB_URL = settings.TEST_DATABASE_URL or settings.DATABASE_URL

test_engine = create_engine(TEST_DB_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def create_fake_user() -> dict:
    return {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "email": faker.unique.email(),
        "username": faker.unique.user_name()[:20],
        "password": "hashed_password",
    }


@contextmanager
def managed_db_session():
    """Context manager yielding a raw session — for tests that need manual control."""
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the test session, then drop them afterwards."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(setup_test_db):
    """Provide a transactional DB session that rolls back after each test.

    Uses a nested savepoint so that tests which trigger a DB-level exception
    (and an implicit rollback) don't deassociate the outer connection-level
    transaction, which would cause SAWarning noise on teardown.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create a savepoint so inner rollbacks don't kill the outer transaction
    session = TestSessionLocal(bind=connection)
    session.begin_nested()  # SAVEPOINT

    yield session

    session.close()
    # Only roll back the outer transaction if it's still active
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """Test client with the real DB session swapped in via dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session) -> User:
    """A committed test user."""
    user = User(
        first_name="Test",
        last_name="User",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("TestPass123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client, test_user, db_session):
    """Return Authorization headers for the test user."""
    resp = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def fake_user_data() -> dict:
    return {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "email": faker.unique.email(),
        "username": faker.unique.user_name()[:20],
        "password": "PlainPass123",
    }


@pytest.fixture()
def seed_users(db_session):
    """Create and commit three test users."""
    users = []
    for _ in range(3):
        data = create_fake_user()
        u = User(**data)
        db_session.add(u)
        users.append(u)
    db_session.commit()
    for u in users:
        db_session.refresh(u)
    return users
