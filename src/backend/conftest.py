import pytest
from _pytest.monkeypatch import MonkeyPatch
from google.appengine.ext import testbed
from google.cloud import ndb
from google.cloud.datastore_v1.proto import datastore_pb2_grpc
from google.cloud.ndb import _datastore_api
from InMemoryCloudDatastoreStub import datastore_stub

from backend.common.models.cached_query_result import CachedQueryResult
from backend.tests.json_data_importer import JsonDataImporter


@pytest.fixture(autouse=True)
def init_test_marker_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "true")


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
def gae_testbed():
    tb = testbed.Testbed()
    tb.activate()
    yield tb
    tb.deactivate()


@pytest.fixture()
def ndb_stub(
    gae_testbed, monkeypatch: MonkeyPatch
) -> datastore_stub.LocalDatastoreStub:
    stub = datastore_stub.LocalDatastoreStub()

    def mock_stub() -> datastore_pb2_grpc.DatastoreStub:
        return stub

    monkeypatch.setattr(_datastore_api, "stub", mock_stub)
    return stub


@pytest.fixture()
def taskqueue_stub(gae_testbed):
    gae_testbed.init_taskqueue_stub(root_path="src/")
    return gae_testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)


@pytest.fixture()
def ndb_client(init_ndb_env_vars, ndb_stub) -> ndb.Client:
    return ndb.Client()


@pytest.fixture()
def ndb_context(request, ndb_client: ndb.Client):
    if "no_auto_ndb_context" in request.keywords:
        yield
        return
    with ndb_client.context() as context:
        yield context


@pytest.fixture()
def test_data_importer(ndb_client) -> JsonDataImporter:
    return JsonDataImporter(ndb_client)


def clear_cached_queries() -> None:
    ndb.delete_multi(CachedQueryResult.query().fetch(keys_only=True))
