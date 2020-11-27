import enum
import os
from typing import Optional

from backend.common.environment.tasks import TasksRemoteConfig


@enum.unique
class EnvironmentMode(enum.Enum):
    LOCAL = "local"
    REMOTE = "remote"


# Mostly GAE env variables
# See https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables
class Environment(object):
    @staticmethod
    def is_dev() -> bool:
        return os.environ.get("GAE_ENV") == "localdev"

    @staticmethod
    def is_prod() -> bool:
        env = os.environ.get("GAE_ENV")
        return env is not None and env.startswith("standard")

    @staticmethod
    def service() -> Optional[str]:
        return os.environ.get("GAE_SERVICE", None)

    @staticmethod
    def service_for_current_service() -> str:
        # Get current service - otherwise, fallback on default service
        service = Environment.service()
        return service if service else "default"

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
    def tasks_remote_config() -> Optional[TasksRemoteConfig]:
        remote_config_ngrok_url = os.environ.get("TASKS_REMOTE_CONFIG_NGROK_URL", None)
        if not remote_config_ngrok_url:
            return None
        return TasksRemoteConfig(ngrok_url=remote_config_ngrok_url)

    @staticmethod
    def ndb_log_level() -> Optional[str]:
        return os.environ.get("NDB_LOG_LEVEL")

    @staticmethod
    def redis_url() -> Optional[str]:
        return os.environ.get("REDIS_CACHE_URL")
