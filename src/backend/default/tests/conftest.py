import pytest
from werkzeug.test import Client


@pytest.fixture
def default_client() -> Client:
    from backend.default.main import app

    return app.test_client()
