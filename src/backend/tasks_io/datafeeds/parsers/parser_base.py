import abc
from typing import Any, Generic, TypeVar


TParsedResponse = TypeVar("TParsedResponse")


class ParserBase(abc.ABC, Generic[TParsedResponse]):
    @abc.abstractmethod
    def parse(self, response: Any) -> TParsedResponse: ...
