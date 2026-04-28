import os
import tempfile
from unittest.mock import patch

import pytest
from werkzeug.security import generate_password_hash

# DATA_DIR must be set before importing app so setup_db writes to a temp dir.
_tmpdir = tempfile.mkdtemp()
os.environ.setdefault("DATA_DIR", _tmpdir)

from app import app as flask_app  # noqa: E402
from models import db, User, Order  # noqa: E402

# Allow session cookies over HTTP in the test client.
flask_app.config["TESTING"] = True
flask_app.config["SESSION_COOKIE_SECURE"] = False

# Minimal lunch options for tests.  Shared so tests and conftest use the same data.
MOCK_LUNCH_OPTIONS = {
    "2025-04-28": {
        "restaurant": "Test Restaurant",
        "meals": [
            {"name": "Test Meal", "type": "C", "desc": "A test meal", "price": 25.00},
        ],
    }
}


@pytest.fixture(autouse=True)
def mock_lunch_options():
    """Prevent load_lunch_options() from hitting the filesystem on every request.

    before_request() calls load_lunch_options() for every HTTP request, including
    the login endpoint, so this must be active for all tests that use the client.
    Individual tests may re-patch with the same value; that is harmless.
    """
    with patch("app.load_lunch_options", return_value=MOCK_LUNCH_OPTIONS):
        yield


@pytest.fixture(autouse=True)
def clean_database():
    """Wipe all rows before each test so tests are independent."""
    with flask_app.app_context():
        db.session.query(Order).delete()
        db.session.query(User).delete()
        db.session.commit()
    yield


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture
def test_user(clean_database):
    """Create a test user and return their id."""
    with flask_app.app_context():
        user = User(
            username="testuser",
            password_hash=generate_password_hash("testpass"),
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def logged_in_user(client, clean_database):
    """Create a test user, log them in via the login endpoint, and return an
    object with .id so tests can reference the user's primary key.

    Because the app uses a server-side cachelib session, this fixture drives a
    real login request so Flask-Login stores a valid session in the cache.
    """
    with flask_app.app_context():
        user = User(
            username="checkout_test_user",
            password_hash=generate_password_hash("password"),
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client.post(
        "/login",
        data={"username": "checkout_test_user", "password": "password"},
        follow_redirects=False,
    )

    class U:
        id = user_id

    return U()


def login(client, username="testuser", password="testpass"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
