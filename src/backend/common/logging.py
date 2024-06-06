import logging

import google.cloud.logging

from backend.common.environment import Environment


def configure_logging() -> None:
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

    # Intentional test to ensure logging is working
    # TODO(eugene): remove this
    logging.info("INFO")
    logging.warning("WARN")
