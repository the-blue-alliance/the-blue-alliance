import base64
from typing import List

from google.cloud import ndb

from backend.common.futures import TypedFuture
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery, DatabaseQuery
from backend.common.queries.dict_converters.converter_base import ConverterBase


class DummyModel(ndb.Model):
    int_prop = ndb.IntegerProperty()


class DummyConverter(ConverterBase):
    pass


class DummyModelPointQuery(DatabaseQuery[DummyModel]):
    DICT_CONVERTER = DummyConverter

    @ndb.tasklet
    def _query_async(self, model_key: str) -> TypedFuture[DummyModel]:
        model = yield DummyModel.get_by_id_async(model_key)
        return model


class DummyModelRangeQuery(DatabaseQuery[List[DummyModel]]):
    DICT_CONVERTER = DummyConverter

    @ndb.tasklet
    def _query_async(self, min: int, max: int) -> TypedFuture[List[DummyModel]]:
        models = yield DummyModel.query(
            DummyModel.int_prop >= min, DummyModel.int_prop <= max
        ).fetch_async()
        return models


class CachedDummyModelRangeQuery(CachedDatabaseQuery[List[DummyModel]]):
    CACKE_KEY_FORMAT = "test_query_{min}_{max}"
    DICT_CONVERTER = DummyConverter
    CACHING_ENABLED = True

    @ndb.tasklet
    def _query_async(self, min: int, max: int) -> TypedFuture[List[DummyModel]]:
        models = yield DummyModel.query(
            DummyModel.int_prop >= min, DummyModel.int_prop <= max
        ).fetch_async()
        return models


def test_point_query_exists_sync() -> None:
    m = DummyModel(id="test")
    m.put()

    query = DummyModelPointQuery(model_key="test")
    result = query.fetch()
    assert result == m


def test_point_query_not_exists_sync() -> None:
    query = DummyModelPointQuery(model_key="test")
    result = query.fetch()
    assert result is None


def test_point_query_exists_async() -> None:
    m = DummyModel(id="test")
    m.put()

    query = DummyModelPointQuery(model_key="test")
    result_future = query.fetch_async()

    result = result_future.result()
    assert result == m


def test_point_query_not_exists_async() -> None:
    query = DummyModelPointQuery(model_key="test")
    result_future = query.fetch_async()

    result = result_future.result()
    assert result is None


def test_range_query_empty_sync() -> None:
    query = DummyModelRangeQuery(min=0, max=10)
    result = query.fetch()

    assert result == []


def test_range_query_empty_async() -> None:
    query = DummyModelRangeQuery(min=0, max=10)
    result_future = query.fetch_async()
    result = result_future.result()

    assert result == []


def test_range_query_with_data_sync() -> None:
    keys = ndb.put_multi([DummyModel(id=f"{i}", int_prop=i) for i in range(0, 5)])
    assert len(keys) == 5

    query = DummyModelRangeQuery(min=0, max=2)
    result = query.fetch()
    assert len(result) == 3


def test_range_query_with_data_async() -> None:
    keys = ndb.put_multi([DummyModel(id=f"{i}", int_prop=i) for i in range(0, 5)])
    assert len(keys) == 5

    query = DummyModelRangeQuery(min=0, max=2)
    result_future = query.fetch_async()
    result = result_future.result()
    assert len(result) == 3


def test_cached_query() -> None:
    keys = ndb.put_multi([DummyModel(id=f"{i}", int_prop=i) for i in range(0, 5)])
    assert len(keys) == 5

    query = CachedDummyModelRangeQuery(min=0, max=2)
    result = query.fetch()
    assert len(result) == 3

    # Now, verify the cached response exists
    assert CachedQueryResult.get_by_id(query.cache_key) is not None

    # And if we delete the underlying data out without clearing the cache, we should
    # still read a stale value
    [k.delete() for k in keys]
    assert ndb.get_multi(keys) == [None] * 5
    assert CachedQueryResult.get_by_id(query.cache_key) is not None

    query = CachedDummyModelRangeQuery(min=0, max=2)
    result = query.fetch()
    assert len(result) == 3


def test_py2_compatibility() -> None:
    """
    The purpose of this test is to make sure that py3 can deserialize cached query results
    pickled by the py2 version of the site.

    We do a bit of ndb hackery to test it. We start with a base64 encoded cached query, pulled
    from the datastore admin tool on prod. We then construct a dummy model (as the value of the
    property has already been pickled+compressed for storage) and then round-trip it to a datastore
    Entity, to force the ndb library to interpret the raw data as a different model type. This will
    let us prove we can deserialize it.

    If we do nothing, this fails because the import path of models has changed between py2/py3.
    It would fail with a message like:

    E       ModuleNotFoundError: No module named 'models'
    """

    class RawCachedQueryResult(ndb.Model):
        import pickletools

        result = ndb.Property()

        created = ndb.DateTimeProperty(auto_now_add=True)
        updated = ndb.DateTimeProperty(auto_now=True)

        @classmethod
        def _get_kind(cls):
            return "CachedQueryResult"

    raw_model = RawCachedQueryResult(
        id="py2_data",
        # This is a py2 serialized value, pulled from the datastore admin tool
        result=base64.b64decode(
            "eJyVkLFKxEAURZO4kphdUMKCMtUiKriwK4iI1tZ228owm3mJEzOT5M1kISlE7fQL/AELCz/JT7C1NjuITSqbV9x7OFzeg3dTubEsOOR6LoELFl7bW3nHj9XGgrqOk11lO/reLJlZzUos+OwWOZ4Mo01L7h8IpQ1Lkcl1m4gcqBGGKVFLI1JAfXZxejnCQzJMCgSRKnoHzcSZjknU53CXbNsZ1DQlUFC17FAv8PGchAgJIKgY9MSdHsX9VbodLIDJF9dPMF7rDMeQDBpg2Fmcdi/wiR8jMAO8C7aC1+/n94/PL6+NyIiDYSLXNNOFsjQh4xLFqoNpr7OmuuR/prdf05P7388s2fwH/A+AHg=="
        ),
    )
    raw_entity = ndb.model._entity_to_ds_entity(raw_model)  # pyre-ignore

    query_result = ndb.model._entity_from_ds_entity(  # pyre-ignore
        raw_entity, model_class=CachedQueryResult
    )

    assert query_result.result is None
