import json
import logging
from typing import Any, Dict
from unittest.mock import patch

from werkzeug.test import create_environ

from backend.common.logging import (
    clear_logging_context,
    configure_logging,
    get_logging_context,
    GoogleCloudStructuredFormatter,
    logging_context,
    LoggingContextFilter,
    set_logging_context,
)
from backend.common.middleware import TraceRequestMiddleware


def test_GoogleCloudStructuredFormatter_basic() -> None:
    """Test that GoogleCloudStructuredFormatter formats logs as JSON."""
    formatter = GoogleCloudStructuredFormatter("%(name)s: %(message)s")
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


def test_GoogleCloudStructuredFormatter_with_labels() -> None:
    """Test that GoogleCloudStructuredFormatter includes labels."""
    formatter = GoogleCloudStructuredFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Set labels on the record (as our filter would do)
    setattr(record, "labels", {"user_id": "123", "request_id": "abc"})

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["severity"] == "WARNING"
    assert "logging.googleapis.com/labels" in parsed
    assert parsed["logging.googleapis.com/labels"]["user_id"] == "123"
    assert parsed["logging.googleapis.com/labels"]["request_id"] == "abc"


def test_GoogleCloudStructuredFormatter_without_labels() -> None:
    """Test that GoogleCloudStructuredFormatter works without labels."""
    formatter = GoogleCloudStructuredFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Test error",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["severity"] == "ERROR"
    assert "test_logger: Test error" in parsed["message"]
    # Should not have labels key if no labels were set
    assert "logging.googleapis.com/labels" not in parsed


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
    """Test that configure_logging uses structured JSON formatter in production."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=False
        ):
            configure_logging()

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            handler = root_logger.handlers[0]
            # Verify our JSON formatter was applied
            assert isinstance(handler.formatter, GoogleCloudStructuredFormatter)

            # Verify the context filter is using labels mode in prod
            context_filter = next(
                (f for f in handler.filters if isinstance(f, LoggingContextFilter)),
                None,
            )
            assert context_filter is not None
            assert context_filter.use_labels is True


def test_configure_logging_handler_in_prod() -> None:
    """Test that configure_logging sets up handler with correct formatter and filter."""
    with patch("backend.common.logging.Environment.is_prod", return_value=True):
        with patch(
            "backend.common.logging.Environment.is_unit_test", return_value=False
        ):
            configure_logging()

            root_logger = logging.getLogger()
            # Should have exactly one handler
            assert len(root_logger.handlers) == 1

            handler = root_logger.handlers[0]
            # Should be a StreamHandler with our formatter
            assert isinstance(handler, logging.StreamHandler)
            assert isinstance(handler.formatter, GoogleCloudStructuredFormatter)

            # Should have the context filter
            assert any(isinstance(f, LoggingContextFilter) for f in handler.filters)


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


def test_GoogleCloudStructuredFormatter_trace_correlation() -> None:
    """Test that GoogleCloudStructuredFormatter includes Cloud Trace fields."""
    from backend.common.profiler import Span, trace_context

    class MockTraceRequest:
        headers = {"X-Cloud-Trace-Context": "TRACE_12345/ROOT_SPAN_6789;o=1"}
        trace_id = "TRACE_12345"
        root_span_id = "ROOT_SPAN_6789"
        _trace_sampled = True

    trace_context.request = MockTraceRequest()

    formatter = GoogleCloudStructuredFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Trace message",
        args=(),
        exc_info=None,
    )

    with patch(
        "backend.common.environment.Environment.project", return_value="tbatv-prod-hrd"
    ):
        # 1. Outside active span -> fallback to root_span_id (non-numeric string fallback)
        output = formatter.format(record)
        parsed = json.loads(output)
        assert (
            parsed["logging.googleapis.com/trace"]
            == "projects/tbatv-prod-hrd/traces/TRACE_12345"
        )
        assert parsed["logging.googleapis.com/spanId"] == "ROOT_SPAN_6789"
        assert parsed["logging.googleapis.com/trace_sampled"] is True

        # 2. Outside active span with numeric root_span_id -> formatted as 16-hex
        trace_context.request.root_span_id = "1234567890"
        output_numeric = formatter.format(record)
        parsed_numeric = json.loads(output_numeric)
        assert parsed_numeric["logging.googleapis.com/spanId"] == f"{1234567890:016x}"
        assert len(parsed_numeric["logging.googleapis.com/spanId"]) == 16

        # 3. Inside active child span -> attaches to child span_id formatted as 16-hex
        with Span("test_child_span") as child:
            output_child = formatter.format(record)
            parsed_child = json.loads(output_child)
            assert (
                parsed_child["logging.googleapis.com/trace"]
                == "projects/tbatv-prod-hrd/traces/TRACE_12345"
            )
            assert parsed_child["logging.googleapis.com/spanId"] == child.span_id_hex
            assert len(parsed_child["logging.googleapis.com/spanId"]) == 16
            assert parsed_child["logging.googleapis.com/trace_sampled"] is True

            # Ensure a spanId whose hex encoding contains only digits 0-9 is NOT corrupted
            child._span_id = str(0x1234567890123456)
            output_numeric_hex = formatter.format(record)
            parsed_numeric_hex = json.loads(output_numeric_hex)
            assert (
                parsed_numeric_hex["logging.googleapis.com/spanId"]
                == "1234567890123456"
            )

    # Clean up
    del trace_context.request


def test_GoogleCloudStructuredFormatter_early_log_trace_correlation() -> None:
    """Test that logs emitted before any Span is created still correlate via request headers."""
    from backend.common.profiler import trace_context

    class MockTraceRequest:
        headers = {"X-Cloud-Trace-Context": "TRACE_EARLY_123/9876543210;o=1"}

    trace_context.request = MockTraceRequest()

    formatter = GoogleCloudStructuredFormatter("%(name)s: %(message)s")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Early message before any Span",
        args=(),
        exc_info=None,
    )

    with patch(
        "backend.common.environment.Environment.project", return_value="tbatv-prod-hrd"
    ):
        output = formatter.format(record)
        parsed = json.loads(output)
        assert (
            parsed["logging.googleapis.com/trace"]
            == "projects/tbatv-prod-hrd/traces/TRACE_EARLY_123"
        )
        assert parsed["logging.googleapis.com/spanId"] == f"{9876543210:016x}"
        assert parsed["logging.googleapis.com/trace_sampled"] is True

    # Clean up
    del trace_context.request
