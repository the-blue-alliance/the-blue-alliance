import logging
from typing import Any, Generator, List

import pytest
from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery


class DummyModelWithRequiredProps(CachedModel):
    """Dummy model with required properties for testing validation."""

    required_prop = ndb.StringProperty(required=True)
    optional_prop = ndb.StringProperty()
    required_int = ndb.IntegerProperty(required=True)


class _DummyQueryClassA:
    CACHE_KEY_FORMAT = "dummy_query_a_{key}"


class _DummyQueryClassB:
    CACHE_KEY_FORMAT = "dummy_query_b_{x}_{y}"


class _DummyQueryClassDuplicatePrefix:
    CACHE_KEY_FORMAT = "dummy_query_a_{other}"


class _DummyCachedQueryForPurge(CachedDatabaseQuery[List[ndb.Model], None]):
    CACHE_KEY_FORMAT = "dummy_purge_query_{key}"
    CACHE_VERSION = 1
    DICT_CONVERTER = None

    @ndb.tasklet
    def _query_async(self, key: str) -> Generator[Any, Any, List[ndb.Model]]:  # type: ignore[override]
        future = ndb.Future()
        future.set_result([])
        models = yield future
        return models


def test_validate_result_properties_all_set(ndb_stub, caplog) -> None:
    """Test validation passes when all result model properties are set."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        result = CachedQueryResult(id="test_result", result=model)
        has_missing_required_properties = result._validate_result_properties()

    # No errors should be logged
    assert has_missing_required_properties is False
    assert len(caplog.records) == 0


def test_validate_result_properties_missing(ndb_stub, caplog) -> None:
    """Test validation logs error when result model has missing properties."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(id="test_model", required_prop="value")
        # required_int is not set (None)
        result = CachedQueryResult(id="test_result", result=model)
        has_missing_required_properties = result._validate_result_properties()

    # Should log an error for missing required_int
    assert has_missing_required_properties is True
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "Required properties not set" in error_message
    assert "DummyModelWithRequiredProps" in error_message
    assert "required_int" in error_message
    assert "Model key:" in error_message
    assert "CachedQueryResult key:" in error_message
    assert "Stack trace:" in error_message


def test_validate_result_properties_list_all_valid(ndb_stub, caplog) -> None:
    """Test validation passes when all models in result list are valid."""
    with caplog.at_level(logging.ERROR):
        models = [
            DummyModelWithRequiredProps(
                id="model1",
                required_prop="value1",
                required_int=42,
            ),
            DummyModelWithRequiredProps(
                id="model2",
                required_prop="value2",
                required_int=43,
            ),
        ]
        result = CachedQueryResult(id="test_result", result=models)
        has_missing_required_properties = result._validate_result_properties()

    # No errors should be logged
    assert has_missing_required_properties is False
    assert len(caplog.records) == 0


def test_validate_result_properties_list_with_invalid(ndb_stub, caplog) -> None:
    """Test validation logs error when a model in result list is invalid."""
    with caplog.at_level(logging.ERROR):
        models = [
            DummyModelWithRequiredProps(
                id="model1",
                required_prop="value1",
                required_int=42,
            ),
            DummyModelWithRequiredProps(id="model2", required_prop="value2"),
        ]
        result = CachedQueryResult(id="test_result", result=models)
        has_missing_required_properties = result._validate_result_properties()

    # Should log an error for the invalid model
    assert has_missing_required_properties is True
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "required_int" in error_message


def test_validate_result_properties_none_result(ndb_stub, caplog) -> None:
    """Test validation handles None result gracefully."""
    with caplog.at_level(logging.ERROR):
        result = CachedQueryResult(id="test_result", result=None)
        has_missing_required_properties = result._validate_result_properties()

    # No errors should be logged for None result
    assert has_missing_required_properties is False
    assert len(caplog.records) == 0


def test_pre_put_hook_raises_on_missing_properties(ndb_stub) -> None:
    """Test that _pre_put_hook raises BadValueError when result models have missing properties."""
    from google.appengine.api import datastore_errors

    model = DummyModelWithRequiredProps(id="test_model", required_prop="value")
    result = CachedQueryResult(id="test_result", result=model)
    # required_int is not set in the model
    with pytest.raises(datastore_errors.BadValueError) as exc_info:
        result.put()

    # Exception message should include model name, keys, and missing property
    error_msg = str(exc_info.value)
    assert "DummyModelWithRequiredProps" in error_msg
    assert "model key:" in error_msg
    assert "result key:" in error_msg
    assert "required_int" in error_msg


def test_pre_put_hook_allows_valid_result(ndb_stub) -> None:
    """Test that _pre_put_hook allows results with valid models."""
    model = DummyModelWithRequiredProps(
        id="test_model",
        required_prop="value",
        required_int=42,
    )
    result = CachedQueryResult(id="test_result", result=model)
    # Should not raise an exception
    result.put()
    # Verify the result was saved
    retrieved = CachedQueryResult.get_by_id("test_result")
    assert retrieved is not None
    assert retrieved.result is not None
    assert retrieved.result.required_prop == "value"
    assert retrieved.result.required_int == 42


def test_post_get_hook_allows_valid_result(ndb_stub, caplog) -> None:
    """Test that _post_get_hook allows valid results on fetch."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        result = CachedQueryResult(id="test_result", result=model)
        result.put()
        caplog.clear()

        # Now fetch the result
        _ = CachedQueryResult.get_by_id("test_result")

    # No errors should be logged
    assert len(caplog.records) == 0


def test_validate_result_properties_non_cached_model(ndb_stub, caplog) -> None:
    """Test validation skips non-CachedModel objects in result."""
    with caplog.at_level(logging.ERROR):
        # Store a plain dict (not a model) in result
        result = CachedQueryResult(id="test_result", result={"key": "value"})
        has_missing_required_properties = result._validate_result_properties()

    # No errors should be logged (non-models are skipped)
    assert has_missing_required_properties is False
    assert len(caplog.records) == 0


def test_validate_result_properties_mixed_types(ndb_stub, caplog) -> None:
    """Test validation handles mixed types in result list."""
    with caplog.at_level(logging.ERROR):
        models = [
            DummyModelWithRequiredProps(
                id="model1",
                required_prop="value1",
                required_int=42,
            ),
            {"key": "value"},  # Non-model object
        ]
        result = CachedQueryResult(id="test_result", result=models)
        has_missing_required_properties = result._validate_result_properties()

    # No errors should be logged (only valid models are checked)
    assert has_missing_required_properties is False
    assert len(caplog.records) == 0


def test_cache_key_prefix_from_format() -> None:
    cache_key_format = "event_teams_query_{event_key}_{year}"
    prefix = CachedQueryResult.cache_key_prefix_from_format(cache_key_format)
    assert prefix == "event_teams_query"


def test_cache_key_bounds_from_prefix() -> None:
    lower, upper = CachedQueryResult.cache_key_bounds_from_prefix("test_prefix")
    assert lower == "test_prefix_"
    assert upper == "test_prefix`"


def test_all_cache_key_prefixes_from_query_classes() -> None:
    prefixes = CachedQueryResult.all_cache_key_prefixes_from_query_classes(
        [_DummyQueryClassA, _DummyQueryClassB, _DummyQueryClassDuplicatePrefix]
    )
    assert prefixes == {"dummy_query_a", "dummy_query_b"}


def test_iter_keys_by_cache_key_prefix_filters(ndb_stub) -> None:
    # Matching prefix
    CachedQueryResult(id="test_prefix_a:1:5", result=None).put()
    CachedQueryResult(id="test_prefix_b:2:5", result=None).put()
    CachedQueryResult(id="test_prefix_b:2:5~dictv3.0", result=None).put()

    # Non-matching prefix and malformed keys
    CachedQueryResult(id="other_prefix_a:1:5", result=None).put()
    CachedQueryResult(id="testprefix_no_underscore:1:5", result=None).put()

    keys = {
        key.string_id()
        for key in CachedQueryResult.iter_keys_by_cache_key_prefix(
            "test_prefix", page_size=2
        )
    }

    assert "test_prefix_a:1:5" in keys
    assert "test_prefix_b:2:5" in keys
    assert "test_prefix_b:2:5~dictv3.0" in keys
    assert "other_prefix_a:1:5" not in keys
    assert "testprefix_no_underscore:1:5" not in keys


def test_iter_keys_by_cache_key_prefix_lexical_bounds(ndb_stub) -> None:
    # Inside the range
    CachedQueryResult(id="test_prefix_a:1:5", result=None).put()

    # Outside lower bound (no underscore after prefix)
    CachedQueryResult(id="test_prefix:1:5", result=None).put()

    # Outside upper bound (starts with prefix followed by backtick)
    CachedQueryResult(id="test_prefix`a:1:5", result=None).put()

    # Exact lower-bound anchor should be excluded by strict '>'
    CachedQueryResult(id="test_prefix_", result=None).put()

    keys = {
        key.string_id()
        for key in CachedQueryResult.iter_keys_by_cache_key_prefix(
            "test_prefix", page_size=10
        )
    }

    assert "test_prefix_a:1:5" in keys
    assert "test_prefix:1:5" not in keys
    assert "test_prefix`a:1:5" not in keys
    assert "test_prefix_" not in keys


def test_iter_keys_by_cache_key_prefix_paginates(ndb_stub) -> None:
    for i in range(0, 7):
        CachedQueryResult(id=f"test_page_{i}:1:5", result=None).put()

    keys = {
        key.string_id()
        for key in CachedQueryResult.iter_keys_by_cache_key_prefix(
            "test_page", page_size=3
        )
    }

    assert len(keys) == 7
    for i in range(0, 7):
        assert f"test_page_{i}:1:5" in keys


def test_db_version_from_key_string() -> None:
    assert CachedQueryResult.db_version_from_key_string("abc:2:5") == 5
    assert CachedQueryResult.db_version_from_key_string("abc:2:5~dictv3.0") == 5
    assert CachedQueryResult.db_version_from_key_string("abc:2:not_an_int") is None
    assert CachedQueryResult.db_version_from_key_string("abc:2") is None


def test_query_version_from_key_string() -> None:
    assert CachedQueryResult.query_version_from_key_string("abc:2:5") == 2
    assert CachedQueryResult.query_version_from_key_string("abc:2:5~dictv3.0") == 2
    assert CachedQueryResult.query_version_from_key_string("abc:not_an_int:5") is None
    assert CachedQueryResult.query_version_from_key_string("abc") is None


def test_purge_query_class_global_version_rejects_non_subclass(ndb_stub) -> None:
    with pytest.raises(TypeError):
        CachedQueryResult.purge_query_class_global_version(
            CachedQueryResult,
            db_version=5,
            page_size=100,
            delete_batch_size=50,
        )


def test_purge_query_class_global_version_rejects_bad_batch_sizes(ndb_stub) -> None:
    with pytest.raises(ValueError):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=5,
            page_size=0,
            delete_batch_size=50,
        )

    with pytest.raises(ValueError):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=5,
            page_size=100,
            delete_batch_size=0,
        )


def test_purge_query_class_global_version_deletes_only_matching_version(
    ndb_stub,
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    db_version = current_v - 2  # Must be < current_v - 1 to pass validation

    old_key = f"dummy_purge_query_a:1:{db_version}"
    old_dict_key = f"dummy_purge_query_b:1:{db_version}~dictv3.0"
    new_key = f"dummy_purge_query_c:1:{current_v}"
    other_prefix_key = "dummy_other_query_z:1:4"

    CachedQueryResult(id=old_key, result=None).put()
    CachedQueryResult(id=old_dict_key, result=None).put()
    CachedQueryResult(id=new_key, result=None).put()
    CachedQueryResult(id=other_prefix_key, result=None).put()

    deleted = CachedQueryResult.purge_query_class_global_version(
        _DummyCachedQueryForPurge,
        db_version=db_version,
        page_size=10,
        delete_batch_size=2,
    )

    assert deleted == 2
    assert CachedQueryResult.get_by_id(old_key) is None
    assert CachedQueryResult.get_by_id(old_dict_key) is None
    assert CachedQueryResult.get_by_id(new_key) is not None
    assert CachedQueryResult.get_by_id(other_prefix_key) is not None


def test_purge_query_class_global_version_rejects_non_positive_version(
    ndb_stub,
) -> None:
    """Test that version 0 and negative versions are rejected."""
    with pytest.raises(ValueError, match="must be a positive integer"):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=0,
            page_size=100,
            delete_batch_size=50,
        )

    with pytest.raises(ValueError, match="must be a positive integer"):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=-1,
            page_size=100,
            delete_batch_size=50,
        )


def test_purge_query_class_global_version_rejects_recent_version(
    ndb_stub,
) -> None:
    """Test that versions >= (CURRENT_VERSION - 1) are rejected."""
    current_version = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    min_safe_current = current_version - 1

    # Try to delete the current version (should fail)
    with pytest.raises(
        ValueError,
        match=f"must be less than {min_safe_current}",
    ):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=current_version,
            page_size=100,
            delete_batch_size=50,
        )

    # Try to delete the prior version (should fail)
    with pytest.raises(
        ValueError,
        match=f"must be less than {min_safe_current}",
    ):
        CachedQueryResult.purge_query_class_global_version(
            _DummyCachedQueryForPurge,
            db_version=min_safe_current,
            page_size=100,
            delete_batch_size=50,
        )

    # Older version should succeed (db_version = current - 2)
    deleted = CachedQueryResult.purge_query_class_global_version(
        _DummyCachedQueryForPurge,
        db_version=current_version - 2,
        page_size=100,
        delete_batch_size=50,
    )
    assert deleted == 0  # No entries created, but validation passed
