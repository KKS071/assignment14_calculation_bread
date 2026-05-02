# File: tests/integration/test_database_init.py
# Purpose: Tests for database_init helpers (init_db / drop_db).
from unittest.mock import patch, MagicMock

from app import database_init


def test_init_db_calls_create_all():
    mock_engine = MagicMock()
    mock_meta = MagicMock()

    with patch("app.database_init.engine", mock_engine), \
         patch("app.database_init.Base") as mock_base:
        mock_base.metadata = mock_meta
        database_init.init_db()
        mock_meta.create_all.assert_called_once_with(bind=mock_engine)


def test_drop_db_calls_drop_all():
    mock_engine = MagicMock()
    mock_meta = MagicMock()

    with patch("app.database_init.engine", mock_engine), \
         patch("app.database_init.Base") as mock_base:
        mock_base.metadata = mock_meta
        database_init.drop_db()
        mock_meta.drop_all.assert_called_once_with(bind=mock_engine)
