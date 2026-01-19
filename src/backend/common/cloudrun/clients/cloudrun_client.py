import abc
from typing import Optional, TypedDict


class JobStatus(TypedDict):
    """Status information for a Cloud Run job execution."""

    state: str  # e.g., "RUNNING", "SUCCEEDED", "FAILED"
    message: str  # Human-readable status message
    is_complete: bool  # Whether the job has finished (success or failure)


class CloudRunClient(abc.ABC):
    @abc.abstractmethod
    def start_job(
        self,
        job_name: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> str: ...

    @abc.abstractmethod
    def get_job_status(self, job_name: str, execution_id: str) -> JobStatus | None: ...
