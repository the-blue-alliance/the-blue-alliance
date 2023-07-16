import pytest
from werkzeug.test import Client


@pytest.fixture
def tasks_cpu_client(gae_testbed, ndb_stub, memcache_stub, taskqueue_stub) -> Client:
    from backend.tasks_cpu.main import app

    return app.test_client()
