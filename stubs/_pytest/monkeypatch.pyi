from _pytest.fixtures import fixture as fixture
from _pytest.pathlib import Path as Path
from typing import Any, Generator, Optional

RE_IMPORT_ERROR_NAME: Any

def monkeypatch() -> None: ...
def resolve(name: Any): ...
def annotated_getattr(obj: Any, name: Any, ann: Any): ...
def derive_importpath(import_path: Any, raising: Any): ...

class Notset: ...

notset: Any

class MonkeyPatch:
    def __init__(self) -> None: ...
    def context(self) -> Generator[MonkeyPatch, None, None]: ...
    def setattr(self, target: Any, name: Any, value: Any = ..., raising: bool = ...) -> None: ...
    def delattr(self, target: Any, name: Any = ..., raising: bool = ...) -> None: ...
    def setitem(self, dic: Any, name: Any, value: Any) -> None: ...
    def delitem(self, dic: Any, name: Any, raising: bool = ...) -> None: ...
    def setenv(self, name: Any, value: Any, prepend: Optional[Any] = ...) -> None: ...
    def delenv(self, name: Any, raising: bool = ...) -> None: ...
    def syspath_prepend(self, path: Any) -> None: ...
    def chdir(self, path: Any) -> None: ...
    def undo(self) -> None: ...
