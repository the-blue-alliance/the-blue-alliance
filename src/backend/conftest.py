import pytest

from google.cloud import ndb
from google.cloud.datastore_v1.proto import datastore_pb2_grpc
from google.cloud.ndb import _datastore_api
from _pytest.monkeypatch import MonkeyPatch
from InMemoryCloudDatastoreStub import datastore_stub


@pytest.fixture(autouse=True)
def init_ndb_env_vars(monkeypatch: MonkeyPatch) -> None:
    """
    Initializing an ndb Client in a test env requires some environment variables to be set
    For now, these are just garbage values intended to give the library _something_
    (we don't expect them to actually work yet)
    """

    monkeypatch.setenv("DATASTORE_EMULATOR_HOST", "localhost:8432")
    monkeypatch.setenv("DATASTORE_DATASET", "tba-unit-test")


@pytest.fixture()
def ndb_stub(monkeypatch: MonkeyPatch) -> datastore_stub.LocalDatastoreStub:
    stub = datastore_stub.LocalDatastoreStub()

    def mock_stub() -> datastore_pb2_grpc.DatastoreStub:
        return stub

    monkeypatch.setattr(_datastore_api, "stub", mock_stub)
    return stub


@pytest.fixture()
def ndb_context(init_ndb_env_vars, ndb_stub):
    client = ndb.Client()
    with client.context() as context:
        yield context
