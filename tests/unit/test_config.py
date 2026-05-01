# File: tests/unit/test_config.py
# Purpose: Unit tests for the Settings configuration class.
from app.core.config import Settings, get_settings


def test_settings_defaults():
    s = Settings()
    assert s.ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7


def test_settings_override_via_env(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    s = Settings()
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 60


def test_get_settings_returns_settings():
    s = get_settings()
    assert isinstance(s, Settings)


def test_get_settings_cached():
    # calling twice should return the same cached object
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_database_url_has_postgres():
    s = Settings()
    assert "postgresql" in s.DATABASE_URL or "postgres" in s.DATABASE_URL


def test_jwt_secret_keys_are_strings():
    s = Settings()
    assert isinstance(s.JWT_SECRET_KEY, str)
    assert isinstance(s.JWT_REFRESH_SECRET_KEY, str)