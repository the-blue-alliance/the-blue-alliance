import abc
from typing import Optional, Tuple

from backend.tasks_io.datafeeds.parsers.parser_base import (
    ParserBase,
    TParsedResponse,
    TParserInput,
)


class ParserPaginated(ParserBase[TParserInput, Tuple[TParsedResponse, bool]]):
    """
    Parser that parses a JSON dict and returns an optional model + a boolean if there is more data to be fetched
    """

    @abc.abstractmethod
    def parse(
        self,
        response: TParserInput,
    ) -> Tuple[Optional[TParsedResponse], bool]: ...
