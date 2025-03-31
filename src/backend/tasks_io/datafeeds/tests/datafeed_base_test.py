from typing import Any
from unittest.mock import patch

import pytest
from google.appengine.ext import testbed

from backend.common.futures import InstantFuture
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class DummyParser(ParserBase[Any]):

    def parse(self, response: Any) -> Any:
        return response


class DummyDatafeed(DatafeedBase[Any]):

    def url(self):
        return "https://example.com/test"

    def headers(self):
        return {"foo": "bar"}

    def parser(self) -> DummyParser:
        return DummyParser()


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


def test_get(urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub) -> None:
    df = DummyDatafeed()

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:

        def fetch_fn(request, response):
            response.StatusCode = 200
            response.Content = b"{}"

        mock_fetch.side_effect = fetch_fn
        result = df.fetch_async().get_result()

    assert result == {}

    assert mock_fetch.call_count == 1
    called_request = mock_fetch.call_args[0][0]
    assert called_request.Url == "https://example.com/test"

    called_headers = {h.Key: h.Value for h in called_request.header}
    assert called_headers == {"foo": "bar"}


def test_parse_404(urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub) -> None:
    df = DummyDatafeed()

    with patch.object(df, "_fetch") as mock_fetch:
        mock_fetch.return_value = InstantFuture(
            URLFetchResult.mock_for_content("https://example.com/test", 404, "")
        )
        result = df.fetch_async().get_result()

    assert result is None
