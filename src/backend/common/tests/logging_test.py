import json
import logging
from unittest.mock import patch

from werkzeug.test import create_environ

from backend.common.logging import (
    clear_logging_context,
    configure_logging,
    get_logging_context,
    GoogleCloudJsonFormatter,
    logging_context,
    set_logging_context,
)
from backend.common.middleware import TraceRequestMiddleware


def test_GoogleCloudJsonFormatter_basic() -> None:
    """Test that GoogleCloudJsonFormatter formats logs as JSON with message and severity."""
    formatter = GoogleCloudJsonFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert "message" in parsed
    assert "severity" in parsed
    assert parsed["severity"] == "INFO"
    assert "test_logger: Test message" in parsed["message"]


def test_GoogleCloudJsonFormatter_with_context() -> None:
    """Test that GoogleCloudJsonFormatter includes logging context."""
    formatter = GoogleCloudJsonFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Set up a mock request with logging context
    class MockRequest:
        logging_context = {"user_id": "123", "request_id": "abc"}

    logging_context.request = MockRequest()

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["severity"] == "WARNING"
    assert parsed["user_id"] == "123"
    assert parsed["request_id"] == "abc"

    # Clean up
    del logging_context.request


def test_GoogleCloudJsonFormatter_without_context() -> None:
    """Test that GoogleCloudJsonFormatter works without logging context."""
    formatter = GoogleCloudJsonFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Test error",
        args=(),
        exc_info=None,
    )

    # Make sure there's no logging context
    if hasattr(logging_context, "request"):
        del logging_context.request

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["severity"] == "ERROR"
    assert "test_logger: Test error" in parsed["message"]
    # Should only have message and severity, no extra fields
    assert len(parsed) == 2


def test_configure_logging_dev() -> None:
    """Test that configure_logging uses regular formatter in dev."""
    with patch("backend.common.logging.Environment.is_prod", return_value=False):
        configure_logging()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        handler = root_logger.handlers[0]
        # In dev, should use regular Formatter, not GoogleCloudJsonFormatter
        assert not isinstance(handler.formatter, GoogleCloudJsonFormatter)


def test_configure_logging_prod() -> None:
    """Test that configure_logging uses JSON formatter in prod."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=True
        ):
            # is_unit_test returns True to avoid calling google.cloud.logging.Client()
            configure_logging()

            root_logger = logging.getLogger()
            # Note: When unit test is True, we still use regular formatter
            # This is expected behavior
            assert len(root_logger.handlers) > 0


def test_configure_logging_prod_not_unit_test() -> None:
    """Test that configure_logging uses JSON formatter in prod when not in unit test."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=False
        ):
            with patch("google.cloud.logging.Client"):
                configure_logging()

                root_logger = logging.getLogger()
                assert len(root_logger.handlers) > 0

                handler = root_logger.handlers[0]
                # In prod (not unit test), should use GoogleCloudJsonFormatter
                assert isinstance(handler.formatter, GoogleCloudJsonFormatter)


def test_TraceRequestMiddleware_initializes_logging_context(app) -> None:
    """Test that TraceRequestMiddleware initializes logging_context.request."""
    middleware = TraceRequestMiddleware(app)

    def start_response(status, headers):
        pass

    environ = create_environ(path="/", base_url="http://localhost")
    middleware(environ, start_response)

    assert hasattr(logging_context, "request")
    assert hasattr(logging_context.request, "logging_context")
    assert isinstance(logging_context.request.logging_context, dict)
    assert len(logging_context.request.logging_context) == 0


def test_set_logging_context() -> None:
    """Test set_logging_context helper function."""

    # Set up a mock request
    class MockRequest:
        logging_context = {}

    logging_context.request = MockRequest()

    # Set some context values
    set_logging_context("user_id", "user123")
    set_logging_context("trace_id", "xyz789")

    assert logging_context.request.logging_context["user_id"] == "user123"
    assert logging_context.request.logging_context["trace_id"] == "xyz789"

    # Clean up
    del logging_context.request


def test_get_logging_context() -> None:
    """Test get_logging_context helper function."""

    # Set up a mock request with context
    class MockRequest:
        logging_context = {"key1": "value1", "key2": "value2"}

    logging_context.request = MockRequest()

    context = get_logging_context()
    assert context == {"key1": "value1", "key2": "value2"}

    # Clean up
    del logging_context.request

    # Test when no request exists
    context_no_request = get_logging_context()
    assert context_no_request == {}


def test_clear_logging_context() -> None:
    """Test clear_logging_context helper function."""

    # Set up a mock request with context
    class MockRequest:
        logging_context = {"key1": "value1", "key2": "value2"}

    logging_context.request = MockRequest()

    # Clear the context
    clear_logging_context()

    assert logging_context.request.logging_context == {}

    # Clean up
    del logging_context.request


def test_set_logging_context_initializes_dict() -> None:
    """Test that set_logging_context initializes the dict if it doesn't exist."""

    # Set up a mock request without logging_context
    class MockRequest:
        pass

    logging_context.request = MockRequest()

    # This should initialize the dict
    set_logging_context("key", "value")

    assert hasattr(logging_context.request, "logging_context")
    assert logging_context.request.logging_context == {"key": "value"}

    # Clean up
    del logging_context.request
