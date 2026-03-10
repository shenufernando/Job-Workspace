import pytest
from unittest.mock import MagicMock
import sys
import os

# Add the backend directory to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
import utils.database

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "JWT_SECRET_KEY": "test_secret_key"
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db(monkeypatch):
    """
    Creates a flexible MySQL mock connection that intercepts database queries and prevents actual SQL execution.
    Returns a tuple of (mock_connection, mock_cursor).
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configure cursor to behave somewhat like a real cursor
    mock_conn.cursor.return_value = mock_cursor
    
    # The dictionary cursor behavior
    mock_dict_cursor = MagicMock()
    def cursor_side_effect(dictionary=False):
        if dictionary:
            return mock_dict_cursor
        return mock_cursor
        
    mock_conn.cursor.side_effect = cursor_side_effect
    
    # Intercept raw MySQL connections allowing g.db context integration properly
    import mysql.connector
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: mock_conn)
    
    return mock_conn, mock_cursor, mock_dict_cursor
