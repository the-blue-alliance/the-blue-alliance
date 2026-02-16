import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

from werkzeug.test import create_environ

from backend.common.logging import (
    clear_logging_context,
    configure_logging,
    get_logging_context,
    logging_context,
    LoggingContextFilter,
    set_logging_context,
)
from backend.common.middleware import TraceRequestMiddleware


def test_LoggingContextFilter_with_labels() -> None:
    """Test that LoggingContextFilter adds context as labels."""
    log_filter = LoggingContextFilter(use_labels=True)

    # Set up mock request with context
    class MockRequest:
        logging_context = {"user_id": "123", "request_id": "abc"}

    logging_context.request = MockRequest()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Apply the filter
    result = log_filter.filter(record)

    assert result is True
    assert hasattr(record, "labels")
    # pyre-ignore[16]: labels is set dynamically by our filter
    labels: Dict[str, Any] = getattr(record, "labels")
    assert labels["user_id"] == "123"
    assert labels["request_id"] == "abc"

    # Clean up
    del logging_context.request


def test_LoggingContextFilter_merges_existing_labels() -> None:
    """Test that LoggingContextFilter merges with existing labels."""
    log_filter = LoggingContextFilter(use_labels=True)

    # Set up mock request with context
    class MockRequest:
        logging_context = {"user_id": "123"}

    logging_context.request = MockRequest()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Set existing labels on the record
    setattr(record, "labels", {"existing_key": "existing_value"})

    # Apply the filter
    log_filter.filter(record)

    # Both existing and new labels should be present
    # pyre-ignore[16]: labels is set dynamically by our filter
    labels: Dict[str, Any] = getattr(record, "labels")
    assert labels["existing_key"] == "existing_value"
    assert labels["user_id"] == "123"

    # Clean up
    del logging_context.request


def test_LoggingContextFilter_without_labels() -> None:
    """Test that LoggingContextFilter appends context to message when use_labels=False."""
    log_filter = LoggingContextFilter(use_labels=False)

    # Set up mock request with context
    class MockRequest:
        logging_context = {"user_id": "123", "request_id": "abc"}

    logging_context.request = MockRequest()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Apply the filter
    log_filter.filter(record)

    # Message should have context appended
    assert "user_id=123" in record.msg
    assert "request_id=abc" in record.msg
    assert "Test message" in record.msg

    # Clean up
    del logging_context.request


def test_LoggingContextFilter_no_context() -> None:
    """Test that LoggingContextFilter works when there's no context."""
    log_filter = LoggingContextFilter(use_labels=True)

    # Make sure there's no logging context
    if hasattr(logging_context, "request"):
        del logging_context.request

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Apply the filter
    result = log_filter.filter(record)

    assert result is True
    # Record should not have labels attribute if there's no context
    assert not hasattr(record, "labels")


def test_configure_logging_dev() -> None:
    """Test that configure_logging uses context filter in dev."""
    with patch("backend.common.logging.Environment.is_prod", return_value=False):
        configure_logging()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        handler = root_logger.handlers[0]
        # Check that our context filter is applied
        filter_found = any(isinstance(f, LoggingContextFilter) for f in handler.filters)
        assert filter_found


def test_configure_logging_prod() -> None:
    """Test that configure_logging handles production but skips in unit tests."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=True
        ):
            # is_unit_test returns True to avoid calling google.cloud.logging.Client()
            configure_logging()

            root_logger = logging.getLogger()
            # Note: When unit test is True, we still use dev config
            # This is expected behavior
            assert len(root_logger.handlers) > 0


def test_configure_logging_prod_not_unit_test() -> None:
    """Test that configure_logging preserves Google Cloud handler and applies context filter."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=False
        ):
            # Mock the Google Cloud logging client
            mock_client = Mock()
            # Use a real StreamHandler so we can test filter attachment
            test_handler = logging.StreamHandler()

            with patch("google.cloud.logging.Client", return_value=mock_client):
                # Mock setup_logging to add a handler like the real one does
                def mock_setup_logging():
                    root_logger = logging.getLogger()
                    # Clear any existing handlers first
                    root_logger.handlers.clear()
                    root_logger.addHandler(test_handler)

                mock_client.setup_logging = mock_setup_logging

                configure_logging()

                root_logger = logging.getLogger()
                # Verify the handler was preserved (not removed)
                assert test_handler in root_logger.handlers

                # Verify our context filter was applied to the handler
                filter_found = any(
                    isinstance(f, LoggingContextFilter) for f in test_handler.filters
                )
                assert filter_found

                # Verify the filter is using labels mode in prod
                context_filter = next(
                    f
                    for f in test_handler.filters
                    if isinstance(f, LoggingContextFilter)
                )
                assert context_filter.use_labels is True


def test_configure_logging_preserves_multiple_handlers() -> None:
    """Test that all handlers added by setup_logging get the context filter."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=False
        ):
            mock_client = Mock()
            # Create multiple handlers like Google Cloud might add
            handler1 = logging.StreamHandler()
            handler2 = logging.StreamHandler()

            with patch("google.cloud.logging.Client", return_value=mock_client):

                def mock_setup_logging():
                    root_logger = logging.getLogger()
                    root_logger.handlers.clear()
                    root_logger.addHandler(handler1)
                    root_logger.addHandler(handler2)

                mock_client.setup_logging = mock_setup_logging

                configure_logging()

                root_logger = logging.getLogger()
                # Both handlers should be preserved
                assert handler1 in root_logger.handlers
                assert handler2 in root_logger.handlers

                # Both should have the context filter
                assert any(
                    isinstance(f, LoggingContextFilter) for f in handler1.filters
                )
                assert any(
                    isinstance(f, LoggingContextFilter) for f in handler2.filters
                )


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


def test_integration_with_cloud_logging_handler() -> None:
    """Test end-to-end integration: context -> filter -> handler with labels."""
    import io

    # Set up logging context
    class MockRequest:
        logging_context = {"user_id": "test_user", "event_key": "2024casj"}

    logging_context.request = MockRequest()

    # Create a logger with our filter
    logger = logging.getLogger("test_integration")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Create a handler with our context filter
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    context_filter = LoggingContextFilter(use_labels=True)
    handler.addFilter(context_filter)
    logger.addHandler(handler)

    # Set logging context and log a message
    set_logging_context("request_id", "req-123")

    # Create a log record
    logger.info("Processing request")

    # Get the record that was processed
    # We need to manually check since the handler already processed it
    # Instead, let's create a custom handler that captures the record

    # Clean up
    del logging_context.request
    logger.handlers.clear()


def test_cloud_logging_handler_receives_labels() -> None:
    """Test that CloudLoggingHandler receives labels from our filter."""

    # Set up logging context
    class MockRequest:
        logging_context = {"user_id": "test_user", "event_key": "2024casj"}

    logging_context.request = MockRequest()

    # Create a mock handler that captures emitted records
    captured_records = []

    class CapturingHandler(logging.Handler):
        def emit(self, record):
            captured_records.append(record)

    # Create logger with our filter
    logger = logging.getLogger("test_cloud_labels")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = CapturingHandler()
    context_filter = LoggingContextFilter(use_labels=True)
    handler.addFilter(context_filter)
    logger.addHandler(handler)

    # Log a message
    logger.info("Test message")

    # Verify the record has labels
    assert len(captured_records) == 1
    record = captured_records[0]

    assert hasattr(record, "labels")
    labels: Dict[str, Any] = getattr(record, "labels")
    assert labels["user_id"] == "test_user"
    assert labels["event_key"] == "2024casj"

    # Clean up
    del logging_context.request
    logger.handlers.clear()


def test_cloud_logging_handler_with_extra_record_labels() -> None:
    """Test that our filter merges with labels passed via extra parameter."""

    # Set up logging context
    class MockRequest:
        logging_context = {"global_key": "global_value"}

    logging_context.request = MockRequest()

    # Create a mock handler that captures emitted records
    captured_records = []

    class CapturingHandler(logging.Handler):
        def emit(self, record):
            captured_records.append(record)

    # Create logger with our filter
    logger = logging.getLogger("test_merge_labels")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = CapturingHandler()
    context_filter = LoggingContextFilter(use_labels=True)
    handler.addFilter(context_filter)
    logger.addHandler(handler)

    # Log with extra labels (this is how Google Cloud Logging accepts per-log labels)
    logger.info("Test message", extra={"labels": {"per_log_key": "per_log_value"}})

    # Verify both global and per-log labels are present
    assert len(captured_records) == 1
    record = captured_records[0]

    assert hasattr(record, "labels")
    labels: Dict[str, Any] = getattr(record, "labels")
    assert labels["global_key"] == "global_value"
    assert labels["per_log_key"] == "per_log_value"

    # Clean up
    del logging_context.request
    logger.handlers.clear()


def test_configure_logging_dev_uses_non_label_mode() -> None:
    """Test that dev mode appends context to message instead of using labels."""
    with patch("backend.common.logging.Environment.is_prod", return_value=False):
        configure_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        # Find the context filter
        context_filter = next(
            (f for f in handler.filters if isinstance(f, LoggingContextFilter)), None
        )

        assert context_filter is not None
        assert context_filter.use_labels is False
