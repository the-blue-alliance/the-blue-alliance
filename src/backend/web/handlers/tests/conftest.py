import pytest
from werkzeug.test import Client


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture
def web_client() -> Client:
    from backend.web.main import app

    return app.test_client()
