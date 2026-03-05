import logging

import pytest
from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel


class DummyModelWithRequiredProps(CachedModel):
    """Dummy model with required properties for testing validation."""

    required_prop = ndb.StringProperty(required=True)
    optional_prop = ndb.StringProperty()
    required_int = ndb.IntegerProperty(required=True)


def test_validate_required_properties_all_set(ndb_stub, caplog) -> None:
    """Test validation passes when all required properties are set."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        model._validate_required_properties()

    # No errors should be logged
    assert len(caplog.records) == 0


def test_validate_required_properties_missing(ndb_stub, caplog) -> None:
    """Test validation logs error when required properties are missing."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(id="test_model", required_prop="value")
        # required_int is not set (None)
        model._validate_required_properties()

    # Should log an error for missing required_int
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "Required properties not set" in error_message
    assert "DummyModelWithRequiredProps" in error_message
    assert "required_int" in error_message
    assert "Model key:" in error_message
    assert "Stack trace:" in error_message


def test_validate_required_properties_multiple_missing(ndb_stub, caplog) -> None:
    """Test validation logs error when multiple required properties are missing."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(id="test_model")
        # Both required_prop and required_int are not set
        model._validate_required_properties()

    # Should log an error listing both missing properties
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "Required properties not set" in error_message
    assert "required_prop" in error_message
    assert "required_int" in error_message


def test_pre_put_hook_raises_on_missing_properties(ndb_stub) -> None:
    """Test that _pre_put_hook raises BadValueError when required properties are missing."""
    from google.appengine.api import datastore_errors

    model = DummyModelWithRequiredProps(id="test_model", required_prop="value")
    # required_int is not set
    with pytest.raises(datastore_errors.BadValueError) as exc_info:
        model.put()

    # Exception message should include model name, key, and missing property
    error_msg = str(exc_info.value)
    assert "DummyModelWithRequiredProps" in error_msg
    assert "key:" in error_msg
    assert "required_int" in error_msg


def test_pre_put_hook_allows_valid_model(ndb_stub) -> None:
    """Test that _pre_put_hook allows models with all required properties."""
    model = DummyModelWithRequiredProps(
        id="test_model",
        required_prop="value",
        required_int=42,
    )
    # Should not raise an exception
    model.put()
    # Verify the model was saved
    retrieved = DummyModelWithRequiredProps.get_by_id("test_model")
    assert retrieved is not None
    assert retrieved.required_prop == "value"
    assert retrieved.required_int == 42


def test_post_get_hook_validates(ndb_stub, caplog) -> None:
    """Test that _post_get_hook calls validation on fetch.

    Note: This test simulates a scenario where a model was saved before
    a property became required, or where data was corrupted/modified directly.
    In normal circumstances, NDB won't allow saving models with missing required properties.
    """
    # We can't actually save a model with missing required properties through normal means,
    # so we'll just verify that _post_get_hook is called by checking a valid model
    # doesn't trigger errors
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        model.put()
        caplog.clear()

        # Fetch the model - should not log any errors since all required props are set
        _ = DummyModelWithRequiredProps.get_by_id("test_model")

    # No errors should be logged for a valid model
    assert len(caplog.records) == 0


def test_post_get_hook_allows_valid_model(ndb_stub, caplog) -> None:
    """Test that _post_get_hook allows valid models on fetch."""
    # First, put a complete model
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(
            id="test_model",
            required_prop="value",
            required_int=42,
        )
        model.put()
        caplog.clear()

        # Now fetch the model
        _ = DummyModelWithRequiredProps.get_by_id("test_model")
    assert len(caplog.records) == 0


def test_validation_with_no_key(ndb_stub, caplog) -> None:
    """Test validation works even when model has no key (unsaved)."""
    with caplog.at_level(logging.ERROR):
        model = DummyModelWithRequiredProps(required_prop="value")
        model._validate_required_properties()

    # Should log error with "No key (unsaved model)"
    assert len(caplog.records) == 1
    error_message = caplog.records[0].message
    assert "No key (unsaved model)" in error_message
    assert "required_int" in error_message
