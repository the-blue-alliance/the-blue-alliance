from __future__ import annotations

import abc
import hashlib
import json
import logging
import pickle
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator, Generic, List, Optional, Set, Type, Union

import orjson
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.futures import TypedFuture
from backend.common.memcache import MemcacheClient
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.profiler import Span
from backend.common.queries.dict_converters.converter_base import ConverterBase
from backend.common.queries.types import DictQueryReturn, QueryReturn

# ContextVar holding a mapping of {query_cache_key: result_md5_hash} for CachedDatabaseQuery
# instances accessed within the active track_accessed_query_cache_keys() context:
# - Key (str): The query cache key (e.g., "team_query_frc254~dictv3.1" or "team_query_frc254").
# - Value (str): The deterministic 32-character hex MD5 hash of the query result.
accessed_query_cache_keys_ctx: ContextVar[Optional[Dict[str, str]]] = ContextVar[
    Optional[Dict[str, str]]
]("accessed_query_cache_keys_ctx", default=None)


@contextmanager
def track_accessed_query_cache_keys() -> Generator[Dict[str, str], None, None]:
    """
    Context manager to collect cache keys and MD5 result hashes of all CachedDatabaseQuery instances
    accessed during the block execution.

    Yields:
        Dict[str, str]: Mapping of query cache key (e.g., "team_query_frc254~dictv3.1")
        to the deterministic 32-character hex MD5 hash of its query result.
    """
    keys: Dict[str, str] = {}
    token = accessed_query_cache_keys_ctx.set(keys)
    try:
        yield keys
    finally:
        accessed_query_cache_keys_ctx.reset(token)


class DatabaseQuery(abc.ABC, Generic[QueryReturn, DictQueryReturn]):
    _query_args: Dict[str, Any]
    DICT_CONVERTER: Optional[Type[ConverterBase[QueryReturn, DictQueryReturn]]] = None

    def __init__(self, *args, **kwargs) -> None:
        self._query_args = kwargs

    @abc.abstractmethod
    def _query_async(self) -> TypedFuture[QueryReturn]: ...

    @ndb.tasklet
    def _do_query(self, *args, **kwargs) -> Generator[Any, Any, QueryReturn]:
        # This gives CachedDatabaseQuery a place to hook into
        with Span(f"{self.__class__.__name__}._query_async"):
            res = yield self._query_async(*args, **kwargs)
        return res

    @ndb.tasklet
    def _do_dict_query(
        self, _dict_version: ApiMajorVersion, *args, **kwargs
    ) -> Generator[Any, Any, Union[None, DictQueryReturn, List[DictQueryReturn]]]:
        # This gives CachedDatabaseQuery a place to hook into
        with Span(f"{self.__class__.__name__}._query_async"):
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
        fut: TypedFuture[DictQueryReturn] = self.fetch_dict_async(version)
        return fut.get_result()

    @ndb.tasklet
    def fetch_dict_async(
        self, version: ApiMajorVersion
    ) -> Generator[Any, Any, DictQueryReturn]:
        with Span("{}.fetch_dict_async".format(self.__class__.__name__)):
            query_result = yield self._do_dict_query(version, **self._query_args)
            return query_result


class CachedDatabaseQuery(
    DatabaseQuery[QueryReturn, DictQueryReturn],
    Generic[QueryReturn, DictQueryReturn],
    metaclass=abc.ABCMeta,
):
    DATABASE_QUERY_VERSION = 6
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
    def _compute_result_hash(cls, result: Any) -> str:
        with Span("query.compute_result_hash") as span:
            if result is None:
                span.set_label("result_type", "none")
                return "none"
            if isinstance(result, (bytes, bytearray)):
                span.set_label("result_type", "bytes")
                span.set_label("byte_size", str(len(result)))
                return hashlib.md5(result).hexdigest()
            if isinstance(result, str):
                span.set_label("result_type", "str")
                span.set_label("byte_size", str(len(result)))
                return hashlib.md5(result.encode("utf-8")).hexdigest()
            try:
                span.set_label("result_type", "json")
                serialized = orjson.dumps(result)
                span.set_label("byte_size", str(len(serialized)))
                return hashlib.md5(serialized).hexdigest()
            except (TypeError, orjson.JSONEncodeError):
                span.set_label("result_type", "pickle")
                pickled = pickle.dumps(result, protocol=4)
                span.set_label("byte_size", str(len(pickled)))
                return hashlib.md5(pickled).hexdigest()

    @classmethod
    def _record_accessed_cache_key(cls, cache_key: str, result: Any = None) -> None:
        accessed_keys = accessed_query_cache_keys_ctx.get()
        if accessed_keys is not None:
            accessed_keys[cache_key] = cls._compute_result_hash(result)

    @classmethod
    def delete_cache_multi(cls, cache_keys: Set[str]) -> None:
        all_cache_keys = []
        for cache_key in cache_keys:
            all_cache_keys.append(cache_key)
            if getattr(cls, "DICT_CONVERTER", None) is not None:
                all_cache_keys += [
                    cls._dict_cache_key(cache_key, valid_dict_version)
                    for valid_dict_version in set(ApiMajorVersion)
                ]
        logging.info("Deleting db query cache keys: {}".format(all_cache_keys))
        ndb.delete_multi(
            [ndb.Key(CachedQueryResult, cache_key) for cache_key in all_cache_keys]
        )
        try:
            memcache_client = MemcacheClient.get()
            memcache_client.delete_multi(
                [f"q_ver:{k}".encode("utf-8") for k in all_cache_keys]
            )
        except Exception as e:
            logging.warning(f"Failed to delete Memcache query version keys: {e}")

    @classmethod
    def get_query_class_by_name(
        cls, query_class_name: str
    ) -> Optional[Type[CachedDatabaseQuery]]:
        """Find a CachedDatabaseQuery subclass by name.

        Args:
            query_class_name: The name of the query class to find

        Returns:
            The query class if found, None otherwise
        """
        return next(
            (c for c in cls.__subclasses__() if c.__name__ == query_class_name),
            None,
        )

    @classmethod
    def validate_db_version_for_deletion(cls, db_version: int) -> None:
        """Validate that db_version is safe to delete.

        Rules:
        - Must be a positive integer
        - Must be less than (CURRENT_VERSION - 1), ensuring the prior version
          is kept as a buffer.

        Args:
            db_version: The database version to validate

        Raises:
            ValueError: If db_version is invalid or too recent
        """
        if db_version <= 0:
            raise ValueError(
                f"Cannot delete version {db_version}: must be a positive integer"
            )

        current_version = cls.DATABASE_QUERY_VERSION
        min_safe_current = current_version - 1
        if db_version >= min_safe_current:
            raise ValueError(
                f"Cannot delete version {db_version}: must be less than "
                f"{min_safe_current} (current version {current_version} must "
                "have at least one prior version as a buffer)"
            )

    @ndb.tasklet
    def _do_query(self, *args, **kwargs) -> Generator[Any, Any, QueryReturn]:
        cache_key = self.cache_key

        if not self.MODEL_CACHING_ENABLED:
            with Span(f"{self.__class__.__name__}._query_async"):
                result = yield self._query_async(*args, **kwargs)
            self._record_accessed_cache_key(cache_key, result)
            return result

        with Span("{}._do_query".format(self.__class__.__name__)):
            with Span("query.cache_lookup") as span:
                span.set_label("cache_key", cache_key)
                cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
                span.set_label("cache_hit", str(cached_query_result is not None))

            # Validate cached result for corruption and treat as cache miss if corrupted
            if (
                cached_query_result is not None
                and cached_query_result._validate_result_properties()
            ):
                logging.error(
                    "Corrupted cached result detected in _do_query; treating as cache miss. "
                    "cache_key=%s",
                    cache_key,
                )
                cached_query_result = None

            if cached_query_result is None:
                with Span(f"{self.__class__.__name__}._query_async"):
                    query_result = yield self._query_async(*args, **kwargs)
                if self.CACHE_WRITES_ENABLED:
                    try:
                        with Span("query.async_cache_write"):
                            yield CachedQueryResult(
                                id=cache_key, result=query_result
                            ).put_async()
                    except Exception as e:
                        logging.warning(
                            f"CachedQueryResult.put_async() failed: {cache_key}"
                        )
                        logging.exception(e)
                self._record_accessed_cache_key(cache_key, query_result)
                return query_result

            with Span("query.unpickle_models") as span:
                result = cached_query_result.result
                if isinstance(result, list):
                    span.set_label("result_count", str(len(result)))
                self._record_accessed_cache_key(cache_key, result)
                return result

    @ndb.tasklet
    def _do_dict_query(
        self, _dict_version: ApiMajorVersion, *args, **kwargs
    ) -> Generator[Any, Any, Union[None, DictQueryReturn, List[DictQueryReturn]]]:
        cache_key = (
            self.dict_cache_key(_dict_version)
            if self.DICT_CONVERTER is not None
            else self.cache_key
        )

        if not self.DICT_CACHING_ENABLED:
            with Span(f"{self.__class__.__name__}._query_async"):
                result = yield self._query_async(*args, **kwargs)
            self._record_accessed_cache_key(cache_key, result)
            return result

        with Span("{}._do_dict_query".format(self.__class__.__name__)):
            with Span("query.cache_lookup") as span:
                span.set_label("cache_key", cache_key)
                cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
                span.set_label("cache_hit", str(cached_query_result is not None))

            if cached_query_result is None:
                with Span(f"{self.__class__.__name__}._query_async"):
                    query_result = yield self._query_async(*args, **kwargs)

                # See https://github.com/facebook/pyre-check/issues/267
                converted_result = none_throws(self.DICT_CONVERTER)(  # pyre-ignore[45]
                    query_result
                ).convert(_dict_version)

                if self.CACHE_WRITES_ENABLED:
                    try:
                        with Span("query.async_cache_write"):
                            yield CachedQueryResult(
                                id=cache_key, result_dict=converted_result
                            ).put_async()
                    except Exception as e:
                        logging.warning(
                            f"CachedQueryResult.put_async() failed: {cache_key}"
                        )
                        logging.exception(e)
                self._record_accessed_cache_key(cache_key, converted_result)
                return converted_result

            values = getattr(cached_query_result, "_values", None)
            val = values.get(b"result_dict") if values else None
            if val is not None and not isinstance(
                val, (ndb.model._BaseValue, bytes, bytearray, str)
            ):
                result = cached_query_result.result_dict
                self._record_accessed_cache_key(cache_key, result)
                return result

            raw_bytes = cached_query_result.get_json_bytes()
            if raw_bytes is not None:
                try:
                    with Span("query.json_decode") as span:
                        span.set_label("byte_size", str(len(raw_bytes)))
                        result = orjson.loads(raw_bytes)
                        self._record_accessed_cache_key(cache_key, result)
                        return result
                except (orjson.JSONDecodeError, Exception) as e:
                    logging.warning(
                        f"orjson.loads failed for cache_key {cache_key}, falling back to result_dict: {e}"
                    )
            result = cached_query_result.result_dict
            self._record_accessed_cache_key(cache_key, result)
            return result

    def fetch_json(self, version: ApiMajorVersion) -> Optional[bytes]:
        fut: TypedFuture[Optional[bytes]] = self.fetch_json_async(version)
        return fut.get_result()

    @ndb.tasklet
    def fetch_json_async(
        self, version: ApiMajorVersion
    ) -> Generator[Any, Any, Optional[bytes]]:
        with Span("{}.fetch_json_async".format(self.__class__.__name__)):
            query_result = yield self._do_json_query(version, **self._query_args)
            return query_result

    @ndb.tasklet
    def _do_json_query(
        self, _dict_version: ApiMajorVersion, *args, **kwargs
    ) -> Generator[Any, Any, Optional[bytes]]:
        cache_key = (
            self.dict_cache_key(_dict_version)
            if self.DICT_CONVERTER is not None
            else self.cache_key
        )

        if not self.DICT_CACHING_ENABLED:
            dict_result = yield self._do_dict_query(_dict_version, *args, **kwargs)
            if dict_result is None:
                self._record_accessed_cache_key(cache_key, None)
                return None
            try:
                with Span("query.serialize_json"):
                    res = orjson.dumps(dict_result)
            except (orjson.JSONEncodeError, TypeError) as e:
                logging.warning(
                    f"orjson.dumps failed in _do_json_query, falling back to json.dumps: {e}"
                )
                res = json.dumps(dict_result, separators=(",", ":")).encode("utf-8")
            self._record_accessed_cache_key(cache_key, res)
            return res

        with Span("{}._do_json_query".format(self.__class__.__name__)):
            with Span("query.cache_lookup") as span:
                span.set_label("cache_key", cache_key)
                cached_query_result = yield CachedQueryResult.get_by_id_async(cache_key)
                span.set_label("cache_hit", str(cached_query_result is not None))

            if cached_query_result is None:
                with Span(f"{self.__class__.__name__}._query_async"):
                    query_result = yield self._query_async(*args, **kwargs)

                converted_result = none_throws(self.DICT_CONVERTER)(  # pyre-ignore[45]
                    query_result
                ).convert(_dict_version)

                cqr = CachedQueryResult(id=cache_key, result_dict=converted_result)
                if self.CACHE_WRITES_ENABLED:
                    try:
                        with Span("query.async_cache_write"):
                            yield cqr.put_async()
                    except Exception as e:
                        logging.warning(
                            f"CachedQueryResult.put_async() failed: {cache_key}"
                        )
                        logging.exception(e)

                if converted_result is None:
                    self._record_accessed_cache_key(cache_key, None)
                    return None

                res = cqr.get_json_bytes()
                if res is None:
                    try:
                        with Span("query.serialize_json"):
                            res = orjson.dumps(converted_result)
                    except (orjson.JSONEncodeError, TypeError) as e:
                        logging.warning(
                            f"orjson.dumps failed for cache_key {cache_key}, falling back to json.dumps: {e}"
                        )
                        res = json.dumps(
                            converted_result, separators=(",", ":")
                        ).encode("utf-8")
                self._record_accessed_cache_key(cache_key, res)
                return res

            raw_bytes = cached_query_result.get_json_bytes()
            if raw_bytes is not None:
                self._record_accessed_cache_key(cache_key, raw_bytes)
                return raw_bytes
            if cached_query_result.result_dict is None:
                self._record_accessed_cache_key(cache_key, None)
                return None
            try:
                with Span("query.serialize_json"):
                    res = orjson.dumps(cached_query_result.result_dict)
            except (orjson.JSONEncodeError, TypeError) as e:
                logging.warning(
                    f"orjson.dumps failed for cache_key {cache_key}, falling back to json.dumps: {e}"
                )
                res = json.dumps(
                    cached_query_result.result_dict, separators=(",", ":")
                ).encode("utf-8")
            self._record_accessed_cache_key(cache_key, res)
            return res
