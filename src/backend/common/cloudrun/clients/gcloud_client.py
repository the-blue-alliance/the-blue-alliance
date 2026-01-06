from google.auth.credentials import Credentials
from google.cloud.run_v2 import ExecutionsClient, JobsClient
from google.cloud.run_v2.types import Condition, EnvVar, RunJobRequest

from backend.common.cloudrun.clients.cloudrun_client import CloudRunClient, JobStatus


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
        request = RunJobRequest()
        request.name = full_job_name

        if args is not None or env is not None:
            container_override = RunJobRequest.Overrides.ContainerOverride()

            if args is not None:
                container_override.args.extend(args)

            if env is not None:
                for key, value in env.items():
                    env_var = EnvVar()
                    env_var.name = key
                    env_var.value = value
                    container_override.env.append(env_var)

            request.overrides.container_overrides.append(container_override)

        operation = self.jobs_client.run_job(request=request)

        # Extract execution ID from the operation or metadata
        execution_name = operation.metadata.name if operation.metadata else ""
        execution_id = execution_name.split("/")[-1] if execution_name else ""

        return execution_id

    def get_job_status(self, job_name: str, execution_id: str) -> JobStatus | None:
        """Get the status of a Cloud Run job execution.

        Args:
            job_name: The name of the job.
            execution_id: The ID of the execution.

        Returns:
            JobStatus dict with state, message, and completion status, or None if not found.
        """
        parent = f"projects/{self.project}/locations/{self.region}"
        full_execution_name = f"{parent}/jobs/{job_name}/executions/{execution_id}"

        try:
            execution = self.executions_client.get_execution(name=full_execution_name)

            # Determine if job is complete by checking task counts
            is_complete = (
                execution.succeeded_count
                + execution.failed_count
                + execution.cancelled_count
                >= execution.task_count
            )

            # Determine overall state based on task counts
            if not is_complete:
                state = "RUNNING"
                message = "Job is running"
            elif execution.succeeded_count == execution.task_count:
                state = "SUCCEEDED"
                message = f"Job completed successfully ({execution.succeeded_count}/{execution.task_count} tasks succeeded)"
            elif execution.failed_count > 0:
                state = "FAILED"
                message = f"Job failed ({execution.failed_count}/{execution.task_count} tasks failed, {execution.succeeded_count} succeeded)"
            elif execution.cancelled_count > 0:
                state = "CANCELLED"
                message = f"Job was cancelled ({execution.cancelled_count}/{execution.task_count} tasks cancelled)"
            else:
                state = "UNKNOWN"
                message = "Job status unknown"

            # Get additional details from the newest condition if available
            if execution.conditions:
                newest_condition = execution.conditions[0]

                # Collect reason information from the condition
                reason_parts = []
                if newest_condition.message:
                    reason_parts.append(newest_condition.message)

                # Check for reason enums (only one will be set due to oneof)
                if newest_condition.reason and newest_condition.reason != 0:
                    # pyre-ignore[19,16]: Proto-plus enums have dynamic name attribute
                    reason_name = Condition.CommonReason(newest_condition.reason).name
                    reason_parts.append(f"Reason: {reason_name}")
                elif (
                    newest_condition.revision_reason
                    and newest_condition.revision_reason != 0
                ):
                    # pyre-ignore[19,16]: Proto-plus enums have dynamic name attribute
                    reason_name = Condition.RevisionReason(
                        newest_condition.revision_reason
                    ).name
                    reason_parts.append(f"Revision reason: {reason_name}")
                elif (
                    newest_condition.execution_reason
                    and newest_condition.execution_reason != 0
                ):
                    # pyre-ignore[19,16]: Proto-plus enums have dynamic name attribute
                    reason_name = Condition.ExecutionReason(
                        newest_condition.execution_reason
                    ).name
                    reason_parts.append(f"Execution reason: {reason_name}")

                if reason_parts:
                    message = f"{message}. {'. '.join(reason_parts)}"

            return JobStatus(state=state, message=message, is_complete=is_complete)
        except Exception:
            return None
