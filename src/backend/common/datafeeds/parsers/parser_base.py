import abc
from typing import Generic, TypeVar

TParserInput = TypeVar("TParserInput")
TParsedResponse = TypeVar("TParsedResponse")


class ParserBase(abc.ABC, Generic[TParserInput, TParsedResponse]):
    @abc.abstractmethod
    def parse(self, response: TParserInput) -> TParsedResponse: ...
