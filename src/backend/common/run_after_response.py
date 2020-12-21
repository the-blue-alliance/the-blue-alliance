import logging
from typing import Callable

from werkzeug.local import Local


local = Local()
local.callbacks = []


def run_after_response(callback: Callable[[], None]) -> None:
    local.callbacks.append(callback)


def execute_callbacks() -> None:
    for callback in local.callbacks:
        logging.info(f"Running callack after response: {callback.__name__}")
        callback()
