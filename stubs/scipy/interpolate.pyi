from typing import Any

from numpy import ndarray

class CubicSpline:
    def __init__(self, x: Any, y: Any) -> None: ...
    def __call__(self, x: Any) -> ndarray: ...
