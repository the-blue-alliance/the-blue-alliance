import logging

import google.cloud.logging

from backend.common.environment import Environment


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
    logging.basicConfig(
        level=logging.getLevelName(log_level.upper()),
        format="%(levelname)s\t %(asctime)s %(pathname)s:%(lineno)d] %(name)s: %(message)s",
    )

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
