import abc
from typing import Optional


class CloudRunClient(abc.ABC):
    @abc.abstractmethod
    def start_job(
        self,
        job_name: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> str: ...

    @abc.abstractmethod
    def get_job_status(self, job_name: str, execution_id: str) -> str | None: ...
