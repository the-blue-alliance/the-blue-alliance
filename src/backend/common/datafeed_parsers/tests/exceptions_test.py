import pytest

from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parser_input_exception() -> None:
    with pytest.raises(ParserInputException, match="bad input"):
        raise ParserInputException("bad input")
