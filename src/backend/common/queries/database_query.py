import abc
from backend.common.typed_future import TypedFuture
from backend.common.profiler import TraceContext
from backend.common.queries.dict_converters.converter_base import ConverterBase
from backend.common.queries.exceptions import DoesNotExistException
from backend.common.queries.types import QueryReturn
from google.cloud import ndb
from typing import Generic


class DatabaseQuery(abc.ABC, Generic[QueryReturn]):

    _query_args: int
    DICT_CONVERTER: ConverterBase

    def __init__(self, *args, **kwargs):
        self._query_args = kwargs

    @abc.abstractmethod
    def _query_async(self) -> TypedFuture[QueryReturn]:
        ...

    def fetch(self) -> QueryReturn:
        return self.fetch_async().get_result()

    @ndb.tasklet
    def fetch_async(self) -> TypedFuture[QueryReturn]:
        with TraceContext() as root:
            with root.span("{}.fetch_async".format(self.__class__.__name__)):
                query_result = yield self._query_async(**self._query_args)
                # Type-hinting the tasklet decorator is hard, but it consumes
                # the generator and returns the overall future
                return query_result  # pyre-ignore

    def fetch_dict(self, version: int) -> dict:
        return self.fetch_dict_async(version).get_result()

    @ndb.tasklet
    def fetch_dict_async(self, version: int) -> TypedFuture[dict]:
        query_result = yield self.fetch_async()
        if query_result is None:
            raise DoesNotExistException()
        # Type-hinting the tasklet decorator is hard, but it consumes
        # the generator and returns the overall future
        return self.DICT_CONVERTER.convert(query_result, version)  # pyre-ignore
