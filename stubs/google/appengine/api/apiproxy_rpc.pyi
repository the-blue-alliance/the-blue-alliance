from concurrent import futures
from typing import Any

_THREAD_POOL: futures.ThreadPoolExecutor

class RPC:
    IDLE: int
    RUNNING: int
    FINISHING: int
    package: Any
    call: Any
    request: Any
    future: Any
    response: Any
    callback: Any
    deadline: Any
    stub: Any
    cpu_usage_mcycles: int
    def __init__(self, package: Any | None = ..., call: Any | None = ..., request: Any | None = ..., response: Any | None = ..., callback: Any | None = ..., deadline: Any | None = ..., stub: Any | None = ...) -> None: ...
    def Clone(self): ...
    def MakeCall(self, package: Any | None = ..., call: Any | None = ..., request: Any | None = ..., response: Any | None = ..., callback: Any | None = ..., deadline: Any | None = ...) -> None: ...
    def Wait(self) -> None: ...
    def CheckSuccess(self) -> None: ...
    @property
    def exception(self): ...
    @property
    def state(self): ...
