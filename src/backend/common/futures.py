import types
from typing import Generic, Optional, TypeVar

from google.appengine.ext import ndb


T = TypeVar("T")


class TypedFuture(ndb.Future, Generic[T]):
    def done(self) -> bool:
        return super().done()

    def wait(self) -> None:
        super().wait()

    def check_success(self) -> None:
        super().check_success()

    def set_result(self, result: T) -> None:
        super().set_result(result)

    def set_exception(self, exc: Exception, tb=None) -> None:
        super().set_exception(exc, tb)

    def get_result(self) -> T:
        return super().get_result()

    def get_exception(self) -> Exception:
        return super().get_exception()

    def get_traceback(self) -> Optional[types.TracebackType]:
        return super().get_traceback()


class InstantFuture(TypedFuture[T], Generic[T]):
    def __init__(self, result: T):
        super().__init__()
        self.set_result(result)


class FailedFuture(TypedFuture[T], Generic[T]):
    def __init__(self, exception: Exception):
        super().__init__()
        self.set_exception(exception)
