import logging
from typing import Callable

from werkzeug.local import Local


local_context = Local()


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
    if not hasattr(local_context.request, "callbacks"):
        local_context.request.callbacks = []
    local_context.request.callbacks.append(callback)


def execute_callbacks() -> None:
    if not hasattr(local_context.request, "callbacks"):
        return

    for callback in local_context.request.callbacks:
        logging.info(
            f"Running callback after response: {callback.__name__ if hasattr(callback, '__name__') else None}"
        )
        try:
            callback()
        except Exception as e:
            logging.info(f"Callback failed: {e}")
