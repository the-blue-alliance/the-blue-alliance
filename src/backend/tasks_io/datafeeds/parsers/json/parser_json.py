import abc
from typing import Any, TypeVar

from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


TParsedResponse = TypeVar("TParsedResponse")


class ParserJSON(ParserBase[TParsedResponse]):
    """
    Provides a basic structure for parsing pages.
    Parsers are not allowed to return Model objects, only dictionaries.
    """

    @abc.abstractmethod
    def parse(self, response: dict[str, Any]) -> TParsedResponse | None: ...
