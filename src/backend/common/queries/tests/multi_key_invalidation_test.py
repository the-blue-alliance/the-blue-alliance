from typing import Any, Generator, List, TypedDict

import pytest
from flask import Flask, g
from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.flask_cache import configure_flask_cache
from backend.common.memcache import MemcacheClient
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.converter_base import ConverterBase


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


class DummyItem(ndb.Model):
    name = ndb.StringProperty()
    val = ndb.IntegerProperty()


class DummyDict(TypedDict):
    name: str
    val: int


class DummyConverter(ConverterBase):
    SUBVERSIONS = {
        ApiMajorVersion.API_V3: 0,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[DummyItem], version: ApiMajorVersion
    ) -> List[DummyDict]:
        return [cls.converter_v3(m) for m in model_list]

    @classmethod
    def converter_v3(cls, model: DummyItem) -> DummyDict:
        return {"name": model.name, "val": model.val}


class DummyQueryA(CachedDatabaseQuery[List[DummyItem], List[DummyDict]]):
    DICT_CONVERTER = DummyConverter
    CACHE_KEY_FORMAT = "query_a_{key}"
    CACHE_VERSION = 1

    @ndb.tasklet
    def _query_async(self, key: str) -> Generator[Any, Any, List[DummyItem]]:
        item = yield DummyItem.get_by_id_async(key)
        return [DummyItem(name="A", val=1)] if item is None else [item]


class DummyQueryB(CachedDatabaseQuery[List[DummyItem], List[DummyDict]]):
    DICT_CONVERTER = DummyConverter
    CACHE_KEY_FORMAT = "query_b_{key}"
    CACHE_VERSION = 1

    @ndb.tasklet
    def _query_async(self, key: str) -> Generator[Any, Any, List[DummyItem]]:
        item = yield DummyItem.get_by_id_async(key)
        return [DummyItem(name="B", val=2)] if item is None else [item]


def test_query_access_tracked_in_request_context(app: Flask, ndb_stub) -> None:
    with app.test_request_context("/test"):
        assert getattr(g, "accessed_query_keys", None) is None
        qa = DummyQueryA(key="foo")
        qa.fetch_dict(ApiMajorVersion.API_V3)
        accessed = getattr(g, "accessed_query_keys", set())
        assert qa.cache_key in accessed

        qb = DummyQueryB(key="bar")
        qb.fetch_dict(ApiMajorVersion.API_V3)
        assert qb.cache_key in accessed
        assert len(accessed) == 2


def test_delete_cache_multi_increments_generation_tokens(
    ndb_stub, memcache_stub
) -> None:
    mc = MemcacheClient.get()
    key = "query_a_foo:1:0"
    gen_key = f"gen:{key}".encode()

    assert mc.get(gen_key) is None

    # First invalidation sets to timestamp token
    DummyQueryA.delete_cache_multi({key})
    val1 = mc.get(gen_key)
    assert isinstance(val1, int) and val1 > 0

    # Second invalidation increments it
    DummyQueryA.delete_cache_multi({key})
    val2 = mc.get(gen_key)
    assert val2 == val1 + 1

    # Dict cache keys should NOT be stored in Memcache
    dict_key = DummyQueryA._dict_cache_key(key, ApiMajorVersion.API_V3)
    assert mc.get(f"gen:{dict_key}".encode()) is None


def test_query_access_tracked_for_fetch_and_fetch_json(app: Flask, ndb_stub) -> None:
    with app.test_request_context("/test"):
        qa = DummyQueryA(key="foo")
        qa.fetch()
        accessed = getattr(g, "accessed_query_keys", set())
        assert qa.cache_key in accessed

        qb = DummyQueryB(key="bar")
        qb.fetch_json(ApiMajorVersion.API_V3)
        assert qb.cache_key in accessed
        assert len(accessed) == 2


def test_multikey_etag_and_fast_304(app: Flask, ndb_stub, memcache_stub) -> None:
    configure_flask_cache(app)

    handler_calls = 0

    @app.route("/compound")
    @cached_public
    def compound_endpoint():
        nonlocal handler_calls
        handler_calls += 1
        qa = DummyQueryA(key="alpha")
        qb = DummyQueryB(key="beta")
        res_a = qa.fetch_dict(ApiMajorVersion.API_V3)
        res_b = qb.fetch_dict(ApiMajorVersion.API_V3)
        return {"a": res_a, "b": res_b}

    client = app.test_client()

    # 1. First request (cold miss) -> runs handler and mints composite ETag
    resp1 = client.get("/compound")
    assert resp1.status_code == 200
    assert handler_calls == 1
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert etag.startswith('"') and etag.endswith('"')

    # Verify generation tokens were initialized to integer timestamps in memcache
    mc = MemcacheClient.get()
    qa_gen = mc.get(f"gen:{DummyQueryA(key='alpha').cache_key}".encode())
    qb_gen = mc.get(f"gen:{DummyQueryB(key='beta').cache_key}".encode())
    assert isinstance(qa_gen, int) and qa_gen > 0
    assert isinstance(qb_gen, int) and qb_gen > 0

    # 2. Second request with If-None-Match -> should return 304 fast-path
    resp2 = client.get("/compound", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    assert resp2.headers.get("ETag") == etag
    assert "Cache-Control" in resp2.headers
    # Handler should NOT have been called again!
    assert handler_calls == 1

    # 2b. Revalidation with weak ETag (common with CDNs/proxies)
    resp_weak = client.get("/compound", headers={"If-None-Match": f"W/{etag}"})
    assert resp_weak.status_code == 304
    assert handler_calls == 1

    # 3. Invalidate one query (QueryA)
    DummyQueryA.delete_cache_multi({DummyQueryA(key="alpha").cache_key})
    qa_gen_after = mc.get(f"gen:{DummyQueryA(key='alpha').cache_key}".encode())
    assert qa_gen_after == qa_gen + 1

    # 4. Request with old ETag -> generation mismatch, handler executes to fetch fresh data
    resp3 = client.get("/compound", headers={"If-None-Match": etag})
    assert resp3.status_code == 200
    assert handler_calls == 2
    new_etag = resp3.headers.get("ETag")
    assert new_etag is not None
    assert new_etag != etag

    # 5. Request with new ETag -> should return 304 fast-path again
    resp4 = client.get("/compound", headers={"If-None-Match": new_etag})
    assert resp4.status_code == 304
    assert handler_calls == 2

    # 6. Response cache expiration simulation:
    # Delete the cached response body in Flask-Cache to simulate 61s TTL expiration.
    # Because deps:{cache_key} lives for 1 day, fast-path 304 continues to succeed without running the handler.
    # Find the view cache key in Flask-Caching and remove only the response body:
    with app.test_request_context("/compound"):
        view_func = app.view_functions["compound_endpoint"]
        # The cache key used by flask_caching
        view_key = "/compound"
        app.cache.delete(view_key)

    resp5 = client.get("/compound", headers={"If-None-Match": new_etag})
    assert resp5.status_code == 304
    assert handler_calls == 2  # Handler was NOT called!

    # 7. Memcache key eviction simulation:
    # If gen:{key} is evicted from Memcache, the server detects mismatch/missing and re-runs handler.
    mc.delete(f"gen:{DummyQueryA(key='alpha').cache_key}".encode())
    resp6 = client.get("/compound", headers={"If-None-Match": new_etag})
    assert resp6.status_code == 200
    assert handler_calls == 3
