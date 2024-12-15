from __future__ import annotations

import abc
import logging
from typing import Any, Dict, Generator, Generic, List, Optional, Set, Type, Union

from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.futures import TypedFuture
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.profiler import Span
from backend.common.queries.dict_converters.converter_base import ConverterBase
from backend.common.queries.types import DictQueryReturn, QueryReturn


class DatabaseQuery(abc.ABC, Generic[QueryReturn, DictQueryReturn]):
    _query_args: Dict[str, Any]
    DICT_CONVERTER: Optional[Type[ConverterBase[QueryReturn, DictQueryReturn]]]

    def __init__(self, *args, **kwargs) -> None:
        self._query_args = kwargs

    @abc.abstractmethod
    def _query_async(self) -> TypedFuture[QueryReturn]: ...

    @ndb.tasklet
    def _do_query(self, *args, **kwargs) -> Generator[Any, Any, QueryReturn]:
        # This gives CachedDatabaseQuery a place to hook into
        res = yield self._query_async(*args, **kwargs)
        return res

    @ndb.tasklet
    def _do_dict_query(
        self, _dict_version: ApiMajorVersion, *args, **kwargs
    ) -> Generator[Any, Any, Union[None, DictQueryReturn, List[DictQueryReturn]]]:
        # This gives CachedDatabaseQuery a place to hook into
        res = yield self._query_async(*args, **kwargs)

        if self.DICT_CONVERTER is None:
            raise Exception(
                f"{self.__class__.__name__} does not provide a Dict converter!"
            )

        # See https://github.com/facebook/pyre-check/issues/267
        return self.DICT_CONVERTER(res).convert(_dict_version)  # pyre-ignore[45]

    def fetch(self) -> QueryReturn:
        return self.fetch_async().get_result()

    @ndb.tasklet
    def fetch_async(self) -> Generator[Any, Any, QueryReturn]:
        with Span("{}.fetch_async".format(self.__class__.__name__)):
            query_result = yield self._do_query(**self._query_args)
            return query_result

    def fetch_dict(self, version: ApiMajorVersion) -> DictQueryReturn:
        return self.fetch_dict_async(version).get_result()

    @ndb.tasklet
    def fetch_dict_async(
        self, version: ApiMajorVersion
    ) -> Generator[Any, Any, DictQueryReturn]:
        with Span("{}.fetch_dict_async".format(self.__class__.__name__)):
            query_result = yield self._do_dict_query(version, **self._query_args)
            return query_result


class CachedDatabaseQuery(
    DatabaseQuery, Generic[QueryReturn, DictQueryReturn], metaclass=abc.ABCMeta
):
    DATABASE_QUERY_VERSION = 4
    BASE_CACHE_KEY_FORMAT: str = (
        "{}:{}:{}"  # (partial_cache_key, cache_version, database_query_version)
    )
    CACHE_KEY_FORMAT: str = ""
    CACHE_VERSION: int = 0
    DICT_CACHING_ENABLED: bool = True
    MODEL_CACHING_ENABLED: bool = True
    CACHE_WRITES_ENABLED: bool = True
    _cache_key: Optional[str] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def cache_key(self) -> str:
        if not self._cache_key:
            self._cache_key = self.BASE_CACHE_KEY_FORMAT.format(
                self.CACHE_KEY_FORMAT.format(**self._query_args),
                self.CACHE_VERSION,
                self.DATABASE_QUERY_VERSION,
            )
        return none_throws(self._cache_key)

    def dict_cache_key(self, dict_version: ApiMajorVersion) -> str:
        return self._dict_cache_key(self.cache_key, dict_version)

    @classmethod
    def _dict_cache_key(cls, cache_key: str, dict_version: ApiMajorVersion) -> str:
        subvserion = none_throws(cls.DICT_CONVERTER).SUBVERSIONS[dict_version]
        return f"{cache_key}~dictv{dict_version}.{subvserion}"

    @classmethod
    def delete_cache_multi(cls, cache_keys: Set[str]) -> None:
        all_cache_keys = []
        for cache_key in cache_keys:
            all_cache_keys.append(cache_key)
            if cls.DICT_CONVERTER is not None:
                all_cache_keys += [
                    cls._dict_cache_key(cache_key, valid_dict_version)
                    for valid_dict_version in set(ApiMajorVersion)
                ]
        logging.info("Deleting db query cache keys: {}".format(all_cache_keys))
        ndb.delete_multi(
            [ndb.Key(CachedQueryResult, cache_key) for cache_key in all_cache_keys]
        )

    @ndb.tasklet
    def _do_query(self, *args, **kwargs) -> Generator[Any, Any, QueryReturn]:
        if not self.MODEL_CACHING_ENABLED:
            result = yield self._query_async(*args, **kwargs)
            return result

        with Span("{}._do_query".format(self.__class__.__name__)):
            cache_key = self.cache_key
            cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
            if cached_query_result is None:
                query_result = yield self._query_async(*args, **kwargs)
                if self.CACHE_WRITES_ENABLED:
                    try:
                        yield CachedQueryResult(
                            id=cache_key, result=query_result
                        ).put_async()
                    except BadRequestError as e:
                        logging.warning("CachedQueryResult.put_async() failed!")
                        logging.exception(e)
                return query_result
            return cached_query_result.result

    @ndb.tasklet
    def _do_dict_query(
        self, _dict_version: ApiMajorVersion, *args, **kwargs
    ) -> Generator[Any, Any, Union[None, DictQueryReturn, List[DictQueryReturn]]]:
        if not self.DICT_CACHING_ENABLED:
            result = yield self._query_async(*args, **kwargs)
            return result

        with Span("{}._do_dict_query".format(self.__class__.__name__)):
            cache_key = self.dict_cache_key(_dict_version)
            cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
            if cached_query_result is None:
                query_result = yield self._query_async(*args, **kwargs)

                # See https://github.com/facebook/pyre-check/issues/267
                converted_result = none_throws(self.DICT_CONVERTER)(  # pyre-ignore[45]
                    query_result
                ).convert(_dict_version)

                if self.CACHE_WRITES_ENABLED:
                    try:
                        yield CachedQueryResult(
                            id=cache_key, result_dict=converted_result
                        ).put_async()
                    except BadRequestError as e:
                        logging.warning("CachedQueryResult.put_async() failed!")
                        logging.exception(e)
                return converted_result
            return cached_query_result.result_dict
