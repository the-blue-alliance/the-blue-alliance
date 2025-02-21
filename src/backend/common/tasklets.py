from typing import Callable, cast, Generator, Iterable, TypeVar, Union

from google.appengine.ext import ndb
from pyre_extensions import ParameterSpecification

from backend.common.futures import TypedFuture

TParams = ParameterSpecification("TParams")
TReturn = TypeVar("TReturn")


def typed_tasklet(
    f: Callable[
        TParams, Union[TReturn, Iterable[TReturn], Generator[TReturn, None, None]]
    ],
) -> Callable[TParams, TypedFuture[TReturn]]:
    @ndb.tasklet
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Union[TReturn, Iterable[TReturn], Generator[TReturn, None, None]]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TypedFuture[TReturn]], inner)
