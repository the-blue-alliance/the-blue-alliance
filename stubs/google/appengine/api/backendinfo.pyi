from google.appengine.api import validation as validation, yaml_builder as yaml_builder, yaml_listener as yaml_listener, yaml_object as yaml_object
from typing import Any

NAME_REGEX: str
FILE_REGEX: str
CLASS_REGEX: str
OPTIONS_REGEX: str
STATE_REGEX: str
BACKENDS: str
NAME: str
CLASS: str
INSTANCES: str
OPTIONS: str
PUBLIC: str
DYNAMIC: str
FAILFAST: str
MAX_CONCURRENT_REQUESTS: str
START: str
VALID_OPTIONS: Any
STATE: str

class BadConfig(Exception): ...

class BackendEntry(validation.Validated):
    ATTRIBUTES: Any
    def __init__(self, *args, **kwargs) -> None: ...
    def Init(self): ...
    def set_class(self, Class) -> None: ...
    def get_class(self): ...
    def ToDict(self): ...
    public: Any
    dynamic: Any
    failfast: Any
    def ParseOptions(self): ...
    options: Any
    def WriteOptions(self): ...

def LoadBackendEntry(backend_entry): ...

class BackendInfoExternal(validation.Validated):
    ATTRIBUTES: Any

def LoadBackendInfo(backend_info, open_fn: Any | None = ...): ...
