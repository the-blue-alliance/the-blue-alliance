import enum
import os
import tempfile
from pathlib import Path
from typing import Optional


@enum.unique
class EnvironmentMode(enum.Enum):
    LOCAL = "local"
    REMOTE = "remote"


# Mostly GAE env variables
# See https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables
class Environment:
    DEFAULT_FLASK_SECRET_KEY = "thebluealliance"

    @staticmethod
    def _strtobool(value: str) -> bool:
        if not value:
            return False
        return str(value).lower() in ("y", "yes", "t", "true", "on", "1")

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
    def flask_secret_key() -> Optional[str]:
        return os.environ.get("FLASK_SECRET_KEY", Environment.DEFAULT_FLASK_SECRET_KEY)

    @classmethod
    def flask_response_cache_enabled(cls) -> bool:
        return bool(
            cls._strtobool(os.environ.get("FLASK_RESPONSE_CACHE_ENABLED", "true"))
        )

    @classmethod
    def cache_control_header_enabled(cls) -> bool:
        return bool(
            cls._strtobool(os.environ.get("CACHE_CONTROL_HEADER_ENABLED", "true"))
        )

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

    @staticmethod
    def save_frc_api_response() -> bool:
        # Should always be True in production
        if Environment.is_prod():
            return True
        return bool(os.environ.get("SAVE_FRC_API_RESPONSE", False))

    @staticmethod
    def cloudrun_region() -> Optional[str]:
        return os.environ.get("CLOUDRUN_REGION", None)
