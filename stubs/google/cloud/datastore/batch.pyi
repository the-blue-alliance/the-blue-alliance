from google.cloud.datastore import helpers as helpers
from typing import Any, Optional

class Batch:
    def __init__(self, client: Any) -> None: ...
    def current(self): ...
    @property
    def project(self): ...
    @property
    def namespace(self): ...
    @property
    def mutations(self): ...
    def put(self, entity: Any) -> None: ...
    def delete(self, key: Any) -> None: ...
    def begin(self) -> None: ...
    def commit(self, retry: Optional[Any] = ..., timeout: Optional[Any] = ...) -> None: ...
    def rollback(self) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
