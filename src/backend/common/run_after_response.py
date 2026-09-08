import logging
from typing import Any, Callable, TypeVar

from werkzeug.local import Local

from backend.common.profiler import Span

# Request-local context that survives after Flask app context teardown
response_context = Local()


TCallback = TypeVar("TCallback", bound=Callable[..., Any])


def run_after_response(callback: TCallback) -> TCallback:
    """
    Enqueues a callback to be run after the request response.
    Usage examples:
    1) As a lambda
    run_after_response(lambda: ...)

    2) As a named function
    run_after_response(function_to_run)

    3) As a decorator
    @run_after_response
    def function_to_run():
        ...
    """
    if not hasattr(response_context, "request"):
        logging.debug(
            "run_after_response called outside active request context; dropping callback."
        )
        return callback

    if not hasattr(response_context.request, "after_response_callbacks"):
        response_context.request.after_response_callbacks = []
    response_context.request.after_response_callbacks.append(callback)
    return callback


def execute_callbacks() -> None:
    if not hasattr(response_context, "request"):
        return

    callbacks = getattr(response_context.request, "after_response_callbacks", [])
    response_context.request.after_response_callbacks = []

    for callback in callbacks:
        name = getattr(callback, "__name__", None) or getattr(
            getattr(callback, "func", None), "__name__", None
        )
        try:
            with Span(f"execute_callback:{name}"):
                callback()
        except Exception:
            logging.warning(f"Callback {name} failed after response", exc_info=True)
