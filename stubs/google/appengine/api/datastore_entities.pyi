from google.appengine.api import datastore as datastore, datastore_errors as datastore_errors, datastore_types as datastore_types
from typing import Any

class GdKind(datastore.Entity):
    HEADER: str
    FOOTER: str
    def __init__(self, kind, title, kind_properties, contact_properties=...) -> None: ...
    def ToXml(self): ...

class Message(GdKind):
    KIND_PROPERTIES: Any
    CONTACT_PROPERTIES: Any
    def __init__(self, title, kind: str = ...) -> None: ...

class Event(GdKind):
    KIND_PROPERTIES: Any
    CONTACT_PROPERTIES: Any
    class Status:
        CONFIRMED: str
        TENTATIVE: str
        CANCELED: str
    def __init__(self, title, kind: str = ...) -> None: ...
    def ToXml(self): ...

class Contact(GdKind):
    CONTACT_SECTION_HEADER: str
    CONTACT_SECTION_FOOTER: str
    KIND_PROPERTIES: Any
    CONTACT_SECTION_PROPERTIES: Any
    def __init__(self, title, kind: str = ...) -> None: ...
    def ToXml(self): ...
