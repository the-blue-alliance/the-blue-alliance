import enum
import os
from typing import Optional


@enum.unique
class EnvironmentMode(enum.Enum):
    LOCAL = "local"
    REMOTE = "remote"


class Environment(object):
    @staticmethod
    def is_dev() -> bool:
        return os.environ.get("GAE_ENV") == "localdev"

    @staticmethod
    def is_prod() -> bool:
        env = os.environ.get("GAE_ENV")
        return env is not None and env.startswith("standard")

    @staticmethod
    def project() -> Optional[str]:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", None)

    @staticmethod
    def log_level() -> Optional[str]:
        return os.environ.get("TBA_LOG_LEVEL")

    @staticmethod
    def tasks_mode() -> EnvironmentMode:
        return EnvironmentMode(os.environ.get("TASKS_MODE", "local"))

    @staticmethod
    def ndb_log_level() -> Optional[str]:
        return os.environ.get("NDB_LOG_LEVEL")
