import abc
from typing import Any, Generic, TypeVar

from backend.common.deferred.queues.task_queue import TaskQueue


TTaskQueue = TypeVar("TTaskQueue", bound=TaskQueue)


class TaskClient(abc.ABC, Generic[TTaskQueue]):
    def __init__(self, client: Any) -> None:
        self._client = client

    @abc.abstractmethod
    def queue(self, name: str) -> TTaskQueue:
        ...
