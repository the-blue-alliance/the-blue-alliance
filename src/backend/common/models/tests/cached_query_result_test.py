import logging

import pytest
from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.cached_query_result import CachedQueryResult


class DummyModelWithRequiredProps(CachedModel):
    """Dummy model with required properties for testing validation."""

    required_prop = ndb.StringProperty(required=True)
    optional_prop = ndb.StringProperty()
    required_int = ndb.IntegerProperty(required=True)


def test_validate_result_properties_all_set(ndb_stub, caplog) -> None:
    """Test validation passes when all result model properties are set."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        result = CachedQueryResult(id="test_result", result=model)
        result._validate_result_properties()

    # No errors should be logged
    assert len(caplog.records) == 0


def test_validate_result_properties_missing(ndb_stub, caplog) -> None:
    """Test validation logs error when result model has missing properties."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(id="test_model", required_prop="value")
        # required_int is not set (None)
        result = CachedQueryResult(id="test_result", result=model)
        result._validate_result_properties()

    # Should log an error for missing required_int
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
        result._validate_result_properties()

    # No errors should be logged
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
        result._validate_result_properties()

    # Should log an error for the invalid model
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "required_int" in error_message


def test_validate_result_properties_none_result(ndb_stub, caplog) -> None:
    """Test validation handles None result gracefully."""
    with caplog.at_level(logging.ERROR):
        result = CachedQueryResult(id="test_result", result=None)
        result._validate_result_properties()

    # No errors should be logged for None result
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
        result._validate_result_properties()

    # No errors should be logged (non-models are skipped)
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
        result._validate_result_properties()

    # No errors should be logged (only valid models are checked)
    assert len(caplog.records) == 0
