import contextvars
from typing import Any, Callable, cast, Generator, Iterable, ParamSpec, TypeVar, Union

from google.appengine.ext import ndb
from google.appengine.ext.ndb import tasklets as ndb_tasklets

from backend.common.futures import TypedFuture

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")

_tasklet_context_propagation_enabled: bool = False


def enable_tasklet_context_propagation() -> None:
    """
    Patches NDB Future to propagate Python 3 contextvars across tasklet yields.

    By default, NDB saves and restores Datastore contexts (ndb.Context), namespaces,
    and connections across tasklet yields, but does not propagate Python 3 contextvars.
    This hook captures the caller's context when a Future is created and runs tasklet
    execution steps inside that context, mirroring modern asyncio.Task behavior.
    """
    global _tasklet_context_propagation_enabled
    if _tasklet_context_propagation_enabled:
        return
    _tasklet_context_propagation_enabled = True

    future_cls: Any = ndb_tasklets.Future
    orig_init = future_cls.__init__
    orig_help = getattr(future_cls, "_help_tasklet_along", None)
    if orig_help is None:
        return

    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        orig_init(self, *args, **kwargs)
        self._py_context = contextvars.copy_context()

    def new_help(self: Any, *args: Any, **kwargs: Any) -> Any:
        ctx = getattr(self, "_py_context", None)
        if ctx is not None:
            return ctx.run(orig_help, self, *args, **kwargs)
        return orig_help(self, *args, **kwargs)

    future_cls.__init__ = new_init
    future_cls._help_tasklet_along = new_help


# Automatically enable tasklet context propagation on module import
enable_tasklet_context_propagation()


def typed_tasklet(
    f: Callable[
        TParams, Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]
    ],
) -> Callable[TParams, TypedFuture[TReturn]]:
    @ndb.tasklet
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TypedFuture[TReturn]], inner)


def typed_toplevel(
    f: Callable[
        TParams, Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]
    ],
) -> Callable[TParams, TReturn]:
    @ndb.toplevel
    def inner(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Union[TReturn, Iterable[TReturn], Generator[Any, Any, TReturn]]:
        return f(*args, **kwargs)

    return cast(Callable[TParams, TReturn], inner)
