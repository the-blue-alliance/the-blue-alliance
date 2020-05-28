import pytest
from werkzeug.test import Client


@pytest.fixture
def web_client() -> Client:
    from web.main import app

    return app.test_client()
