import abc
from typing import Any, Dict, Optional, TypeVar

from backend.common.datafeeds.parsers.parser_base import ParserBase


TParsedResponse = TypeVar("TParsedResponse")


class ParserJSON(ParserBase[TParsedResponse]):
    """
    Provides a basic structure for parsing pages.
    Parsers are not allowed to return Model objects, only dictionaries.
    """

    @abc.abstractmethod
    def parse(self, response: Dict[str, Any]) -> Optional[TParsedResponse]:
        ...
