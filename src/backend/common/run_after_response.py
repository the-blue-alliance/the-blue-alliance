import logging
from typing import Callable

from werkzeug.local import Local

from backend.common.profiler import Span

# Request-local context that survives after Flask app context teardown
response_context = Local()


def run_after_response(callback: Callable[[], None]) -> None:
    """
    Enqueues a callback to be run after the request response.
    Usage examples:
    1) As a lambda (Note that this will not log the function name because it is a lambda)
    run_after_response(lambda: ...)

    2) As a named function
    run_after_response(function_to_run)

    3) As a decorator
    @run_after_response
    def function_to_run():
        ...
    """
    if not hasattr(response_context, "request"):
        return

    if not hasattr(response_context.request, "after_response_callbacks"):
        response_context.request.after_response_callbacks = []
    response_context.request.after_response_callbacks.append(callback)


def execute_callbacks() -> None:
    if not hasattr(response_context, "request"):
        return

    callbacks = getattr(response_context.request, "after_response_callbacks", [])

    for callback in callbacks:
        callback_name = callback.__name__ if hasattr(callback, "__name__") else None
        logging.info(f"Running callback after response: {callback_name}")
        with Span(f"execute_callback:{callback_name}"):
            try:
                callback()
            except Exception as e:
                logging.info(f"Callback failed: {e}")
