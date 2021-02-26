import abc
from typing import Dict, Generic, Optional, TypeVar

from backend.common.deferred.requests.task_request import TaskRequest
from backend.common.deferred.tasks.task import Task


TTaskRequest = TypeVar("TTaskRequest", bound=TaskRequest)


class TaskQueue(abc.ABC, Generic[TTaskRequest]):

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"TaskQueue(name={self.name})"

    # TODO: Add support for `countdown`, `eta`, `name`, `retry_options` | Also support Task.schedule_time
    def enqueue(
        self,
        task: Task,
        url: str,
        headers: Dict[str, str],
        service: Optional[str] = None,
    ) -> None:
        self._enqueue(self._task_request(url, headers, task.serialize(), service))

    @abc.abstractmethod
    def _task_request(
        self,
        url: str,
        headers: Dict[str, str],
        body: bytes,
        service: Optional[str] = None,
    ) -> TTaskRequest:
        ...

    @abc.abstractmethod
    def _enqueue(self, request: TTaskRequest) -> None:
        ...
