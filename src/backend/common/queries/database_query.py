from __future__ import annotations

import abc
from typing import Any, Dict, Generic, Optional, Set, Type

from google.cloud import ndb
from pyre_extensions import safe_cast

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.futures import TypedFuture
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.profiler import Span
from backend.common.queries.dict_converters.converter_base import ConverterBase
from backend.common.queries.exceptions import DoesNotExistException
from backend.common.queries.types import QueryReturn


class DatabaseQuery(abc.ABC, Generic[QueryReturn]):
    _query_args: Dict[str, Any]
    DICT_CONVERTER: Type[ConverterBase[QueryReturn]] = ConverterBase

    def __init__(self, *args, **kwargs) -> None:
        self._query_args = kwargs

    @abc.abstractmethod
    def _query_async(self) -> TypedFuture[QueryReturn]:
        ...

    def _do_query(self, *args, **kwargs) -> TypedFuture[QueryReturn]:
        # This gives CachedDatabaseQuery a place to hook into
        return self._query_async(*args, **kwargs)

    def fetch(self) -> QueryReturn:
        return self.fetch_async().get_result()

    @ndb.tasklet
    def fetch_async(self) -> TypedFuture[QueryReturn]:
        with Span("{}.fetch_async".format(self.__class__.__name__)):
            query_result = yield self._do_query(**self._query_args)
            return safe_cast(TypedFuture[QueryReturn], query_result)

    def fetch_dict(self, version: ApiMajorVersion) -> Dict:
        return self.fetch_dict_async(version).get_result()

    @ndb.tasklet
    def fetch_dict_async(self, version: ApiMajorVersion) -> TypedFuture[Dict]:
        query_result = yield self.fetch_async()
        if query_result is None:
            raise DoesNotExistException()
        # See https://github.com/facebook/pyre-check/issues/267
        res = self.DICT_CONVERTER(  # pyre-ignore[45]
            safe_cast(QueryReturn, query_result)
        ).convert(version)
        return safe_cast(TypedFuture[Dict], res)


class CachedDatabaseQuery(DatabaseQuery, Generic[QueryReturn]):
    DATABASE_QUERY_VERSION = 0
    BASE_CACHE_KEY_FORMAT: str = (
        "{}:{}:{}"  # (partial_cache_key, cache_version, database_query_version)
    )
    CACHE_KEY_FORMAT: str = ""
    CACHE_VERSION: int = 0
    CACHING_ENABLED: bool = False
    _cache_key: Optional[str] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def cache_key(self) -> Optional[str]:
        if not self._cache_key:
            self._cache_key = self.BASE_CACHE_KEY_FORMAT.format(
                self.CACHE_KEY_FORMAT.format(**self._query_args),
                self.CACHE_VERSION,
                self.DATABASE_QUERY_VERSION,
            )
        return self._cache_key

    @ndb.tasklet
    def _do_query(self, *args, **kwargs) -> TypedFuture[QueryReturn]:
        if not self.CACHING_ENABLED:
            result = yield self._query_async(*args, **kwargs)
            return result  # pyre-ignore[7]

        cache_key = self.cache_key
        cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
        if cached_query_result is None:
            query_result = yield self._query_async(*args, **kwargs)
            yield CachedQueryResult(id=cache_key, result=query_result).put_async()
            return query_result  # pyre-ignore[7]
        return cached_query_result.result

    @classmethod
    def _event_affected_queries(
        cls, event_key: EventKey, year: Year, district_key: Optional[DistrictKey]
    ) -> Set[CachedDatabaseQuery]:
        return set()

    @classmethod
    def _eventteam_affected_queries(
        cls, event_key: EventKey, team_key: TeamKey, year: Year
    ) -> Set[CachedDatabaseQuery]:
        return set()

    @classmethod
    def _team_affected_queries(cls, team_key: TeamKey) -> Set[CachedDatabaseQuery]:
        return set()
