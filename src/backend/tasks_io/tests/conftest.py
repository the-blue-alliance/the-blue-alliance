import pytest
from flask.testing import FlaskClient


@pytest.fixture
def tasks_io_client() -> FlaskClient:
    from backend.tasks_io.main import app

    return app.test_client()
