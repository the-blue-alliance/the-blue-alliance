import logging
from typing import Callable

from werkzeug.local import Local


local = Local()
local.callbacks = []


def run_after_response(callback: Callable[[], None]) -> None:
    """
    Enques a allback to be run a callback after the request repsonse.
    Usage examples:
    1) As a lambda (Note that this will not log the function name because it is a lambda)
    run_after_response(lambda: ...)

    2) As a named function
    run_after_response(function_to_run)

    3) As a decorator
    @run_after_response
    function_to_run():
        ...
    """
    local.callbacks.append(callback)


def execute_callbacks() -> None:
    for callback in local.callbacks:
        logging.info(f"Running callack after response: {callback.__name__}")
        callback()
