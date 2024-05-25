import logging
from unittest.mock import Mock, patch

import pytest

from backend.tasks_io.datafeeds.datafeed_html import DatafeedHTML
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


@pytest.fixture
def mock_parser() -> Mock:
    return Mock(spec=ParserBase)


def test_refer(mock_parser) -> None:
    df = DatafeedHTML()
    url = "my.usfirst.org/myarea"

    with patch("requests.get") as mock_get:
        df.parse(url=url, parser=mock_parser)

    mock_get.assert_called()
    args, kwargs = mock_get.call_args

    assert args[0] == url
    assert kwargs["timeout"] == 10

    expected_headers = {
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
        "Referer": "usfirst.org",
    }
    assert kwargs["headers"] == expected_headers


@pytest.mark.parametrize("session_key", [None, "test"])
def test_cookie(mock_parser, session_key: str) -> None:
    df = DatafeedHTML()
    url = "thebluealliance.com"

    with patch("requests.get") as mock_get:
        df.parse(url=url, parser=mock_parser, usfirst_session_key=session_key)

    mock_get.assert_called()
    args, kwargs = mock_get.call_args

    assert args[0] == url
    assert kwargs["timeout"] == 10

    expected_headers = {
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
    }

    if session_key:
        expected_headers["Cookie"] = session_key

    assert kwargs["headers"] == expected_headers


def test_raises(mock_parser, caplog) -> None:
    df = DatafeedHTML()

    with patch(
        "requests.get", side_effect=Exception("Mock error")
    ) as mock_get, caplog.at_level(logging.INFO):
        results = df.parse(url="thebluealliance.com", parser=mock_parser)

    assert len(caplog.records) == 2
    assert caplog.records[0].message == "URLFetch failed for: thebluealliance.com"
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[1].message == "Mock error"
    assert caplog.records[1].levelno == logging.INFO

    mock_get.assert_called()
    assert results == ([], False)


@pytest.mark.parametrize("status_code", [200, 500])
def test_parse(mock_parser, status_code: int, caplog) -> None:
    df = DatafeedHTML()
    content = "content"
    expected = ([], True)

    with patch(
        "requests.get", return_value=Mock(status_code=status_code, content=content)
    ), patch.object(
        mock_parser, "parse", return_value=expected
    ) as mock_parse, caplog.at_level(
        logging.WARNING
    ):
        results = df.parse(url="thebluealliance.com", parser=mock_parser)

    if status_code == 200:
        assert len(caplog.records) == 0

        mock_parse.assert_called_with(content)
        assert results == expected
    else:
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].message == "Unable to retreive url: thebluealliance.com"
        )
        assert caplog.records[0].levelno == logging.WARNING

        mock_parse.assert_not_called()
        assert results == ([], False)
