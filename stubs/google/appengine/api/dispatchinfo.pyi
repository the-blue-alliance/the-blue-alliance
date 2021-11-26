from google.appengine.api import appinfo as appinfo, validation as validation, yaml_builder as yaml_builder, yaml_listener as yaml_listener, yaml_object as yaml_object
from typing import Any

APPLICATION: str
DISPATCH: str
URL: str
MODULE: str
SERVICE: str

class Error(Exception): ...
class MalformedDispatchConfigurationError(Error): ...

class DispatchEntryURLValidator(validation.Validator):
    def Validate(self, value, unused_key: Any | None = ...): ...

class ParsedURL:
    host_exact: bool
    host: Any
    path_exact: bool
    path: Any
    def __init__(self, url_pattern) -> None: ...

class DispatchEntry(validation.Validated):
    ATTRIBUTES: Any

class DispatchInfoExternal(validation.Validated):
    ATTRIBUTES: Any

def LoadSingleDispatch(dispatch_info, open_fn: Any | None = ...): ...
