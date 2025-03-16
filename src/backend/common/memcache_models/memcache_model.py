import abc
from datetime import timedelta
from typing import Generic, Optional, TypeVar

from backend.common.memcache import MemcacheClient

DT = TypeVar("DT")


class MemcacheModel(abc.ABC, Generic[DT]):
    """
    This is an abstraction around data we write/read from memcache
    """

    def __init__(self) -> None:
        self.mc_client = MemcacheClient.get()

    @abc.abstractmethod
    def key(self) -> bytes: ...

    @abc.abstractmethod
    def ttl(self) -> timedelta: ...

    def put(self, val: DT) -> None:
        mc_key = self.key()
        ttl_seconds = self.ttl().seconds
        self.mc_client.set(mc_key, val, ttl_seconds)

    def get(self) -> Optional[DT]:
        mc_key = self.key()
        return self.mc_client.get(mc_key)
