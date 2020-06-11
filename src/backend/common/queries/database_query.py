import abc
from backend.common.typed_future import TypedFuture
from backend.common.profiler import Span
from google.cloud import ndb
from typing import TypeVar, Generic


QueryReturn = TypeVar("QueryReturn")


class DatabaseQuery(abc.ABC, Generic[QueryReturn]):

    _query_args: int

    def __init__(self, *args, **kwargs):
        self._query_args = kwargs

    @abc.abstractmethod
    def _query_async(self) -> TypedFuture[QueryReturn]:
        ...

    def fetch(self) -> QueryReturn:
        return self.fetch_async().get_result()

    @ndb.tasklet
    def fetch_async(self) -> TypedFuture[QueryReturn]:
        with Span("{}.fetch_async".format(self.__class__.__name__)):
            query_result = yield self._query_async(**self._query_args)
            # Type-hinting the tasklet decorator is hard, but it consumes
            # the generator and returns the overall future
            return query_result  # pyre-ignore
