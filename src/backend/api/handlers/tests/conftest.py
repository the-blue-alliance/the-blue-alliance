import pytest
from werkzeug.test import Client


@pytest.fixture
def api_client(gae_testbed, ndb_stub, memcache_stub, taskqueue_stub) -> Client:
    from backend.api.main import app

    return app.test_client()
