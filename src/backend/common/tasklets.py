from collections.abc import Callable, Generator, Iterable
from typing import Any, cast, ParamSpec, TypeVar

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")


def typed_tasklet(
    f: Callable[TParams, TReturn | Iterable[TReturn] | Generator[Any, Any, TReturn]],
) -> Callable[TParams, TypedFuture[TReturn]]:
    @ndb.tasklet
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> TReturn | Iterable[TReturn] | Generator[Any, Any, TReturn]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TypedFuture[TReturn]], inner)


def typed_toplevel(
    f: Callable[TParams, TReturn | Iterable[TReturn] | Generator[Any, Any, TReturn]],
) -> Callable[TParams, TReturn]:
    @ndb.toplevel
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> TReturn | Iterable[TReturn] | Generator[Any, Any, TReturn]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TReturn], inner)
