from google.auth.credentials import Credentials
from google.cloud.run_v2 import ExecutionsClient, JobsClient
from google.cloud.run_v2.types import EnvVar, RunJobRequest

from backend.common.cloudrun.clients.cloudrun_client import CloudRunClient


class GCloudRunClient(CloudRunClient):
    """Google Cloud Run client implementation."""

    def __init__(
        self,
        project: str,
        region: str,
        credentials: Credentials | None = None,
    ) -> None:
        """Initialize the Cloud Run client.

        Args:
            project: The Google Cloud project ID.
            region: The Cloud Run region (e.g., 'us-central1').
            credentials: Optional Google Cloud credentials.
        """
        self.project = project
        self.region = region
        self.jobs_client = JobsClient(credentials=credentials)
        self.executions_client = ExecutionsClient(credentials=credentials)

    def start_job(
        self,
        job_name: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        """Start a Cloud Run job.

        Args:
            job_name: The name of the job to start.
            args: Optional list of arguments to pass to the container.
            env: Optional dictionary of environment variables to set.

        Returns:
            The execution ID of the started job.
        """
        parent = f"projects/{self.project}/locations/{self.region}"
        full_job_name = f"{parent}/jobs/{job_name}"

        # Build RunJobRequest with overrides if args or env are provided
        request = RunJobRequest(name=full_job_name)

        if args is not None or env is not None:
            container_override = RunJobRequest.Overrides.ContainerOverride()

            if args is not None:
                container_override.args = args

            if env is not None:
                container_override.env = [
                    EnvVar(name=key, value=value) for key, value in env.items()
                ]

            request.overrides = RunJobRequest.Overrides(
                container_overrides=[container_override]
            )

        operation = self.jobs_client.run_job(request=request)

        # Extract execution ID from the operation or metadata
        execution_name = operation.metadata.name if operation.metadata else ""
        execution_id = execution_name.split("/")[-1] if execution_name else ""

        return execution_id

    def get_job_status(self, job_name: str, execution_id: str) -> str | None:
        """Get the status of a Cloud Run job execution.

        Args:
            job_name: The name of the job.
            execution_id: The ID of the execution.

        Returns:
            The execution State enum value or None if not found.
        """
        parent = f"projects/{self.project}/locations/{self.region}"
        full_execution_name = f"{parent}/jobs/{job_name}/executions/{execution_id}"

        try:
            execution = self.executions_client.get_execution(name=full_execution_name)
            # Get the state from the conditions if available
            if execution.conditions:
                # The first condition typically contains the overall status
                condition = execution.conditions[0]
                return condition.state if condition.state else None
            return None
        except Exception:
            return None
