import abc

from google.cloud.tasks_v2.types import task as gct_task

from backend.common.deferred.requests.task_request import TaskRequest


class GCloudTaskRequest(TaskRequest):
    @property
    @abc.abstractmethod
    def proto_task(self) -> gct_task.Task:
        ...
