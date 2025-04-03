import abc
import logging
from typing import Any, Dict, Generator, Generic, Optional, TypeVar

from google.appengine.ext import ndb
from google.appengine.ext.ndb.context import Context

from backend.common.futures import TypedFuture
from backend.common.profiler import Span
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase, TParsedResponse


TReturn = TypeVar("TReturn")


class DatafeedBase(abc.ABC, Generic[TReturn]):

    ndb_context: Context

    def __init__(self) -> None:
        self.ndb_context = ndb.get_context()

    @abc.abstractmethod
    def url(self) -> str: ...

    @abc.abstractmethod
    def headers(self) -> Dict[str, str]: ...

    @abc.abstractmethod
    def parser(self) -> ParserBase[TReturn]: ...

    def fetch_async(self) -> TypedFuture[Optional[TReturn]]:
        # Work around a pyre limitation where we can't combine
        # decorator type hints with generics
        return self._gen()

    @ndb.tasklet
    def _gen(self) -> Generator[Any, Any, Optional[TReturn]]:
        response = yield self._fetch()
        parser = self.parser()
        return self._parse(response, parser)

    def _fetch(self) -> TypedFuture[URLFetchResult]:
        url = self.url()
        headers = self.headers()
        return self._urlfetch(url, headers)

    @ndb.tasklet
    def _urlfetch(
        self, url: str, headers: Dict[str, str]
    ) -> Generator[Any, Any, URLFetchResult]:
        with Span(f"api_fetch:{type(self).__name__}"):
            resp = yield self.ndb_context.urlfetch(url, headers=headers, deadline=30)
            return URLFetchResult(url, resp)

    def _parse(
        self, response: URLFetchResult, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            with Span(f"api_parser:{type(parser).__name__}"):
                return parser.parse(response.json())
        elif response.status_code == 404:
            return None

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None
