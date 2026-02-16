import logging
from typing import Any, Dict

import google.cloud.logging
from werkzeug.local import Local

from backend.common.environment import Environment

# Request-local context for storing additional logging context
logging_context = Local()


def set_logging_context(key: str, value: Any) -> None:
    """
    Set a key-value pair in the request-local logging context.
    This context will be included in all log messages during this request.

    Example:
        set_logging_context("user_id", "user123")
        set_logging_context("request_id", "req-abc-123")
    """
    if hasattr(logging_context, "request") and logging_context.request:
        if not hasattr(logging_context.request, "logging_context"):
            logging_context.request.logging_context = {}
        logging_context.request.logging_context[key] = value


def get_logging_context() -> Dict[str, Any]:
    """
    Get the current request-local logging context.

    Returns:
        Dictionary of context key-value pairs, or empty dict if no context.
    """
    if hasattr(logging_context, "request") and logging_context.request:
        return getattr(logging_context.request, "logging_context", {})
    return {}


def clear_logging_context() -> None:
    """
    Clear all values from the request-local logging context.
    """
    if hasattr(logging_context, "request") and logging_context.request:
        logging_context.request.logging_context = {}


class LoggingContextFilter(logging.Filter):
    """
    A logging filter that adds request-local context to log records as labels.

    This filter integrates with Google Cloud Logging's CloudLoggingHandler by
    setting record.labels, which are then properly indexed and searchable in GCP.

    For local development, the labels are formatted as key=value pairs in the message.
    """

    def __init__(self, use_labels: bool = True) -> None:
        """
        Args:
            use_labels: If True, use record.labels for Google Cloud integration.
                       If False, append context to message for local dev.
        """
        super().__init__()
        self.use_labels = use_labels

    def filter(self, record: logging.LogRecord) -> bool:
        """Add logging context to the record."""
        context = get_logging_context()

        if context:
            if self.use_labels:
                # For Google Cloud: merge context into labels
                # CloudLoggingFilter expects record.labels to be set by user code
                existing_labels = getattr(record, "labels", {})
                setattr(record, "labels", {**existing_labels, **context})
            else:
                # For local dev: append context to message
                context_str = " ".join(f"{k}={v}" for k, v in context.items())
                record.msg = f"{record.msg} [{context_str}]"

        return True


def configure_logging() -> None:
    # See https://github.com/GoogleChrome/chromium-dashboard/issues/3197
    import threading

    # Patch treading library to work-around bug with Google Cloud Logging.
    original_delete = threading.Thread._delete  # type: ignore

    def safe_delete(self):
        try:
            original_delete(self)
        except KeyError:
            pass

    threading.Thread._delete = safe_delete  # type: ignore

    log_level = Environment.log_level() or "INFO"

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(log_level.upper()))

    if Environment.is_prod() and not Environment.is_unit_test():
        # Setting this up only needs to be done in prod to ensure logs are grouped properly with the request.
        # This adds a CloudLoggingHandler with CloudLoggingFilter which supports labels
        client = google.cloud.logging.Client()
        client.setup_logging()

        # Add our custom filter to inject logging context as labels
        # The CloudLoggingHandler will pick up record.labels and send them to GCP
        context_filter = LoggingContextFilter(use_labels=True)
        for handler in root_logger.handlers:
            handler.addFilter(context_filter)
    else:
        # In dev/local, use standard logging format
        formatter = logging.Formatter(
            "%(levelname)s\t %(asctime)s %(pathname)s:%(lineno)d] %(name)s: %(message)s"
        )

        # Remove any existing handlers and add our handler
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Add our context filter (will append context to message in dev)
        context_filter = LoggingContextFilter(use_labels=False)
        handler.addFilter(context_filter)

        root_logger.addHandler(handler)

    ndb_log_level = Environment.ndb_log_level()
    if ndb_log_level:
        from google.appengine.ext import ndb

        ndb_loggers = [
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict
            if ndb.__name__ in name
        ]
        for logger in ndb_loggers:
            logger.setLevel(ndb_log_level.upper())
