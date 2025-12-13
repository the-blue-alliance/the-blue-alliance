from bs4.element import AttributeValueList as AttributeValueList, NamespacedAttribute as NamespacedAttribute, NavigableString as NavigableString, PageElement as PageElement, ResultSet as ResultSet, Tag as Tag
from typing import Any
from typing_extensions import Protocol

class _RegularExpressionProtocol(Protocol):
    def search(self, string: str, pos: int = ..., endpos: int = ...) -> Any | None: ...
    @property
    def pattern(self) -> str: ...
