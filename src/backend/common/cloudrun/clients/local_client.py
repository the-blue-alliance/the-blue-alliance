from backend.common.cloudrun.clients.cloudrun_client import CloudRunClient


class LocalCloudRunClient(CloudRunClient):
    """Local stub implementation for Cloud Run client."""

    def start_job(
        self,
        job_name: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        """Start a Cloud Run job locally (stubbed).

        Args:
            job_name: The name of the job to start.

        Returns:
            A stub execution ID.
        """
        return "test-execution-id"

    def get_job_status(self, job_name: str, execution_id: str) -> str | None:
        """Get the status of a Cloud Run job execution locally (stubbed).

        Args:
            job_name: The name of the job.
            execution_id: The ID of the execution.

        Returns:
            The execution status or None if not found.
        """
        return "CONDITION_SUCCEEDED"
