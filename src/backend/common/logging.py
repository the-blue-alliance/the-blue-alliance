import logging

from backend.common.environment import Environment


def configure_logging() -> None:
    log_level = Environment.log_level() or "INFO"
    logging.basicConfig(
        level=logging.getLevelName(log_level.upper()),
        format="%(levelname)s\t %(asctime)s %(pathname)s:%(lineno)d] %(name)s: %(message)s",
    )
