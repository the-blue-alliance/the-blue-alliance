from typing import Any, Callable, cast, Generator, Iterable, ParamSpec, TypeVar, Union

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")


def typed_tasklet(
    f: Callable[
        TParams, Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]
    ],
) -> Callable[TParams, TypedFuture[TReturn]]:
    @ndb.tasklet
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TypedFuture[TReturn]], inner)


def typed_toplevel(
    f: Callable[
        TParams, Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]
    ],
) -> Callable[TParams, TReturn]:
    @ndb.toplevel
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TReturn], inner)
