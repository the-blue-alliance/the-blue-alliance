import abc
from typing import Any, Dict, Optional, Tuple, TypeVar

from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


TParsedResponse = TypeVar("TParsedResponse")


class ParserPaginatedJSON(ParserJSON[Tuple[TParsedResponse, bool]]):
    """
    Parser that parses a JSON dict and returns an optional model + a boolean if there is more data to be fetched
    """

    @abc.abstractmethod
    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[Optional[TParsedResponse], bool]: ...
