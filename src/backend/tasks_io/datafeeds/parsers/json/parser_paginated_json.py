import abc
from typing import Any, TypeVar

from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


TParsedResponse = TypeVar("TParsedResponse")


class ParserPaginatedJSON(ParserJSON[tuple[TParsedResponse, bool]]):
    """
    Parser that parses a JSON dict and returns an optional model + a boolean if there is more data to be fetched
    """

    @abc.abstractmethod
    def parse(
        self, response: dict[str, Any]
    ) -> tuple[TParsedResponse | None, bool]: ...
