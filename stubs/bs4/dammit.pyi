import cchardet
import chardet
import charset_normalizer
from _typeshed import Incomplete
from bs4._typing import _Encoding, _Encodings
from types import ModuleType
from typing import Iterator, Pattern
from typing_extensions import Literal

chardet_module: ModuleType | None
chardet_module = cchardet
chardet_module = chardet
chardet_module = charset_normalizer
xml_encoding: str
html_meta: str
encoding_res: dict[type, dict[str, Pattern]]

class EntitySubstitution:
    HTML_ENTITY_TO_CHARACTER: dict[str, str]
    CHARACTER_TO_HTML_ENTITY: dict[str, str]
    CHARACTER_TO_HTML_ENTITY_RE: Pattern[str]
    CHARACTER_TO_HTML_ENTITY_WITH_AMPERSAND_RE: Pattern[str]
    CHARACTER_TO_XML_ENTITY: dict[str, str]
    ANY_ENTITY_RE: Incomplete
    BARE_AMPERSAND_OR_BRACKET: Pattern[str]
    AMPERSAND_OR_BRACKET: Pattern[str]
    @classmethod
    def quoted_attribute_value(cls, value: str) -> str: ...
    @classmethod
    def substitute_xml(cls, value: str, make_quoted_attribute: bool = False) -> str: ...
    @classmethod
    def substitute_xml_containing_entities(cls, value: str, make_quoted_attribute: bool = False) -> str: ...
    @classmethod
    def substitute_html(cls, s: str) -> str: ...
    @classmethod
    def substitute_html5(cls, s: str) -> str: ...
    @classmethod
    def substitute_html5_raw(cls, s: str) -> str: ...

class EncodingDetector:
    known_definite_encodings: Incomplete
    user_encodings: Incomplete
    exclude_encodings: Incomplete
    chardet_encoding: Incomplete
    is_html: Incomplete
    declared_encoding: str | None
    def __init__(self, markup: bytes, known_definite_encodings: _Encodings | None = None, is_html: bool | None = False, exclude_encodings: _Encodings | None = None, user_encodings: _Encodings | None = None, override_encodings: _Encodings | None = None) -> None: ...
    markup: bytes
    sniffed_encoding: _Encoding | None
    @property
    def encodings(self) -> Iterator[_Encoding]: ...
    @classmethod
    def strip_byte_order_mark(cls, data: bytes) -> tuple[bytes, _Encoding | None]: ...
    @classmethod
    def find_declared_encoding(cls, markup: bytes | str, is_html: bool = False, search_entire_document: bool = False) -> _Encoding | None: ...

class UnicodeDammit:
    smart_quotes_to: Incomplete
    tried_encodings: Incomplete
    contains_replacement_characters: bool
    is_html: Incomplete
    log: Incomplete
    detector: Incomplete
    markup: Incomplete
    unicode_markup: Incomplete
    original_encoding: Incomplete
    def __init__(self, markup: bytes, known_definite_encodings: _Encodings | None = [], smart_quotes_to: Literal['ascii', 'xml', 'html'] | None = None, is_html: bool = False, exclude_encodings: _Encodings | None = [], user_encodings: _Encodings | None = None, override_encodings: _Encodings | None = None) -> None: ...
    CHARSET_ALIASES: dict[str, _Encoding]
    ENCODINGS_WITH_SMART_QUOTES: _Encodings
    @property
    def declared_html_encoding(self) -> _Encoding | None: ...
    def find_codec(self, charset: _Encoding) -> str | None: ...
    MS_CHARS: dict[bytes, str | tuple[str, str]]
    MS_CHARS_TO_ASCII: dict[bytes, str]
    WINDOWS_1252_TO_UTF8: dict[int, bytes]
    MULTIBYTE_MARKERS_AND_SIZES: list[tuple[int, int, int]]
    FIRST_MULTIBYTE_MARKER: int
    LAST_MULTIBYTE_MARKER: int
    @classmethod
    def detwingle(cls, in_bytes: bytes, main_encoding: _Encoding = 'utf8', embedded_encoding: _Encoding = 'windows-1252') -> bytes: ...
