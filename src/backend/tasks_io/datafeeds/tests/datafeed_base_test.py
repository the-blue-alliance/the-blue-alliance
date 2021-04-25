from unittest.mock import Mock, patch

import pytest

from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


@pytest.fixture
def mock_parser() -> Mock:
    return Mock(spec=ParserBase)


def test_refer(mock_parser) -> None:
    df = DatafeedBase()
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
    df = DatafeedBase()
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


def test_raises(mock_parser) -> None:
    df = DatafeedBase()

    with patch("requests.get", side_effect=Exception("Mock error")) as mock_get:
        results = df.parse(url="thebluealliance.com", parser=mock_parser)

    mock_get.assert_called()
    assert results == ([], False)


@pytest.mark.parametrize("status_code", [200, 500])
def test_parse(mock_parser, status_code: int) -> None:
    df = DatafeedBase()
    content = "content"
    expected = ([], True)

    with patch(
        "requests.get", return_value=Mock(status_code=status_code, content=content)
    ), patch.object(mock_parser, "parse", return_value=expected) as mock_parse:
        results = df.parse(url="thebluealliance.com", parser=mock_parser)

    if status_code == 200:
        mock_parse.assert_called_with(content)
        assert results == expected
    else:
        mock_parse.assert_not_called()
        assert results == ([], False)
