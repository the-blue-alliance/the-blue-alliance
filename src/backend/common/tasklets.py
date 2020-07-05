from typing import Callable, cast, TypeVar

from google.cloud import ndb
from pyre_extensions import ParameterSpecification

from backend.common.futures import TypedFuture

TParams = ParameterSpecification("TParams")
TReturn = TypeVar("TReturn")


def typed_tasklet(
    f: Callable[TParams, TReturn]
) -> Callable[TParams, TypedFuture[TReturn]]:
    @ndb.tasklet
    def inner(*args: TParams.args, **kwargs: TParams.kwargs) -> TReturn:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TypedFuture[TReturn]], inner)
