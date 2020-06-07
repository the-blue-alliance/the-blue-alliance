import types
from google.cloud import ndb
from typing import Callable, Generic, Optional, TypeVar


T = TypeVar("T")


class TypedFuture(ndb.Future, Generic[T]):
    def done(self) -> bool:
        return super().done()

    def running(self) -> bool:
        return super().running()

    def wait(self) -> None:
        super().wait()

    def check_success(self) -> None:
        super().check_success()

    def set_result(self, result: T) -> None:
        super().set_result(result)

    def set_exception(self, exception: Exception) -> None:
        super().set_exception(exception)

    def result(self) -> T:
        return super().result()

    def get_result(self) -> T:
        return super().get_result()

    def exception(self) -> Exception:
        return super().exception()

    def get_exception(self) -> Exception:
        return super().get_exception()

    def get_traceback(self) -> Optional[types.TracebackType]:
        return super().get_traceback()

    def add_done_callback(self, callback: Callable[[], None]) -> None:
        super().add_done_callback(callback)

    def cancel(self) -> None:
        super().cancel()

    def cancelled(self) -> bool:
        return super().cancelled()
