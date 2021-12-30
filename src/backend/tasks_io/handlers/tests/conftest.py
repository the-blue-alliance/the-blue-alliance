import pytest
from werkzeug.test import Client

from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
    FMSApiSecrets,
)


@pytest.fixture
def tasks_client(gae_testbed, ndb_stub, memcache_stub, taskqueue_stub) -> Client:
    from backend.tasks_io.main import app

    return app.test_client()


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
