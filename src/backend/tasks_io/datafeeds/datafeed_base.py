import abc
import logging
from typing import Any, cast, Dict, Generator, Generic, Optional, TypeVar
from urllib.parse import urlencode

from google.appengine.ext import ndb
from google.appengine.ext.ndb.context import Context

from backend.common.futures import TypedFuture
from backend.common.profiler import Span
from backend.common.urlfetch import TypedURLFetchResult, URLFetchMethod, URLFetchResult
from backend.tasks_io.datafeeds.parsers.parser_base import (
    ParserBase,
    TParsedResponse,
    TParserInput,
)

TAPIResponse = TypeVar("TAPIResponse")
TReturn = TypeVar("TReturn")


class DatafeedBase(abc.ABC, Generic[TAPIResponse, TReturn]):

    ndb_context: Context

    def __init__(self) -> None:
        self.ndb_context = ndb.get_context()

    @abc.abstractmethod
    def url(self) -> str: ...

    def headers(self) -> Dict[str, str]:
        return {}

    @abc.abstractmethod
    def parser(self) -> ParserBase[TAPIResponse, TReturn]: ...

    @property
    def method(self) -> URLFetchMethod:
        return URLFetchMethod.GET

    def payload(self) -> Optional[Dict[str, str]]:
        return None

    def fetch_async(self) -> TypedFuture[Optional[TReturn]]:
        # Work around a pyre limitation where we can't combine
        # decorator type hints with generics
        return self._gen()

    @ndb.tasklet
    def _gen(self) -> Generator[Any, Any, Optional[TReturn]]:
        response = yield self._fetch()
        parser = self.parser()
        return self._parse(response, parser)

    def _fetch(self) -> TypedFuture[TypedURLFetchResult[TAPIResponse]]:
        url = self.url()
        headers = self.headers()
        return self._urlfetch(url, headers)

    @ndb.tasklet
    def _urlfetch(
        self, url: str, headers: Dict[str, str]
    ) -> Generator[Any, Any, TypedURLFetchResult[TAPIResponse]]:
        with Span(f"api_fetch:{type(self).__name__}"):
            if payload_data := self.payload():
                payload = urlencode(payload_data).encode()
            else:
                payload = None

            resp = yield self.ndb_context.urlfetch(
                url,
                headers=headers,
                deadline=30,
                method=self.method,
                payload=payload,
            )
            resp = URLFetchResult(url, resp)
            return cast(TypedURLFetchResult[TAPIResponse], resp)

    def _parse(
        self,
        response: TypedURLFetchResult[TParserInput],
        parser: ParserBase[TParserInput, TParsedResponse],
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            with Span(f"api_parser:{type(parser).__name__}"):
                resp_body = response.json()
                if resp_body is None:
                    return None
                return parser.parse(resp_body)
        elif response.status_code == 404:
            return None

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None
