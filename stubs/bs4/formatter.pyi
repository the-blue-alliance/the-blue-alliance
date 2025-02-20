from bs4._typing import _AttributeValue
from bs4.dammit import EntitySubstitution as EntitySubstitution
from typing import Iterable

class Formatter(EntitySubstitution):
    HTML: str
    XML: str
    HTML_DEFAULTS: dict[str, set[str]]
    language: str | None
    entity_substitution: _EntitySubstitutionFunction | None
    void_element_close_prefix: str
    cdata_containing_tags: set[str]
    indent: str
    empty_attributes_are_booleans: bool
    def __init__(self, language: str | None = None, entity_substitution: _EntitySubstitutionFunction | None = None, void_element_close_prefix: str = '/', cdata_containing_tags: set[str] | None = None, empty_attributes_are_booleans: bool = False, indent: int | str = 1) -> None: ...
    def substitute(self, ns: str) -> str: ...
    def attribute_value(self, value: str) -> str: ...
    def attributes(self, tag: bs4.element.Tag) -> Iterable[tuple[str, _AttributeValue | None]]: ...

class HTMLFormatter(Formatter):
    REGISTRY: dict[str | None, HTMLFormatter]
    def __init__(self, entity_substitution: _EntitySubstitutionFunction | None = None, void_element_close_prefix: str = '/', cdata_containing_tags: set[str] | None = None, empty_attributes_are_booleans: bool = False, indent: int | str = 1) -> None: ...

class XMLFormatter(Formatter):
    REGISTRY: dict[str | None, XMLFormatter]
    def __init__(self, entity_substitution: _EntitySubstitutionFunction | None = None, void_element_close_prefix: str = '/', cdata_containing_tags: set[str] | None = None, empty_attributes_are_booleans: bool = False, indent: int | str = 1) -> None: ...
