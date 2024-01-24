import logging
from typing import Callable

from flask import g


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
    if "after_response_callbacks" not in g:
        g.after_response_callbacks = []
    g.after_response_callbacks.append(callback)


def execute_callbacks() -> None:
    if not g or "after_response_callbacks" not in g:
        return

    for callback in g.after_response_callbacks:
        logging.info(
            f"Running callback after response: {callback.__name__ if hasattr(callback, '__name__') else None}"
        )
        try:
            callback()
        except Exception as e:
            logging.info(f"Callback failed: {e}")
