import logging
import traceback
from typing import Any, Generator, Iterable, Optional

from google.appengine.ext import ndb


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """

    # Only one of result or result_dict should ever be populated for one model
    result = ndb.PickleProperty(compressed=True)  # Raw models
    result_dict = ndb.JsonProperty()  # Dict version of models

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @staticmethod
    def cache_key_prefix_from_format(cache_key_format: str) -> str:
        cache_key_splits = cache_key_format.split("_")
        cache_key_prefix_parts = []
        for part in cache_key_splits:
            if "{" not in part and "}" not in part:
                cache_key_prefix_parts.append(part)
        return "_".join(cache_key_prefix_parts)

    @classmethod
    def all_cache_key_prefixes_from_query_classes(
        cls, query_classes: Iterable[Any]
    ) -> set[str]:
        return {
            cls.cache_key_prefix_from_format(query_class.CACHE_KEY_FORMAT)
            for query_class in query_classes
        }

    @staticmethod
    def cache_key_bounds_from_prefix(cache_key_prefix: str) -> tuple[str, str]:
        # Query keys in the lexical range ["{prefix}_*"].
        #
        # Lower bound: > "{prefix}_" to skip the synthetic anchor key itself.
        # Upper bound: < "{prefix}`" where '`' (ASCII 96) is the next character
        # after '_' (ASCII 95), so all strings beginning with "{prefix}_" match.
        lower_bound = cache_key_prefix + "_"
        upper_bound = cache_key_prefix + "`"
        return lower_bound, upper_bound

    @classmethod
    def query_by_cache_key_prefix(cls, cache_key_prefix: str) -> ndb.Query:
        lower_bound, upper_bound = cls.cache_key_bounds_from_prefix(cache_key_prefix)
        return (
            cls.query()
            .filter(cls.key > ndb.Key(cls, lower_bound))  # pyre-ignore[58]
            .filter(cls.key < ndb.Key(cls, upper_bound))  # pyre-ignore[58]
        )

    @classmethod
    def iter_keys_by_cache_key_prefix(
        cls, cache_key_prefix: str, page_size: int
    ) -> Generator[ndb.Key, None, None]:
        query = cls.query_by_cache_key_prefix(cache_key_prefix)

        cursor = None
        more = True
        while more:
            keys, cursor, more = query.fetch_page(
                page_size, start_cursor=cursor, keys_only=True
            )
            for key in keys:
                yield key

    @staticmethod
    def db_version_from_key_string(key_string: str) -> Optional[int]:
        parts = key_string.split(":")
        if len(parts) < 3:
            return None
        db_version_str = parts[2].split("~")[0]
        try:
            return int(db_version_str)
        except ValueError:
            return None

    @staticmethod
    def query_version_from_key_string(key_string: str) -> Optional[int]:
        parts = key_string.split(":")
        if len(parts) < 2:
            return None
        try:
            return int(parts[1])
        except ValueError:
            return None

    @classmethod
    def purge_query_class_global_version(
        cls,
        query_class: Any,
        db_version: int,
        page_size: int,
        delete_batch_size: int,
    ) -> int:
        from backend.common.queries.database_query import CachedDatabaseQuery

        if not isinstance(query_class, type) or not issubclass(
            query_class, CachedDatabaseQuery
        ):
            raise TypeError("query_class must be a CachedDatabaseQuery subclass")

        if page_size <= 0:
            raise ValueError("page_size must be > 0")
        if delete_batch_size <= 0:
            raise ValueError("delete_batch_size must be > 0")

        # Validate db_version for safe deletion
        if db_version <= 0:
            raise ValueError(
                f"Cannot delete version {db_version}: must be a positive integer"
            )

        current_version = CachedDatabaseQuery.DATABASE_QUERY_VERSION
        min_safe_current = current_version - 1
        if db_version >= min_safe_current:
            raise ValueError(
                f"Cannot delete version {db_version}: must be less than "
                f"{min_safe_current} (current version {current_version} must "
                "have at least one prior version as a buffer)"
            )

        cache_key_prefix = cls.cache_key_prefix_from_format(
            query_class.CACHE_KEY_FORMAT
        )

        deleted = 0
        keys_to_delete = []
        for key in cls.iter_keys_by_cache_key_prefix(cache_key_prefix, page_size):
            key_string = key.string_id()
            if key_string is None:
                continue
            key_db_version = cls.db_version_from_key_string(key_string)
            if key_db_version is None or key_db_version != db_version:
                continue

            keys_to_delete.append(key)
            if len(keys_to_delete) >= delete_batch_size:
                deleted += len(keys_to_delete)
                ndb.delete_multi(keys_to_delete)
                keys_to_delete = []

        if keys_to_delete:
            deleted += len(keys_to_delete)
            ndb.delete_multi(keys_to_delete)

        return deleted

    def _validate_result_properties(self) -> bool:
        """
        Validates that all required properties on models in the result field are set.
        Logs an error with stack trace and model key if validation fails.

        Returns True when one or more models have missing required properties,
        otherwise False.
        """
        if self.result is None:
            return False

        # Handle both single model and list of models
        models_to_check = []
        if isinstance(self.result, list):
            models_to_check = self.result
        else:
            models_to_check = [self.result]

        for model in models_to_check:
            # Skip non-CachedModel objects and models without _properties
            if not hasattr(model, "_properties"):
                continue

            missing_properties = []
            for prop_name, prop in model._properties.items():
                # Check if property is required and value is None
                if hasattr(prop, "_required") and prop._required:
                    value = getattr(model, prop_name, None)
                    if value is None:
                        missing_properties.append(prop_name)

            # Log error if any required properties are missing
            if missing_properties:
                stack_trace = "".join(traceback.format_stack())
                model_key = (
                    model.key.urlsafe() if model.key else "No key (unsaved model)"
                )
                cached_result_key = (
                    self.key.urlsafe() if self.key else "No key (unsaved result)"
                )
                logging.error(
                    f"Required properties not set on {model.__class__.__name__} "
                    f"in CachedQueryResult: {', '.join(missing_properties)}\n"
                    f"Model key: {model_key}\n"
                    f"CachedQueryResult key: {cached_result_key}\n"
                    f"Stack trace:\n{stack_trace}"
                )
                return True

        return False

    def _pre_put_hook(self) -> None:
        """
        Hook called before the entity is written to the datastore.
        Raises BadValueError if any required properties are missing in cached models.
        """
        if self.result is None:
            return

        from google.appengine.api import datastore_errors

        # Handle both single model and list of models
        models_to_check = []
        if isinstance(self.result, list):
            models_to_check = self.result
        else:
            models_to_check = [self.result]

        for model in models_to_check:
            # Skip non-CachedModel objects and models without _properties
            if not hasattr(model, "_properties"):
                continue

            missing_properties = []
            for prop_name, prop in model._properties.items():
                # Check if property is required and value is None
                if hasattr(prop, "_required") and prop._required:
                    value = getattr(model, prop_name, None)
                    if value is None:
                        missing_properties.append(prop_name)

            # Raise exception if any required properties are missing
            if missing_properties:
                model_key = (
                    model.key.urlsafe() if model.key else "No key (unsaved model)"
                )
                cached_result_key = (
                    self.key.urlsafe() if self.key else "No key (unsaved result)"
                )
                raise datastore_errors.BadValueError(
                    f"Required properties not set on {model.__class__.__name__} "
                    f"in CachedQueryResult (model key: {model_key}, "
                    f"result key: {cached_result_key}): "
                    f"{', '.join(missing_properties)}"
                )

    @classmethod
    def _post_get_hook(cls, key: ndb.Key, future: Any) -> None:
        """
        Hook called after the entity is retrieved from the datastore.
        Validates all required properties on models in the result field.
        """
        entity = future.get_result()
        # Check if the method exists before calling. NDB's hook system can invoke
        # this on different model types (especially when tests manipulate NDB's kind map).
        if entity and hasattr(entity, "_validate_result_properties"):
            entity._validate_result_properties()
