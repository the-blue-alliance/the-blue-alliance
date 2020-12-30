import pickle
from typing import Any, Callable


class Task:
    def __init__(self, obj: Callable, *args: Any, **kwargs: Any) -> None:
        self.obj = obj
        self.args = args
        self.kwargs = kwargs

    def serialize(self) -> bytes:
        return pickle.dumps(
            (self.obj, self.args, self.kwargs), protocol=pickle.HIGHEST_PROTOCOL
        )
