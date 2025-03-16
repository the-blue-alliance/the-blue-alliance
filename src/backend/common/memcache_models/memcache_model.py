import abc
from datetime import timedelta
from typing import Any, Generator, Generic, Optional, TypeVar

from backend.common.futures import TypedFuture
from backend.common.memcache import MemcacheClient
from backend.common.tasklets import typed_tasklet

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

    def put(self, val: DT) -> bool:
        return self.put_async(val).get_result()

    @typed_tasklet  # pyre-ignore[56]
    def _put_async(self, val: DT) -> Generator[Any, Any, bool]:
        mc_key = self.key()
        ttl_seconds = self.ttl().seconds
        res = yield self.mc_client.set_async(mc_key, val, ttl_seconds)
        return res

    def put_async(self, val: DT) -> TypedFuture[bool]:
        return self._put_async(val)

    def get(self) -> Optional[DT]:
        return self.get_async().get_result()

    @typed_tasklet  # pyre-ignore[56]
    def _get_async(self) -> Generator[Any, Any, DT]:
        mc_key = self.key()
        ret = yield self.mc_client.get_async(mc_key)
        return ret

    def get_async(self) -> TypedFuture[DT]:
        return self._get_async()
