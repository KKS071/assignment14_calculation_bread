# File: tests/integration/test_database.py
# Purpose: Tests for database utility functions (get_engine, get_sessionmaker, get_db).
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app import database as db_module
from app.database import get_db, get_engine, get_sessionmaker


def test_get_engine_returns_engine():
    eng = get_engine()
    assert isinstance(eng, Engine)


def test_get_sessionmaker_returns_sessionmaker():
    eng = get_engine()
    sm = get_sessionmaker(eng)
    assert isinstance(sm, sessionmaker)


def test_get_db_yields_session():
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    try:
        next(gen)
    except StopIteration:
        pass
    finally:
        session.close()


def test_base_has_metadata():
    from app.database import Base
    assert hasattr(Base, "metadata")
