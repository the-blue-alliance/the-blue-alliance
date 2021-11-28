import enum
import os
import tempfile
from distutils.util import strtobool
from pathlib import Path
from typing import Optional


@enum.unique
class EnvironmentMode(enum.Enum):
    LOCAL = "local"
    REMOTE = "remote"


# Mostly GAE env variables
# See https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables
class Environment:
    @staticmethod
    def is_unit_test() -> bool:
        return os.environ.get("TBA_UNIT_TEST") == "true"

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
    def project() -> Optional[str]:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", None)

    @staticmethod
    def log_level() -> Optional[str]:
        return os.environ.get("TBA_LOG_LEVEL")

    @staticmethod
    def ndb_log_level() -> Optional[str]:
        return os.environ.get("NDB_LOG_LEVEL")

    @staticmethod
    def flask_response_cache_enabled() -> bool:
        return bool(strtobool(os.environ.get("FLASK_RESPONSE_CACHE_ENABLED", "true")))

    @staticmethod
    def cache_control_header_enabled() -> bool:
        return bool(strtobool(os.environ.get("CACHE_CONTROL_HEADER_ENABLED", "true")))

    @staticmethod
    def storage_mode() -> EnvironmentMode:
        return EnvironmentMode(os.environ.get("STORAGE_MODE", "local"))

    @staticmethod
    def storage_path() -> Path:
        # Fallback to returning a tmp directory for a storage path
        return Path(os.environ.get("STORAGE_PATH", tempfile.gettempdir()))

    @staticmethod
    def auth_emulator_host() -> Optional[str]:
        return os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
