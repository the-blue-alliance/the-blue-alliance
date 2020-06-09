import logging
from typing import Any

class NullHandler(logging.Handler):
    def emit(self, record: Any) -> None: ...
