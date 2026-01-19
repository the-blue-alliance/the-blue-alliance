from typing import Optional

from backend.common.cloudrun.clients.cloudrun_client import (
    CloudRunClient,
    JobStatus,
)
from backend.common.cloudrun.clients.gcloud_client import GCloudRunClient
from backend.common.cloudrun.clients.local_client import LocalCloudRunClient
from backend.common.environment import Environment
from backend.common.sitevars.google_cloudrun_config import GoogleCloudRunConfig


def _client_for_env() -> CloudRunClient:
    """Get the appropriate CloudRun client based on the environment.

    Returns:
        A CloudRunClient instance suitable for the current environment.

    Raises:
        ValueError: If required environment variables are not set.
    """
    if Environment.is_unit_test():
        return LocalCloudRunClient()

    if Environment.is_dev():
        return LocalCloudRunClient()

    project = Environment.project()
    if not project:
        raise ValueError(
            "Environment.project (GOOGLE_CLOUD_PROJECT) must be set to use Cloud Run client."
        )

    region = GoogleCloudRunConfig.region()
    if not region:
        raise ValueError(
            "GoogleCloudRunConfig.region must be set to use Cloud Run client."
        )

    return GCloudRunClient(project, region)


def start_job(
    job_name: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str:
    """Start a Cloud Run job.

    Args:
        job_name: The name of the job to start.

    Returns:
        The execution ID of the started job.
    """
    client = _client_for_env()
    return client.start_job(job_name, args, env)


def get_job_status(job_name: str, execution_id: str) -> Optional[JobStatus]:
    """Get the status of a Cloud Run job execution.

    Args:
        job_name: The name of the job.
        execution_id: The ID of the execution.

    Returns:
        A JobStatus dict with 'state', 'message', and 'is_complete' fields, or None if not found.
    """
    client = _client_for_env()
    return client.get_job_status(job_name, execution_id)
