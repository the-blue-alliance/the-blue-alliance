import pytest
from werkzeug.test import Client


@pytest.fixture
def api_client() -> Client:
    from backend.api.main import app

    return app.test_client()
