import logging
from typing import Callable, Iterable, Optional

from werkzeug.local import Local


# Request-local context that survives after Flask app context teardown
response_context = Local()

from backend.common.profiler import Span


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
    if not hasattr(response_context, "after_response_callbacks"):
        response_context.after_response_callbacks = []
    response_context.after_response_callbacks.append(callback)


def execute_callbacks() -> None:
    callbacks = getattr(response_context, "after_response_callbacks", None)
    if not callbacks:
        return

    for callback in callbacks:
        callback_name = callback.__name__ if hasattr(callback, '__name__') else None
        logging.info(
            f"Running callback after response: {callback_name}"
        )
        with Span(f"execute_callback:{callback_name}"):
            try:
                callback()
            except Exception as e:
                logging.info(f"Callback failed: {e}")

    if hasattr(response_context, "after_response_callbacks"):
        delattr(response_context, "after_response_callbacks")
