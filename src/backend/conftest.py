from typing import Generator

import pytest
from freezegun import api as freezegun_api
from google.appengine.api import datastore_types
from google.appengine.ext import ndb, testbed

from backend.common.context_cache import context_cache
from backend.common.models.cached_query_result import CachedQueryResult
from backend.tests.json_data_importer import JsonDataImporter


@pytest.fixture(autouse=True)
def init_test_marker_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "true")


@pytest.fixture(autouse=True)
def clear_context_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(context_cache, "CACHE_DATA", {})


@pytest.fixture()
def gae_testbed() -> Generator[testbed.Testbed, None, None]:
    tb = testbed.Testbed()
    tb.activate()
    yield tb
    tb.deactivate()


@pytest.fixture()
def ndb_stub(
    gae_testbed: testbed.Testbed,
    memcache_stub,
    monkeypatch: pytest.MonkeyPatch,
) -> testbed.datastore_file_stub.DatastoreFileStub:
    gae_testbed.init_datastore_v3_stub()

    # monkeypatch the ndb library to work with freezegun
    fake_datetime = getattr(freezegun_api, "FakeDatetime")
    v = getattr(datastore_types, "_VALIDATE_PROPERTY_VALUES", {})
    v[fake_datetime] = datastore_types.ValidatePropertyNothing
    monkeypatch.setattr(datastore_types, "_VALIDATE_PROPERTY_VALUES", v)

    p = getattr(datastore_types, "_PACK_PROPERTY_VALUES", {})
    p[fake_datetime] = datastore_types.PackDatetime
    monkeypatch.setattr(datastore_types, "_PACK_PROPERTY_VALUES", p)

    stub = gae_testbed.get_stub(testbed.DATASTORE_SERVICE_NAME)
    return stub


@pytest.fixture()
def taskqueue_stub(
    gae_testbed: testbed.Testbed,
) -> testbed.taskqueue_stub.TaskQueueServiceStub:
    gae_testbed.init_taskqueue_stub(root_path="src/")
    return gae_testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)


@pytest.fixture()
def memcache_stub(
    gae_testbed: testbed.Testbed,
    monkeypatch: pytest.MonkeyPatch,
) -> testbed.memcache_stub.MemcacheServiceStub:
    # for some reason, tests hang forever with a dangling thread if we don't set this
    monkeypatch.setattr(testbed.memcache_stub.MemcacheServiceStub, "THREADSAFE", False)
    gae_testbed.init_memcache_stub()
    stub = gae_testbed.get_stub(testbed.MEMCACHE_SERVICE_NAME)
    return stub


@pytest.fixture()
def ndb_context(ndb_stub):
    pass


@pytest.fixture()
def test_data_importer(ndb_stub) -> JsonDataImporter:
    return JsonDataImporter()


def clear_cached_queries() -> None:
    ndb.delete_multi(CachedQueryResult.query().fetch(keys_only=True))
