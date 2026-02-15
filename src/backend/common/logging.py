import json
import logging

import google.cloud.logging
from werkzeug.local import Local

from backend.common.environment import Environment

# Request-local context for storing additional logging context
logging_context = Local()


class GoogleCloudJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for Google Cloud Logging.
    Formats log records as JSON with 'message' and 'severity' fields.
    See: https://cloud.google.com/appengine/docs/standard/writing-application-logs?tab=python#stdout_stderr
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "message": super().format(record),
            "severity": record.levelname,
        }

        # Add any additional context from the request-local logging_context
        if hasattr(logging_context, "request") and logging_context.request:
            context_dict = getattr(logging_context.request, "logging_context", {})
            if context_dict:
                log_obj.update(context_dict)

        return json.dumps(log_obj)


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

    if Environment.is_prod() and not Environment.is_unit_test():
        # Setting this up only needs to be done in prod to ensure logs are grouped properly with the request.
        client = google.cloud.logging.Client()
        client.setup_logging()

    log_level = Environment.log_level() or "INFO"

    # Use JSON formatter for Google Cloud in production, regular format otherwise
    if Environment.is_prod() and not Environment.is_unit_test():
        formatter = GoogleCloudJsonFormatter("%(name)s: %(message)s")
    else:
        formatter = logging.Formatter(
            "%(levelname)s\t %(asctime)s %(pathname)s:%(lineno)d] %(name)s: %(message)s"
        )

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(log_level.upper()))

    # Remove any existing handlers and add our handler with the appropriate formatter
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
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
