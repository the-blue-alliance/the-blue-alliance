import re
import time
from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict, total=False):
    regex: str
    valid_until: int
    cache_length: int


class TurboMode(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "turbo_mode"

    @staticmethod
    def description() -> str:
        return "For overriding cache timers"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            regex="",
        )

    @classmethod
    def cache_ttl(cls, request_path: str, default_ttl: int) -> int:
        cfg = cls.get()
        path_regex = cfg.get("regex", "")
        if not path_regex or path_regex == "$^":
            return default_ttl

        pattern = re.compile(path_regex)
        valid_until = cfg.get("valid_until", -1)  # UNIX time
        cache_length = cfg.get("cache_length", default_ttl)
        now = time.time()

        if now <= int(valid_until) and cache_length > 0 and pattern.match(request_path):
            return cache_length

        return default_ttl
