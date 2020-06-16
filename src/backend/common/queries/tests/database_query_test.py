from typing import List

from google.cloud import ndb

from backend.common.futures import TypedFuture
from backend.common.queries.database_query import DatabaseQuery
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
