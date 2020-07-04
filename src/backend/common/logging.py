import logging

from backend.common.environment import Environment


def configure_logging() -> None:
    log_level = Environment.log_level() or "INFO"
    logging.basicConfig(
        level=logging.getLevelName(log_level.upper()),
        format="%(levelname)s\t %(asctime)s %(pathname)s:%(lineno)d] %(name)s: %(message)s",
    )

    ndb_log_level = Environment.ndb_log_level()
    if ndb_log_level:
        from google.cloud import ndb

        ndb_loggers = [
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict  # pyre-ignore[16]
            if ndb.__name__ in name
        ]
        for logger in ndb_loggers:
            logger.setLevel(ndb_log_level.upper())
